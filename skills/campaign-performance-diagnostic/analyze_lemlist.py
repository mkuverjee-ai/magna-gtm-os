"""
Generic Lemlist lead export analyser (LinkedIn pillar).

Stream a Lemlist campaign / lead export CSV and emit a structured
JSON of LinkedIn connection rates, reply rates, positive-reply rates, and step
completion rates. Cuts by time, campaign, persona, industry, persona x
industry, company size, and copy-theme fingerprints.

This script is intentionally tolerant: Lemlist exports vary in shape depending
on which view the operator exports. Common column names are tried in order,
and the script reports which columns it ended up using so the operator can
verify the read was correct.

Usage:
    python3 analyze_lemlist.py <path-to-lemlist-export.csv>
        [--min-sample 100]
        [--output _lemlist_analysis.json]

Outputs `_lemlist_analysis.json` next to the input by default.

If the operator did not provide a Lemlist export, do not invoke this script.
The Instantly analyser (analyze_leads.py) is the primary pipeline.
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

# Common Lemlist column candidates (probed in order until one is non-empty for the row).
COL_CANDIDATES = {
    "campaign": ["campaignName", "Campaign", "campaign", "Campaign Name"],
    "first_name": ["firstName", "First Name", "first_name"],
    "company": ["companyName", "Company", "company"],
    "title": ["title", "jobTitle", "Title", "Job Title"],
    "linkedin_url": ["linkedinUrl", "LinkedIn URL", "linkedin_url", "linkedin"],
    "persona": ["Persona", "persona"],
    "industry": ["industry", "Industry", "Person - Industry", "Sector"],
    "size": ["companyHeadCount", "company_size_range", "companySize"],
    "step": ["step", "currentStep", "Step", "stepIndex"],
    "status": ["state", "leadState", "Lead State", "status"],
    "connected": ["isConnected", "isConnectionAccepted", "connectionAccepted"],
    "reply_count": ["replyCount", "linkedinReplyCount", "messageReplyCount"],
    "interest_status": ["interestStatus", "Interest Status", "outcome"],
    "timestamp": ["lastActivityAt", "addedAt", "createdAt", "timestamp_created"],
    "trigger": ["Trigger", "trigger"],
    "icebreaker": ["icebreaker", "Icebreaker", "openingLine"],
}


def parse_args(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    p.add_argument("csv_path", help="Path to the Lemlist export CSV.")
    p.add_argument("--min-sample", type=int, default=100, help="Confidence threshold. Default: %(default)s")
    p.add_argument("--output", help="Override output path (default: _lemlist_analysis.json next to input).")
    return p.parse_args(argv)


def first_present(row: dict, keys: list[str]) -> str:
    for k in keys:
        v = (row.get(k) or "").strip()
        if v:
            return v
    return ""


def truthy(v: str) -> bool:
    return v.strip().lower() in {"true", "yes", "1", "y"}


def fingerprint(text: str) -> str:
    if not text:
        return ""
    return re.sub(r"\s+", " ", text.strip())[:FINGERPRINT_LEN]


class Tally:
    __slots__ = ("uploaded", "engaged", "connected", "replied", "positive", "negative")

    def __init__(self):
        self.uploaded = 0
        self.engaged = 0  # received at least one message in the sequence
        self.connected = 0
        self.replied = 0
        self.positive = 0
        self.negative = 0

    def add(self, engaged, connected, replied, positive, negative):
        self.uploaded += 1
        if engaged:
            self.engaged += 1
        if connected:
            self.connected += 1
        if replied:
            self.replied += 1
        if positive:
            self.positive += 1
        if negative:
            self.negative += 1

    def as_dict(self, min_sample: int):
        engaged = self.engaged or 0
        connection_rate = (self.connected / self.uploaded * 100) if self.uploaded else 0.0
        reply_rate = (self.replied / max(engaged, 1) * 100) if engaged else 0.0
        pos_rate = (self.positive / max(engaged, 1) * 100) if engaged else 0.0
        return {
            "uploaded": self.uploaded,
            "engaged": self.engaged,
            "connected": self.connected,
            "replied": self.replied,
            "positive": self.positive,
            "negative": self.negative,
            "connection_rate": round(connection_rate, 3),
            "reply_rate": round(reply_rate, 3),
            "positive_rate": round(pos_rate, 3),
            "low_sample": self.engaged < min_sample,
        }


def run(args):
    input_path = Path(args.csv_path).expanduser().resolve()
    if not input_path.exists():
        sys.exit(f"Input CSV not found: {input_path}")
    output_path = (
        Path(args.output).expanduser().resolve() if args.output else input_path.with_name("_lemlist_analysis.json")
    )

    overall = Tally()
    cuts = {
        "by_month": {},
        "by_campaign": {},
        "by_persona": {},
        "by_industry": {},
        "by_persona_industry": {},
        "by_step": {},
        "by_icebreaker_fp": {},
    }
    icebreaker_examples = {}
    columns_used = {}
    interest_counts = collections.Counter()
    rows_seen = 0

    with input_path.open(newline="", encoding="utf-8", errors="replace") as f:
        reader = csv.DictReader(f)
        header = reader.fieldnames or []
        # Record which header we matched for each logical column.
        for logical, candidates in COL_CANDIDATES.items():
            columns_used[logical] = next((c for c in candidates if c in header), "")
        for row in reader:
            rows_seen += 1
            campaign = first_present(row, COL_CANDIDATES["campaign"]) or "(unknown campaign)"
            persona = (first_present(row, COL_CANDIDATES["persona"]) or "unknown").lower()
            industry = (first_present(row, COL_CANDIDATES["industry"]) or "unknown").lower()
            step = first_present(row, COL_CANDIDATES["step"]) or "unknown"
            timestamp = first_present(row, COL_CANDIDATES["timestamp"])
            month = timestamp[:7] if timestamp else "unknown"
            interest = first_present(row, COL_CANDIDATES["interest_status"])
            interest_counts[interest] += 1

            try:
                reply_count = int(first_present(row, COL_CANDIDATES["reply_count"]) or 0)
            except ValueError:
                reply_count = 0
            connected = truthy(first_present(row, COL_CANDIDATES["connected"]))
            replied = reply_count > 0
            engaged = connected or replied or (first_present(row, COL_CANDIDATES["status"]) not in ("", "paused", "queued"))
            positive = interest == "Interested"
            negative = interest in {"Not interested", "Wrong person", "Do not contact"}

            icebreaker_text = first_present(row, COL_CANDIDATES["icebreaker"])
            ice_fp = fingerprint(icebreaker_text)
            if ice_fp and ice_fp not in icebreaker_examples:
                icebreaker_examples[ice_fp] = icebreaker_text

            overall.add(engaged, connected, replied, positive, negative)

            def grouped_add(target, key):
                if key not in target:
                    target[key] = Tally()
                target[key].add(engaged, connected, replied, positive, negative)

            grouped_add(cuts["by_month"], month)
            grouped_add(cuts["by_campaign"], campaign)
            grouped_add(cuts["by_persona"], persona)
            grouped_add(cuts["by_industry"], industry)
            grouped_add(cuts["by_persona_industry"], f"{persona} | {industry}")
            grouped_add(cuts["by_step"], step)
            if ice_fp:
                grouped_add(cuts["by_icebreaker_fp"], ice_fp)

            if rows_seen % 10_000 == 0:
                print(f"  processed {rows_seen} rows...", file=sys.stderr)

    def serialize(d):
        return {k: v.as_dict(args.min_sample) for k, v in d.items()}

    result = {
        "meta": {
            "input_file": str(input_path),
            "total_rows": rows_seen,
            "min_sample_threshold": args.min_sample,
            "fingerprint_len": FINGERPRINT_LEN,
            "columns_used": columns_used,
        },
        "overall": overall.as_dict(args.min_sample),
        "interest_status_counts": dict(interest_counts),
        **{name: serialize(d) for name, d in cuts.items()},
        "icebreaker_examples": icebreaker_examples,
    }
    output_path.write_text(json.dumps(result, indent=2, ensure_ascii=False))
    print(f"Wrote {output_path} ({output_path.stat().st_size / 1024:.1f} KB) from {rows_seen} rows.")
    missing = [k for k, v in columns_used.items() if not v]
    if missing:
        print(
            "WARNING: these logical columns were not found in the Lemlist header: "
            + ", ".join(missing)
            + ". Update COL_CANDIDATES at the top of this script if the export uses different names.",
            file=sys.stderr,
        )


if __name__ == "__main__":
    run(parse_args())
