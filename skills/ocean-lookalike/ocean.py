#!/usr/bin/env python3
"""Ocean.io lookalike company search: one seed domain in, companies like it out.

    O="python3 skills/ocean-lookalike/ocean.py"
    $O count acme.com                                    # how many lookalikes exist (0.2 credits)
    $O count acme.com --size 51-200,201-500 --country US,GB
    $O find  acme.com --limit 50 --out plays/<play-slug>/leads/companies/x.csv
    $O find  acme.com,stripe.com --limit 100 --out x.csv   # up to 5 seeds, blended

Ocean is the way this OS asks "who looks like this company". AI Ark answers
"who matches these filters", which is a different question. Use Ocean when you have a
customer worth cloning and Ocean's own similarity model is the filter.

Cost is 0.2 credits per company returned, measured. `count` returns the full match
total for a single row, so always size the set before spending on it.
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

BASE = "https://api.ocean.io/v3/search/companies"
PAGE = 100  # Ocean's per-call ceiling

FIELDS = ["name", "domain", "primaryCountry", "countries", "companySize",
          "industries", "linkedinIndustry", "industryCategories",
          "employeeCountOcean", "employeeCountLinkedin", "revenue",
          "yearFounded", "description", "keywords", "medias.linkedin",
          "locations.primary", "locations.locality", "locations.region",
          "fundingRound", "fundingRound.date", "fundingRound.type",
          "fundingRound.moneyRaisedInUsd", "departmentSizes"]

FLAT = ["name", "domain", "primaryCountry", "companySize", "employeeCountOcean",
        "employeeCountLinkedin", "revenue", "yearFounded", "linkedinIndustry",
        "industries", "linkedin", "locality", "region", "funding_type",
        "funding_date", "funding_usd", "relevance", "description"]


def ocean(body: dict) -> dict:
    """curl, not urllib: same LibreSSL story as AI Ark on macOS system Python."""
    key = (gtm.cred("OCEAN_API_KEY", required=False) or "").strip()
    if not key:
        sys.exit("No OCEAN_API_KEY. Ocean.io is optional; if you have a key, "
                 "add it with: python3 gtm.py set-key OCEAN_API_KEY")
    args = ["curl", "-s", "-X", "POST", BASE,
            "-H", f"x-api-token: {key}", "-H", "Content-Type: application/json",
            "--data-binary", json.dumps(body)]
    out = subprocess.run(args, capture_output=True, text=True, timeout=180)
    if not out.stdout.strip():
        sys.exit(f"Ocean returned nothing ({out.stderr.strip()[:200]})")
    try:
        d = json.loads(out.stdout)
    except json.JSONDecodeError:
        sys.exit(f"Ocean returned non-JSON: {out.stdout[:300]}")
    if isinstance(d.get("detail"), str) and d["detail"] not in ("OK", ""):
        sys.exit(f"Ocean error: {d['detail'][:300]}")
    if "companies" not in d:
        sys.exit(f"Ocean error: {json.dumps(d)[:300]}")
    return d


def filters(a) -> dict:
    """A seed domain is required. Everything else narrows it."""
    f: dict = {"lookalikeDomains": [d.strip() for d in a.seeds.split(",") if d.strip()][:5]}
    if a.size:
        f["companySizes"] = [s.strip() for s in a.size.split(",") if s.strip()]
    if a.country:
        f["primaryLocations"] = {"includeCountries":
                                 [c.strip().upper() for c in a.country.split(",") if c.strip()]}
    return f


def flatten(item: dict) -> dict:
    c = item.get("company") or {}
    # locations is a LIST of {primary: bool, locality, region}, not a dict, and
    # medias.linkedin is an OBJECT with .url, not a string. Both bite on first use.
    locs = c.get("locations") or []
    loc = next((x for x in locs if isinstance(x, dict) and x.get("primary")),
               (locs[0] if locs and isinstance(locs[0], dict) else {}))
    fund = c.get("fundingRound") or {}
    li = ((c.get("medias") or {}).get("linkedin") or {})
    return {
        "name": c.get("name"),
        "domain": c.get("domain"),
        "primaryCountry": (c.get("primaryCountry") or "").upper(),
        "companySize": c.get("companySize"),
        "employeeCountOcean": c.get("employeeCountOcean"),
        "employeeCountLinkedin": c.get("employeeCountLinkedin"),
        "revenue": c.get("revenue"),
        "yearFounded": c.get("yearFounded"),
        "linkedinIndustry": c.get("linkedinIndustry"),
        "industries": ", ".join(c.get("industries") or [])[:300],
        "linkedin": li.get("url") if isinstance(li, dict) else li,
        "locality": loc.get("locality"),
        "region": loc.get("region"),
        "funding_type": fund.get("type"),
        "funding_date": fund.get("date"),
        "funding_usd": fund.get("moneyRaisedInUsd"),
        "relevance": item.get("relevance"),
        "description": (c.get("description") or "")[:500],
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("count", "find"):
        p = sub.add_parser(name)
        p.add_argument("seeds", help="seed domain, or up to 5 comma-separated")
        p.add_argument("--size", help='e.g. "51-200,201-500"')
        p.add_argument("--country", help='ISO-2, e.g. "US,GB,CA"')
        if name == "find":
            p.add_argument("--limit", type=int, default=25)
            p.add_argument("--out", help="write a CSV")
    a = ap.parse_args()

    if a.cmd == "count":
        d = ocean({"size": 1, "companiesFilters": filters(a), "fields": ["domain"]})
        total = d.get("total")
        print(f"  {total} lookalike companies match ({d.get('creditsUsed')} credits to ask)")
        print(f"  pulling all of them would cost about {round((total or 0) * 0.2, 1)} credits")
        return

    got, after, spent = [], None, 0.0
    while len(got) < a.limit:
        body = {"size": min(PAGE, a.limit - len(got)),
                "companiesFilters": filters(a), "fields": FIELDS}
        if after:
            body["searchAfter"] = after
        d = ocean(body)
        rows = d.get("companies") or []
        spent += float(d.get("creditsUsed") or 0)
        got += rows
        after = d.get("searchAfter")
        if not rows or not after:
            break
    print(f"  {len(got)} lookalikes of {a.seeds} (of {d.get('total')} matching) "
          f"- {round(spent, 1)} credits")
    flat = [flatten(i) for i in got]
    for r in flat[:8]:
        print(f"    {str(r['domain'])[:34]:36} {str(r['companySize'] or ''):10} "
              f"{str(r['primaryCountry'] or ''):3} {str(r['name'] or '')[:30]}")
    if len(flat) > 8:
        print(f"    ... and {len(flat) - 8} more")
    if a.out:
        os.makedirs(os.path.dirname(os.path.abspath(a.out)) or ".", exist_ok=True)
        with open(a.out, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=FLAT, extrasaction="ignore")
            w.writeheader()
            w.writerows(flat)
        print(f"  wrote {len(flat)} rows -> {a.out}")


if __name__ == "__main__":
    main()
