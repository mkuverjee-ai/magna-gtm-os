#!/usr/bin/env python3
"""AI Ark from the command line: search, preview, pull, export single.

This is how the OS calls AI Ark. It goes through curl (see the transport note
below), pages for you, and flattens every person and company into a clean CSV.

    A="python3 skills/ai-ark/aiark.py"
    $A credits                                            # free
    $A preview  --body b.json                             # 1 credit/page
    $A people   --body b.json --size 50 --out people.csv  # 0.5/result
    $A companies --body b.json --size 100 --out co.csv    # 0.1/result
    $A person   --id <uuid>                               # export single, 1 credit if an email is found

`--body` is a JSON file holding the AI Ark request body (see reference.md for the
filter shapes). `--known a.csv b.csv` reports how many returned records are already
in CSVs you pulled before, and `--new-only` keeps those out of the output CSV so the
next paid step (deep research, email finding) only runs on new rows.

A preview masks last names and returns no LinkedIn URL, so a preview CSV is for
judging a list, never for outreach.
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..", "..")))
import gtm  # noqa: E402

BASE = "https://api.ai-ark.com/api/developer-portal"
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36"
CPK, OPK = "ai_ark_people_id", "ai_ark_account_id"

# Employee bands used in the CSV output. Keep this vocabulary stable across pulls.
BANDS = [(0, 1), (2, 10), (11, 50), (51, 200), (201, 500), (501, 1000),
         (1001, 5000), (5001, 10000), (10001, None)]


# ── AI Ark transport ─────────────────────────────────────────────────────────
# macOS system Python 3.9 ships LibreSSL 2.8.3 and cannot negotiate AI Ark's TLS,
# so this always goes through curl. A Python TLS error here is not a dead key.

def ark(path: str, body: dict | None = None, method: str = "POST") -> dict:
    key = (gtm.cred("AI_ARK_API_KEY", required=False) or "").strip()
    if not key:
        sys.exit("No AI_ARK_API_KEY. Add it with: python3 gtm.py set-key AI_ARK_API_KEY")
    args = ["curl", "-s", "-X", method, f"{BASE}{path}",
            "-H", f"X-TOKEN: {key}", "-H", "Content-Type: application/json",
            "-H", "Accept: application/json", "-H", f"User-Agent: {UA}"]
    if body is not None:
        args += ["--data-binary", json.dumps(body)]
    out = subprocess.run(args, capture_output=True, text=True, timeout=180)
    if not out.stdout.strip():
        sys.exit(f"AI Ark returned nothing ({out.stderr.strip()[:200]})")
    try:
        return json.loads(out.stdout)
    except json.JSONDecodeError:
        sys.exit(f"AI Ark returned non-JSON: {out.stdout[:300]}")


# ── helpers ──────────────────────────────────────────────────────────────────

def g(obj, *path, default=None):
    """Walk nested dicts without raising on a null branch."""
    for p in path:
        if not isinstance(obj, dict):
            return default
        obj = obj.get(p)
    return obj if obj is not None else default


def band(rng: dict | None, total=None) -> str | None:
    start, end = g(rng or {}, "start"), g(rng or {}, "end")
    if start is None and total is None:
        return None
    if start is None:
        start = total
    for lo, hi in BANDS:
        if start <= lo if hi is None else (lo <= start <= hi):
            return f"{lo}+" if hi is None else f"{lo}-{hi}"
    return None


def joined(items, key=None) -> str | None:
    if not isinstance(items, list) or not items:
        return None
    vals = [str(i.get(key) if key and isinstance(i, dict) else i) for i in items]
    vals = [v for v in vals if v and v != "None"]
    return ", ".join(vals[:40]) or None


def strip(rec: dict) -> dict:
    """Drop empties so the CSV only carries fields AI Ark actually returned."""
    return {k: v for k, v in rec.items() if v not in (None, "", [], {})}


# ── AI Ark object -> flat CSV row ─────────────────────────────────────────

def map_company(c: dict) -> dict | None:
    cid = c.get("id")
    if not cid:
        return None
    hq = g(c, "location", "headquarter", default={})
    fund = g(c, "financial", "funding", default={})
    return strip({
        OPK: cid,
        "company_name": g(c, "summary", "name"),
        "company_name_for_emails": g(c, "summary", "legal_name"),
        "website": g(c, "link", "domain") or g(c, "link", "domain_ltd"),
        "domain_url": g(c, "link", "website"),
        "linkedin": g(c, "link", "linkedin"),
        "facebook": g(c, "link", "facebook"),
        "x_twitter": g(c, "link", "twitter"),
        "industry": g(c, "summary", "industry"),
        "industry_tags": joined(c.get("industries")),
        "product_and_services": joined(c.get("keywords")),
        "description": g(c, "summary", "description"),
        "seo_description": g(c, "summary", "seo"),
        "founding_year": g(c, "summary", "founded_year"),
        "company_type": g(c, "summary", "type"),
        "headcount": g(c, "summary", "staff", "total"),
        "employee_size": band(g(c, "summary", "staff", "range"), g(c, "summary", "staff", "total")),
        "company_country": hq.get("country"),
        "company_state": hq.get("state"),
        "company_city": hq.get("city"),
        "company_address": hq.get("raw_address"),
        "number_of_locations": len(g(c, "location", "locations", default=[])) or None,
        "annual_revenue": g(c, "financial", "revenue", "annual", "amount"),
        "total_funding": fund.get("total_amount"),
        "last_funding_amount": fund.get("last_amount"),
        "last_funding_type": fund.get("type"),
        "last_funding_date": fund.get("date"),
        "last_updated": c.get("last_updated"),
        "raw": json.dumps(c)[:400000],
    })


def map_contact(p: dict) -> dict | None:
    pid = p.get("id")
    if not pid:
        return None
    co = p.get("company") or {}
    hq = g(co, "location", "headquarter", default={})
    fund = g(co, "financial", "funding", default={})
    loc = p.get("location") or {}
    # AI Ark's email object: {address, status, subStatus, domainType, free, generic,
    # found, date, mx:{record, provider, google, found}}. The address is `address`,
    # NOT `email`, and the provider lives INSIDE mx. Reading `email` silently drops
    # every address while status and domainType still arrive, so the row looks fine.
    emails = g(p, "email", "output", default=[]) or []
    em = emails[0] if isinstance(emails, list) and emails and isinstance(emails[0], dict) else {}
    mx = em.get("mx") if isinstance(em.get("mx"), dict) else {}
    first, last = g(p, "profile", "first_name"), g(p, "profile", "last_name")
    full = g(p, "profile", "full_name") or (" ".join(x for x in (first, last) if x) or None)
    return strip({
        CPK: pid,
        "first_name": first,
        "last_name": last,
        "full_name": full,
        "title": g(p, "profile", "title"),
        "linkedin": g(p, "link", "linkedin"),
        "seniority": g(p, "department", "seniority"),
        "department": (g(p, "department", "departments", default=[]) or [None])[0],
        "country": loc.get("country"),
        "state": loc.get("state"),
        "city": loc.get("city"),
        "location": loc.get("default"),
        "email_business": em.get("address") or em.get("email"),
        "business_status": em.get("status") or em.get("state"),
        "email_provider": mx.get("provider") or em.get("provider"),
        "domain_settings": em.get("domainType"),
        "mx_records": mx.get("record") or (joined(em.get("mx")) if isinstance(em.get("mx"), list) else None),
        "organization": g(co, "summary", "name"),
        "company_ai_ark_account_id": co.get("id"),
        "company_name": g(co, "summary", "name"),
        "company_name_for_emails": g(co, "summary", "legal_name"),
        "company_website": g(co, "link", "domain") or g(co, "link", "domain_ltd"),
        "company_linkedin": g(co, "link", "linkedin"),
        "company_facebook": g(co, "link", "facebook"),
        "company_x_twitter": g(co, "link", "twitter"),
        "company_industry": g(co, "summary", "industry"),
        "company_industry_tags": joined(co.get("industries")),
        "company_product_and_services": joined(co.get("keywords")),
        "company_description": g(co, "summary", "description"),
        "company_seo_description": g(co, "summary", "seo"),
        "company_founding_year": g(co, "summary", "founded_year"),
        "company_type": g(co, "summary", "type"),
        "company_size": g(co, "summary", "staff", "total"),
        "company_employee_count": band(g(co, "summary", "staff", "range"), g(co, "summary", "staff", "total")),
        "company_country": hq.get("country"),
        "company_state": hq.get("state"),
        "company_city": hq.get("city"),
        "company_location": hq.get("raw_address"),
        "company_annual_revenue": g(co, "financial", "revenue", "annual", "amount"),
        "company_total_funding": fund.get("total_amount"),
        "company_last_funding_amount": fund.get("last_amount"),
        "company_last_funding_type": fund.get("type"),
        "company_last_funding_date": fund.get("date"),
        "company_last_updated": co.get("last_updated"),
        "last_updated": p.get("last_updated"),
        "raw": json.dumps(p)[:400000],
    })


# ── local de-dup against a CSV you already hold ──────────────────────────────

ID_COLS = ("id", CPK, OPK)


def known_ids(paths: list) -> set:
    """AI Ark ids already present in one or more CSVs you pulled earlier.

    This CANNOT make the search cheaper: AI Ark bills the query, and which records
    match is only knowable by running it. What it saves is every paid step AFTER
    this one (deep research, email finding), which is where the real money goes."""
    out = set()
    for path in paths or []:
        with open(path, newline="") as f:
            for row in csv.DictReader(f):
                for col in ID_COLS:
                    v = (row.get(col) or "").strip()
                    if v:
                        out.add(v)
    return out


def report_overlap(label: str, got: list, known: set) -> None:
    if not known or not got:
        return
    n = sum(1 for r in got if r.get("id") in known)
    print(f"  already in your --known CSVs: {n} of {len(got)} {label} ({round(100 * n / len(got))}%)")


# ── output ───────────────────────────────────────────────────────────────────

def dump_csv(rows: list, path: str):
    if not rows:
        return
    cols = sorted({k for r in rows for k in r if k != "raw"})
    os.makedirs(os.path.dirname(os.path.abspath(path)) or ".", exist_ok=True)
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k) for k in cols})
    print(f"  wrote {len(rows)} rows -> {path}")


def load_body(path: str) -> dict:
    with open(path) as f:
        return json.load(f)


def pages(path: str, body: dict, size: int, n_pages: int) -> list:
    got = []
    for page in range(n_pages):
        d = ark(path, {**body, "page": page, "size": size})
        content = d.get("content") or []
        if page == 0:
            print(f"  totalElements: {d.get('totalElements')}")
        got += content
        if not content or d.get("last"):
            break
    return got


# ── commands ─────────────────────────────────────────────────────────────────

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    def common(p, needs_body=True):
        if needs_body:
            p.add_argument("--body", required=True, help="JSON file with the AI Ark request body")
        p.add_argument("--size", type=int, default=25)
        p.add_argument("--pages", type=int, default=1)
        p.add_argument("--out", help="write the results to a CSV")
        p.add_argument("--known", nargs="*", default=[],
                       help="CSVs from earlier pulls; their AI Ark ids count as already held")
        p.add_argument("--new-only", dest="new_only", action="store_true",
                       help="with --known: the output CSV gets only records not already held")

    sub.add_parser("credits")
    common(sub.add_parser("preview"))
    common(sub.add_parser("people"))
    common(sub.add_parser("companies"))
    pp = sub.add_parser("person")
    pp.add_argument("--id")
    pp.add_argument("--url")
    common(pp, needs_body=False)
    a = ap.parse_args()

    if a.cmd == "credits":
        print(f"AI Ark credits: {ark('/v1/payments/credits', method='GET').get('total')}")
        return

    if getattr(a, "new_only", False) and not a.known:
        sys.exit("--new-only needs --known <csv> [<csv> ...] to compare against")
    known = known_ids(getattr(a, "known", []))

    if a.cmd == "preview":
        got = pages("/v1/people/preview", load_body(a.body), a.size, a.pages)
        print(f"  {len(got)} previewed (last names masked, no emails)")
        report_overlap("people", got, known)
        if a.out:
            dump_csv([{"id": p.get("id"), "first_name": g(p, "profile", "first_name"),
                       "title": g(p, "profile", "title"), "seniority": g(p, "department", "seniority"),
                       "company": g(p, "company", "summary", "name"),
                       "country": g(p, "location", "country"),
                       "has_mobile": p.get("has_mobile")} for p in got], a.out)
        return

    if a.cmd == "people":
        got = pages("/v1/people", load_body(a.body), a.size, a.pages)
        print(f"  {len(got)} people")
        report_overlap("people", got, known)
        if a.out:
            rows = [p for p in got if not (a.new_only and p.get("id") in known)]
            if a.new_only:
                print(f"  --new-only: {len(rows)} of {len(got)} people written to the CSV")
            dump_csv([map_contact(p) for p in rows if map_contact(p)], a.out)
        return

    if a.cmd == "companies":
        got = pages("/v1/companies", load_body(a.body), a.size, a.pages)
        print(f"  {len(got)} companies")
        report_overlap("companies", got, known)
        if a.out:
            rows = [c for c in got if not (a.new_only and c.get("id") in known)]
            if a.new_only:
                print(f"  --new-only: {len(rows)} of {len(got)} companies written to the CSV")
            dump_csv([map_company(c) for c in rows if map_company(c)], a.out)
        return

    if a.cmd == "person":
        if not (a.id or a.url):
            sys.exit("person needs --id or --url")
        body = {"id": a.id} if a.id else {"url": a.url}
        d = ark("/v1/people/export/single", body)
        if not d.get("id"):
            print("  no result (404 means not found, and costs nothing)")
            return
        print(f"  {g(d, 'profile', 'full_name')} - {g(d, 'profile', 'title')}")
        if a.out:
            dump_csv([map_contact(d)], a.out)
        return


if __name__ == "__main__":
    main()
