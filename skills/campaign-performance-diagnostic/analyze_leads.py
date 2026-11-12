"""
Generic Instantly lead export analyser.

Stream an Instantly lead export CSV and emit a structured JSON of
reply rates, positive-reply rates, and bounce rates cut by time, persona,
industry, persona x industry, company size, case study, email provider, email
security gateway, and copy-theme fingerprints. Every cut is split into
Retargeting vs New Outbound.

This is a generic analyser. It
contains no company-specific defaults. Usage:

    python3 analyze_leads.py <path-to-export.csv>
        [--retargeting-keyword retarget]
        [--min-sample 200]
        [--output _lead_analysis.json]

Outputs a sibling `_lead_analysis.json` next to the input by default.
"""

from __future__ import annotations

import argparse
import collections
import csv
import json
import re
import sys
from pathlib import Path

csv.field_size_limit(sys.maxsize)

FINGERPRINT_LEN = 80
CONTACTED_STATUSES = {
    "Active | Contacted",
    "Completed | Contacted",
    "Completed | Reply received",
    "Active | Reply received",
    "Bounced",
}
POSITIVE_INTEREST = {"Interested"}
NEGATIVE_INTEREST = {
    "Not interested",
    "Wrong person",
    "Do not contact",
    "Do not cotact",  # observed misspelling in Instantly UI
}


def parse_args(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    p.add_argument("csv_path", help="Path to the Instantly lead export CSV.")
    p.add_argument(
        "--retargeting-keyword",
        default="retarget",
        help="Substring (case-insensitive) used to classify a campaign as retargeting. Default: %(default)s",
    )
    p.add_argument(
        "--min-sample",
        type=int,
        default=200,
        help="Minimum contacted count before a cell is marked confident. Default: %(default)s",
    )
    p.add_argument("--output", help="Override output path (default: _lead_analysis.json next to the input).")
    return p.parse_args(argv)


def is_retargeting(campaign_name: str, keyword: str) -> bool:
    return keyword.lower() in (campaign_name or "").lower()


def parse_headcount(text: str) -> str:
    """Map text like '25 - 100' / '1K - 10K' / '50K - 100K' / '201 to 500' to a size bucket."""
    if not text:
        return ""
    t = text.strip().replace(",", "")

    def to_num(piece: str):
        piece = piece.strip().upper()
        if not piece:
            return None
        m = re.match(r"^(\d+(?:\.\d+)?)\s*([KM])?$", piece)
        if not m:
            return None
        val = float(m.group(1))
        suf = m.group(2) or ""
        if suf == "K":
            val *= 1_000
        elif suf == "M":
            val *= 1_000_000
        return val

    parts = re.split(r"\s*(?:-|–|to|To|TO)\s*", t, maxsplit=1)
    if len(parts) == 2:
        lo = to_num(parts[0])
        hi = to_num(parts[1])
    else:
        lo = to_num(parts[0])
        hi = lo
    if lo is None and hi is None:
        return ""
    mid = (lo if lo is not None else 0) + ((hi or lo or 0) - (lo or 0)) / 2
    if mid < 50:
        return "<50"
    if mid < 250:
        return "50 to 250"
    if mid < 1_000:
        return "250 to 1K"
    if mid < 10_000:
        return "1K to 10K"
    return "10K+"


def get_first_present(row: dict, candidate_columns: list[str]) -> str:
    for col in candidate_columns:
        v = (row.get(col) or "").strip()
        if v:
            return v
    return ""


def get_persona(row: dict) -> str:
    v = get_first_present(row, ["Persona", "persona", "persona "])
    if not v or v.lower() == "other":
        return ""
    return v.lower()


def get_industry(row: dict) -> str:
    return get_first_present(
        row, ["industry", "company_industry", "Person - Industry", "Industry", "Sector"]
    ).lower()


def get_case_study(row: dict) -> str:
    """Return VO case-study company; fall back to Solar case-study company."""
    v = (row.get("VO Case Study Company") or "").strip()
    if v and not v.lower().startswith(("none", "no exact", "no direct")):
        return v
    v = (row.get("Solar Case Study Company") or "").strip()
    if v and not v.lower().startswith(("none", "no exact", "no direct")):
        return f"{v} (solar)"
    return ""


def fingerprint(text: str) -> str:
    if not text:
        return ""
    return re.sub(r"\s+", " ", text.strip())[:FINGERPRINT_LEN]


class Tally:
    __slots__ = ("uploaded", "contacted", "replied", "positive", "negative", "bounced")

    def __init__(self):
        self.uploaded = 0
        self.contacted = 0
        self.replied = 0
        self.positive = 0
        self.negative = 0
        self.bounced = 0

    def add(self, contacted, replied, positive, negative, bounced):
        self.uploaded += 1
        if contacted:
            self.contacted += 1
        if replied:
            self.replied += 1
        if positive:
            self.positive += 1
        if negative:
            self.negative += 1
        if bounced:
            self.bounced += 1

    def as_dict(self, min_sample: int):
        contacted = self.contacted or 0
        reply_rate = (self.replied / contacted * 100) if contacted else 0.0
        pos_rate = (self.positive / contacted * 100) if contacted else 0.0
        bounce_rate = (self.bounced / self.uploaded * 100) if self.uploaded else 0.0
        return {
            "uploaded": self.uploaded,
            "contacted": self.contacted,
            "replied": self.replied,
            "positive": self.positive,
            "negative": self.negative,
            "bounced": self.bounced,
            "reply_rate": round(reply_rate, 3),
            "positive_rate": round(pos_rate, 3),
            "bounce_rate": round(bounce_rate, 3),
            "low_sample": self.contacted < min_sample,
        }


def make_grouped() -> dict:
    return {"retargeting": Tally(), "new_outbound": Tally(), "overall": Tally()}


def add_to_grouped(d, key, is_rt, contacted, replied, positive, negative, bounced):
    if key not in d:
        d[key] = make_grouped()
    bucket = d[key]
    bucket["overall"].add(contacted, replied, positive, negative, bounced)
    target = bucket["retargeting"] if is_rt else bucket["new_outbound"]
    target.add(contacted, replied, positive, negative, bounced)


def serialize(d, min_sample):
    return {
        k: {seg: v[seg].as_dict(min_sample) for seg in ("retargeting", "new_outbound", "overall")}
        for k, v in d.items()
    }


def run(args):
    input_path = Path(args.csv_path).expanduser().resolve()
    if not input_path.exists():
        sys.exit(f"Input CSV not found: {input_path}")
    output_path = Path(args.output).expanduser().resolve() if args.output else input_path.with_name("_lead_analysis.json")

    overall = make_grouped()
    cuts = {
        "by_month": {},
        "by_campaign": {},
        "by_persona": {},
        "by_industry": {},
        "by_persona_industry": {},
        "by_size": {},
        "by_case_study": {},
        "by_email_provider": {},
        "by_esg": {},
        "by_trigger_fp": {},
        "by_vp_fp": {},
        "by_pp_fp": {},
    }
    text_examples = {"trigger": {}, "vp": {}, "pp": {}}

    interest_counts = collections.Counter()
    rows_seen = 0

    with input_path.open(newline="", encoding="utf-8", errors="replace") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows_seen += 1
            status = (row.get("Lead Status") or "").strip()
            interest = (row.get("Interest Status") or "").strip()
            interest_counts[interest] += 1
            try:
                reply_count = int(row.get("email_reply_count") or 0)
            except ValueError:
                reply_count = 0
            contacted = status in CONTACTED_STATUSES
            replied = reply_count > 0
            positive = interest in POSITIVE_INTEREST
            negative = interest in NEGATIVE_INTEREST
            bounced = status == "Bounced"

            campaign = (row.get("Campaign Name") or "").strip()
            if not campaign:
                continue  # unassigned leads cannot be attributed
            is_rt = is_retargeting(campaign, args.retargeting_keyword)

            month = (row.get("timestamp_last_contact") or "")[:7] or (row.get("timestamp_created") or "")[:7]

            persona = get_persona(row) or "unknown"
            industry = get_industry(row) or "unknown"
            size_bucket = parse_headcount(row.get("companyHeadCount") or row.get("company_size_range") or "") or "unknown"
            case_study = get_case_study(row) or "(no case study)"
            esp = (row.get("Email Provider") or "Unknown").strip() or "Unknown"
            esg = (row.get("Email Security Gateway Provider") or "Not Found").strip() or "Not Found"

            trigger_text = (row.get("Trigger") or "").strip()
            vp_text = (row.get("Value Prop Paragraph VO") or row.get("value prop paragraph vo") or "").strip()
            pp_text = (row.get("Pain Point Paragraph VO") or row.get("pain point paragraph vo") or "").strip()
            t_fp = fingerprint(trigger_text)
            v_fp = fingerprint(vp_text)
            p_fp = fingerprint(pp_text)

            if t_fp and t_fp not in text_examples["trigger"]:
                text_examples["trigger"][t_fp] = trigger_text
            if v_fp and v_fp not in text_examples["vp"]:
                text_examples["vp"][v_fp] = vp_text
            if p_fp and p_fp not in text_examples["pp"]:
                text_examples["pp"][p_fp] = pp_text

            overall["overall"].add(contacted, replied, positive, negative, bounced)
            (overall["retargeting"] if is_rt else overall["new_outbound"]).add(
                contacted, replied, positive, negative, bounced
            )

            add_to_grouped(cuts["by_month"], month or "unknown", is_rt, contacted, replied, positive, negative, bounced)
            add_to_grouped(cuts["by_campaign"], campaign, is_rt, contacted, replied, positive, negative, bounced)
            add_to_grouped(cuts["by_persona"], persona, is_rt, contacted, replied, positive, negative, bounced)
            add_to_grouped(cuts["by_industry"], industry, is_rt, contacted, replied, positive, negative, bounced)
            add_to_grouped(
                cuts["by_persona_industry"],
                f"{persona} | {industry}",
                is_rt,
                contacted,
                replied,
                positive,
                negative,
                bounced,
            )
            add_to_grouped(cuts["by_size"], size_bucket, is_rt, contacted, replied, positive, negative, bounced)
            add_to_grouped(cuts["by_case_study"], case_study, is_rt, contacted, replied, positive, negative, bounced)
            add_to_grouped(cuts["by_email_provider"], esp, is_rt, contacted, replied, positive, negative, bounced)
            add_to_grouped(cuts["by_esg"], esg, is_rt, contacted, replied, positive, negative, bounced)
            if t_fp:
                add_to_grouped(cuts["by_trigger_fp"], t_fp, is_rt, contacted, replied, positive, negative, bounced)
            if v_fp:
                add_to_grouped(cuts["by_vp_fp"], v_fp, is_rt, contacted, replied, positive, negative, bounced)
            if p_fp:
                add_to_grouped(cuts["by_pp_fp"], p_fp, is_rt, contacted, replied, positive, negative, bounced)

            if rows_seen % 25_000 == 0:
                print(f"  processed {rows_seen} rows...", file=sys.stderr)

    result = {
        "meta": {
            "input_file": str(input_path),
            "total_rows": rows_seen,
            "min_sample_threshold": args.min_sample,
            "fingerprint_len": FINGERPRINT_LEN,
            "retargeting_keyword": args.retargeting_keyword,
        },
        "overall": {seg: overall[seg].as_dict(args.min_sample) for seg in ("retargeting", "new_outbound", "overall")},
        "interest_status_counts": dict(interest_counts),
        **{name: serialize(d, args.min_sample) for name, d in cuts.items()},
        "trigger_examples": text_examples["trigger"],
        "vp_examples": text_examples["vp"],
        "pp_examples": text_examples["pp"],
    }
    output_path.write_text(json.dumps(result, indent=2, ensure_ascii=False))
    print(f"Wrote {output_path} ({output_path.stat().st_size / 1024:.1f} KB) from {rows_seen} rows.")


if __name__ == "__main__":
    run(parse_args())
