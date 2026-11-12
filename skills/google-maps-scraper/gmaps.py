#!/usr/bin/env python3
"""Google Maps scraper via Apify (compass/crawler-google-places). Stdlib only, Python 3.9+.

Subcommands:
  whoami                      check the token, plan and this month's Apify spend
  estimate                    worst-case cost for terms x per-term limit (no API call)
  run                         start a scrape, poll with live spend, download + write CSVs
  status  RUN_ID              one status line for a run
  fetch   RUN_ID              download a finished run's results and write CSVs
  filter  --raw raw.json      re-filter results already downloaded (free)
  abort   RUN_ID              stop a run
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

ACTOR = "compass~crawler-google-places"
API = "https://api.apify.com/v2"
# Measured 2026-09-02 on a 7,790-place run: all-in cost per place with skipClosedPlaces on
# (place-scraped + filter-applied + actor start). Apify hides current prices in the API.
COST_PER_PLACE = 0.00275
HERE = os.path.dirname(os.path.abspath(__file__))
TERMINAL = {"SUCCEEDED", "FAILED", "ABORTED", "TIMED-OUT"}

COLS = ["name", "phone", "website", "domain", "street", "city", "state", "postal_code",
        "country_code", "full_address", "category", "all_categories", "search_term",
        "rating", "reviews", "emails", "google_maps_url", "place_id", "lat", "lng",
        "temporarily_closed", "permanently_closed"]


# ---------------------------------------------------------------- api

def token() -> str:
    """APIFY_TOKEN via gtm.cred: environment, then ~/.magna-gtm-config, then the api_keys table."""
    t = os.environ.get("APIFY_TOKEN", "").strip()
    if t:
        return t
    repo = os.path.abspath(os.path.join(HERE, "..", ".."))
    if os.path.exists(os.path.join(repo, "gtm.py")):
        sys.path.insert(0, repo)
        import gtm  # noqa: E402
        t = gtm.cred("APIFY_TOKEN", required=False)
        if t:
            return t
    sys.exit("No Apify token (APIFY_TOKEN). Add it with: python3 gtm.py set-key APIFY_TOKEN")


def call(method: str, path: str, body=None, params=None, retries: int = 4):
    url = API + path
    if params:
        url += "?" + urllib.parse.urlencode(params)
    data = json.dumps(body).encode() if body is not None else None
    headers = {"Authorization": "Bearer " + token(), "Content-Type": "application/json",
               "User-Agent": "gmaps-skill/1.0"}
    for i in range(retries):
        req = urllib.request.Request(url, data=data, method=method, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=180) as r:
                raw = r.read()
                return json.loads(raw) if raw else {}
        except urllib.error.HTTPError as e:
            msg = e.read().decode(errors="replace")[:600]
            if e.code in (429, 500, 502, 503, 504) and i < retries - 1:
                time.sleep(3 * (i + 1))
                continue
            sys.exit(f"Apify {method} {path} -> HTTP {e.code}: {msg}")
        except urllib.error.URLError as e:
            if i < retries - 1:
                time.sleep(3 * (i + 1))
                continue
            sys.exit(f"Network error calling Apify: {e}")


def run_info(run_id: str) -> dict:
    return call("GET", f"/actor-runs/{run_id}")["data"]


def line_for(d: dict) -> str:
    ch = d.get("chargedEventCounts") or {}
    return (f"{d['status']:10s} places={ch.get('place-scraped', 0):>6} "
            f"spent=${(d.get('usageTotalUsd') or 0):.2f}  run={d['id']}")


def download(dataset_id: str) -> list:
    items, offset, page = [], 0, 1000
    while True:
        chunk = call("GET", f"/datasets/{dataset_id}/items",
                     params={"format": "json", "clean": "true", "offset": offset, "limit": page})
        if not isinstance(chunk, list) or not chunk:
            break
        items.extend(chunk)
        offset += len(chunk)
        if len(chunk) < page:
            break
    return items


# ---------------------------------------------------------------- shaping

def domain_of(url) -> str:
    m = re.match(r"https?://(?:www\.)?([^/?#]+)", url or "")
    return m.group(1).lower() if m else ""


def flatten(x: dict) -> dict:
    loc = x.get("location") or {}
    emails = x.get("emails") or []
    return {
        "name": x.get("title"), "phone": x.get("phone"), "website": x.get("website"),
        "domain": domain_of(x.get("website")), "street": x.get("street"), "city": x.get("city"),
        "state": x.get("state"), "postal_code": x.get("postalCode"),
        "country_code": x.get("countryCode"), "full_address": x.get("address"),
        "category": x.get("categoryName"), "all_categories": "; ".join(x.get("categories") or []),
        "search_term": x.get("searchString"), "rating": x.get("totalScore"),
        "reviews": x.get("reviewsCount"),
        "emails": "; ".join(emails) if isinstance(emails, list) else emails,
        "google_maps_url": x.get("url"), "place_id": x.get("placeId"),
        "lat": loc.get("lat"), "lng": loc.get("lng"),
        "temporarily_closed": x.get("temporarilyClosed"),
        "permanently_closed": x.get("permanentlyClosed"),
    }


def apply_filters(rows: list, a) -> tuple:
    """Return (kept, report) where report lists how many each filter removed."""
    report, kept = [], rows
    if getattr(a, "category_regex", None):
        rx = re.compile(a.category_regex, re.I)
        before = len(kept)
        kept = [r for r in kept if rx.search(f"{r['category'] or ''} {r['all_categories'] or ''}")]
        report.append((f"category matches /{a.category_regex}/", before - len(kept)))
    if getattr(a, "exclude_city", None):
        bad = {c.strip().lower() for c in a.exclude_city}
        before = len(kept)
        kept = [r for r in kept if (r["city"] or "").strip().lower() not in bad]
        report.append((f"city not in {sorted(bad)}", before - len(kept)))
    if getattr(a, "only_state", None):
        want = {s.strip().lower() for s in a.only_state}
        before = len(kept)
        kept = [r for r in kept if (r["state"] or "").strip().lower() in want]
        report.append((f"state in {sorted(want)}", before - len(kept)))
    if getattr(a, "require_phone", False):
        before = len(kept)
        kept = [r for r in kept if r["phone"]]
        report.append(("has a phone", before - len(kept)))
    if getattr(a, "require_website", False):
        before = len(kept)
        kept = [r for r in kept if r["website"]]
        report.append(("has a website", before - len(kept)))
    return kept, report


def write_csv(path: str, rows: list) -> None:
    with open(path, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=COLS, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow(r)


def has_filters(a) -> bool:
    return any([getattr(a, "category_regex", None), getattr(a, "exclude_city", None),
                getattr(a, "only_state", None), getattr(a, "require_phone", False),
                getattr(a, "require_website", False)])


def summarize_and_write(items: list, out_dir: str, a) -> None:
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, "raw.json"), "w") as fh:
        json.dump(items, fh)
    rows = [flatten(x) for x in items]
    write_csv(os.path.join(out_dir, "places-all.csv"), rows)

    n = len(rows) or 1
    print(f"\nplaces: {len(rows)}   unique place_id: {len({r['place_id'] for r in rows})}")
    for f in ["phone", "website", "street", "rating", "emails"]:
        c = sum(1 for r in rows if r[f])
        print(f"  {f:10s} {c:6d}  {100 * c // n:3d}%")
    print("per search term:")
    counts = {}
    for r in rows:
        counts[r["search_term"]] = counts.get(r["search_term"], 0) + 1
    for k, v in sorted(counts.items(), key=lambda kv: -kv[1]):
        print(f"  {str(k):40s} {v}")
    cats = {}
    for r in rows:
        cats[r["category"]] = cats.get(r["category"], 0) + 1
    print("top categories:")
    for k, v in sorted(cats.items(), key=lambda kv: -kv[1])[:12]:
        print(f"  {str(k):40s} {v}")
    cities = {}
    for r in rows:
        cities[r["city"]] = cities.get(r["city"], 0) + 1
    print("top cities:")
    for k, v in sorted(cities.items(), key=lambda kv: -kv[1])[:10]:
        print(f"  {str(k):40s} {v}")

    if has_filters(a):
        kept, report = apply_filters(rows, a)
        write_csv(os.path.join(out_dir, "places-filtered.csv"), kept)
        print("\nfilters:")
        for label, removed in report:
            print(f"  kept only: {label:50s} removed {removed}")
        print(f"  => places-filtered.csv: {len(kept)} rows")
    print(f"\nwrote {out_dir}/raw.json, places-all.csv" + (", places-filtered.csv" if has_filters(a) else ""))


# ---------------------------------------------------------------- commands

def cmd_whoami(a) -> None:
    me = call("GET", "/users/me")["data"]
    plan = me.get("plan") or {}
    print(f"account : {me.get('username')}")
    print(f"plan    : {plan.get('id')}   monthly usage cap: ${plan.get('maxMonthlyUsageUsd')}")
    try:
        u = call("GET", "/users/me/usage/monthly", retries=1)["data"]
        total = u.get("totalUsageCreditsUsdAfterVolumeDiscount") or u.get("totalUsageCreditsUsdBeforeVolumeDiscount")
        cycle = u.get("usageCycle") or {}
        if total is not None:
            print(f"spent   : ${float(total):.2f} this cycle "
                  f"({(cycle.get('startAt') or '')[:10]} -> {(cycle.get('endAt') or '')[:10]})")
    except SystemExit:
        print("spent   : (usage endpoint unavailable for this token)")


def terms_from(a) -> list:
    terms = list(a.terms or [])
    if getattr(a, "terms_file", None):
        terms += [t.strip() for t in open(a.terms_file) if t.strip()]
    terms = [t for t in dict.fromkeys(terms) if t]
    if not terms:
        sys.exit("Give at least one search term with --terms or --terms-file.")
    return terms


def cmd_estimate(a) -> None:
    terms = terms_from(a)
    ceiling = len(terms) * a.per_term
    print(f"search terms      : {len(terms)}")
    print(f"per-term limit    : {a.per_term}")
    print(f"ceiling (places)  : {ceiling:,}   = terms x per-term limit")
    print(f"ceiling (cost)    : ${ceiling * COST_PER_PLACE:,.2f}   at ${COST_PER_PLACE}/place")
    print("Real cost is usually far lower: runs stop when Google runs out of results.")


def build_input(a, terms: list) -> dict:
    inp = {
        "searchStringsArray": terms,
        "maxCrawledPlacesPerSearch": a.per_term,
        "language": a.language,
        "skipClosedPlaces": not a.include_closed,
        "scrapePlaceDetailPage": False,
        "scrapeContacts": bool(a.contacts),
        "maximumLeadsEnrichmentRecords": 0,
        "maxReviews": 0,
        "maxImages": 0,
        "maxQuestions": 0,
    }
    if a.location:
        inp["locationQuery"] = a.location
    if a.country:
        inp["countryCode"] = a.country.lower()
    if a.state:
        inp["state"] = a.state
    if a.city:
        inp["city"] = a.city
    if a.postal_code:
        inp["postalCode"] = a.postal_code
    if not any([a.location, a.country, a.state, a.city, a.postal_code]):
        sys.exit("Give a location: --location \"Illinois, USA\" (or --country/--state/--city/--postal-code).")
    if a.min_stars:
        inp["placeMinimumStars"] = a.min_stars
    if a.website_filter:
        inp["website"] = a.website_filter
    if a.search_matching:
        inp["searchMatching"] = a.search_matching
    return inp


def cmd_run(a) -> None:
    terms = terms_from(a)
    if a.max_usd < 0.50:
        sys.exit("--max-usd must be at least 0.50 (Apify's minimum budget cap per run).")
    if a.pilot:
        a.per_term = min(a.per_term, 30) if a.per_term else 30
    inp = build_input(a, terms)
    ceiling = len(terms) * a.per_term
    worst = ceiling * COST_PER_PLACE
    print(f"terms={len(terms)} per_term={a.per_term} ceiling={ceiling:,} places "
          f"worst-case=${worst:,.2f} budget cap=${a.max_usd:.2f}")
    print("input:", json.dumps(inp))
    if a.dry_run:
        print("\n--dry-run: nothing started, nothing spent.")
        return

    started = call("POST", f"/acts/{ACTOR}/runs", body=inp,
                   params={"maxTotalChargeUsd": f"{a.max_usd:.2f}"})["data"]
    run_id, ds = started["id"], started["defaultDatasetId"]
    print(f"\nstarted run {run_id}   dataset {ds}")
    print(f"console: https://console.apify.com/actors/runs/{run_id}")
    if a.detach:
        print("detached. Check with:  gmaps.py status " + run_id + "   then  gmaps.py fetch " + run_id)
        return

    last = ""
    while True:
        d = run_info(run_id)
        cur = line_for(d)
        if cur != last:
            print(time.strftime("%H:%M:%S"), cur, flush=True)
            last = cur
        if d["status"] in TERMINAL:
            break
        if (d.get("usageTotalUsd") or 0) > a.max_usd * 1.02:
            print(f"spend passed the ${a.max_usd:.2f} cap, aborting run", flush=True)
            call("POST", f"/actor-runs/{run_id}/abort")
        time.sleep(a.poll)

    if d["status"] != "SUCCEEDED":
        print(f"run ended {d['status']} - downloading whatever it collected")
    items = download(ds)
    out = a.out_dir or os.path.join(os.getcwd(), "gmaps-output",
                                    f"{slug(terms[0])}-{dt.date.today().isoformat()}-{run_id[:6]}")
    summarize_and_write(items, out, a)
    print(f"final cost: ${(d.get('usageTotalUsd') or 0):.2f}")


def slug(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")[:40] or "gmaps"


def cmd_status(a) -> None:
    print(line_for(run_info(a.run_id)))


def cmd_fetch(a) -> None:
    d = run_info(a.run_id)
    print(line_for(d))
    if d["status"] not in TERMINAL:
        print("run still going; this downloads what it has so far")
    items = download(d["defaultDatasetId"])
    out = a.out_dir or os.path.join(os.getcwd(), "gmaps-output", f"run-{a.run_id}")
    summarize_and_write(items, out, a)


def cmd_filter(a) -> None:
    items = json.load(open(a.raw))
    out = a.out_dir or os.path.dirname(os.path.abspath(a.raw))
    rows = [flatten(x) for x in items]
    kept, report = apply_filters(rows, a)
    path = os.path.join(out, a.name)
    write_csv(path, kept)
    print(f"input rows: {len(rows)}")
    for label, removed in report:
        print(f"  kept only: {label:50s} removed {removed}")
    print(f"wrote {path}: {len(kept)} rows")


def cmd_abort(a) -> None:
    call("POST", f"/actor-runs/{a.run_id}/abort")
    print("abort requested:", line_for(run_info(a.run_id)))


# ---------------------------------------------------------------- cli

def add_filters(p) -> None:
    p.add_argument("--category-regex", help="keep rows whose Google category matches, e.g. 'law|attorney|legal'")
    p.add_argument("--exclude-city", nargs="+", help="drop these cities, e.g. Chicago")
    p.add_argument("--only-state", nargs="+", help="keep only these states, e.g. Illinois IL")
    p.add_argument("--require-phone", action="store_true")
    p.add_argument("--require-website", action="store_true")
    p.add_argument("--out-dir")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    sub.add_parser("whoami").set_defaults(fn=cmd_whoami)

    e = sub.add_parser("estimate")
    e.add_argument("--terms", nargs="+")
    e.add_argument("--terms-file")
    e.add_argument("--per-term", type=int, required=True)
    e.set_defaults(fn=cmd_estimate)

    r = sub.add_parser("run")
    r.add_argument("--terms", nargs="+", help='search terms, e.g. "dentist" "orthodontist"')
    r.add_argument("--terms-file", help="one search term per line")
    r.add_argument("--location", help='free text, e.g. "Illinois, USA" or "Austin, Texas, USA"')
    r.add_argument("--country", help="two-letter code, e.g. us")
    r.add_argument("--state")
    r.add_argument("--city")
    r.add_argument("--postal-code")
    r.add_argument("--per-term", type=int, default=30, help="max places PER SEARCH TERM (not total)")
    r.add_argument("--pilot", action="store_true", help="cap at 30 per term to measure yield + cost")
    r.add_argument("--max-usd", type=float, required=True, help="hard budget: Apify stops charging past this")
    r.add_argument("--language", default="en")
    r.add_argument("--include-closed", action="store_true", help="keep closed places (default skips them)")
    r.add_argument("--min-stars", choices=["two", "twoAndHalf", "three", "threeAndHalf", "four", "fourAndHalf"])
    r.add_argument("--website-filter", choices=["allPlaces", "withWebsite", "withoutWebsite"])
    r.add_argument("--search-matching", choices=["all", "only_includes", "only_exact"],
                   help="only_includes = place name must contain the term")
    r.add_argument("--contacts", action="store_true",
                   help="PAID ADD-ON: crawl each website for emails/socials. Pilot first to measure cost.")
    r.add_argument("--detach", action="store_true", help="start and return immediately")
    r.add_argument("--dry-run", action="store_true", help="print the input and cost, start nothing")
    r.add_argument("--poll", type=int, default=30)
    add_filters(r)
    r.set_defaults(fn=cmd_run)

    s = sub.add_parser("status")
    s.add_argument("run_id")
    s.set_defaults(fn=cmd_status)

    f = sub.add_parser("fetch")
    f.add_argument("run_id")
    add_filters(f)
    f.set_defaults(fn=cmd_fetch)

    fl = sub.add_parser("filter")
    fl.add_argument("--raw", required=True, help="raw.json from a previous run")
    fl.add_argument("--name", default="places-filtered.csv")
    add_filters(fl)
    fl.set_defaults(fn=cmd_filter)

    ab = sub.add_parser("abort")
    ab.add_argument("run_id")
    ab.set_defaults(fn=cmd_abort)

    a = ap.parse_args()
    a.fn(a)


if __name__ == "__main__":
    main()
