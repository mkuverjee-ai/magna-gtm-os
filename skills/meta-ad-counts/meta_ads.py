#!/usr/bin/env python3
"""Count a company's Meta ads (active / inactive x video / static) from the Meta Ad Library via Apify.

Counts only. It never downloads the ads themselves, so a count costs $0.0042 whatever the size.

  whoami                                   token, plan, this month's Apify spend vs cap
  find-page --brand "Cal AI=calai.app"     which Facebook page the brand ACTUALLY advertises from
  count --page 311353912066626             exact counts for one page (the matrix below)
  count --brand "Cal AI=calai.app"         find the page, then count it
  count --keyword "Cal AI"                 approximate: every page whose ads contain the phrase
  bulk --in list.csv --out counts.csv      a whole list, resumable, with --estimate and --max-usd

The matrix (US by default, --country ALL for worldwide):
  active_all  active_video  active_static  inactive_all  inactive_video  inactive_static
  static = image + meme (meme = image with text). Measured on Cal AI: 617 video + 43 meme = 660 active.

Stdlib only. Token: APIFY_TOKEN via gtm.cred (env, ~/.magna-gtm-config, api_keys table).
"""
from __future__ import annotations

import argparse
import concurrent.futures as cf
import csv
import json
import os
import re
import sys
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter

API = "https://api.apify.com/v2"
ACTOR = "apify~facebook-ads-scraper"
COST_PER_CALL = 0.0042          # one onlyTotal run, measured (3,871 runs = $16.26)
COST_PER_AD = 0.0042            # ads returned by a phrase search, measured
PHRASE_ADS = 10                 # ads pulled to work out which page a brand advertises from
CAP = 50001                     # the Ad Library's ceiling: a count at the cap means a generic term
HERE = os.path.dirname(os.path.abspath(__file__))
UA = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) Chrome/125.0 Safari/537.36"}

PAGE_URL = ("https://www.facebook.com/ads/library/?active_status={status}&ad_type=all&country={country}"
            "&is_targeted_country=false&media_type={media}&search_type=page&view_all_page_id={pid}")
KEYWORD_URL = ("https://www.facebook.com/ads/library/?active_status={status}&ad_type=all&country={country}"
               "&is_targeted_country=false&media_type={media}&search_type=keyword_exact_phrase&q={q}")

FULL = [(s, m) for s in ("active", "inactive") for m in ("all", "video", "image", "meme")]
QUICK = [("active", "all"), ("active", "video"), ("active", "image"), ("active", "meme")]
VIDEO_ONLY = [("active", "video")]
PRESETS = {"full": FULL, "active": QUICK, "video": VIDEO_ONLY}

_spend_lock = threading.Lock()
SPEND = {"calls": 0, "ads": 0}


# ---------------------------------------------------------------- api

_TOKEN: list = []
_token_lock = threading.Lock()


def token() -> str:
    """Resolved once and cached. gtm's key cache fills lazily and is not
    thread-safe: bulk workers racing it got nothing (966 of 967 rows failed)."""
    with _token_lock:
        if not _TOKEN:
            _TOKEN.append(_resolve_token())
        return _TOKEN[0]


def _resolve_token() -> str:
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


def call(method, path, body=None, params=None, timeout=300, retries=4):
    url = API + path + ("?" + urllib.parse.urlencode(params) if params else "")
    data = json.dumps(body).encode() if body is not None else None
    headers = {"Authorization": "Bearer " + token(), "Content-Type": "application/json",
               "User-Agent": "meta-ad-counts/1.0"}
    for i in range(retries):
        try:
            req = urllib.request.Request(url, data=data, method=method, headers=headers)
            with urllib.request.urlopen(req, timeout=timeout) as r:
                raw = r.read()
                return json.loads(raw) if raw else {}
        except urllib.error.HTTPError as e:
            msg = e.read().decode(errors="replace")[:400]
            # 403 = the account's monthly hard limit; retrying only burns time.
            if e.code == 403:
                sys.exit(f"Apify 403: monthly limit reached or token refused. {msg}")
            if e.code in (429, 500, 502, 503, 504) and i < retries - 1:
                time.sleep(15 * (i + 1))
                continue
            raise SystemExit(f"Apify HTTP {e.code}: {msg}")
        except (urllib.error.URLError, TimeoutError, ConnectionError):
            if i == retries - 1:
                raise
            time.sleep(15 * (i + 1))
    return {}


def actor(body):
    out = call("POST", f"/acts/{ACTOR}/run-sync-get-dataset-items", body=body)
    return out if isinstance(out, list) else []


def total(url):
    """One onlyTotal run -> (count, page_name)."""
    items = actor({"startUrls": [{"url": url}], "onlyTotal": True})
    with _spend_lock:
        SPEND["calls"] += 1
    it = items[0] if items else {}
    name = ((it.get("pageInfo") or {}).get("page") or {}).get("name")
    return it.get("totalCount") or 0, name


def spent():
    return SPEND["calls"] * COST_PER_CALL + SPEND["ads"] * COST_PER_AD


# ---------------------------------------------------------------- counting

def matrix(pid=None, keyword=None, country="US", combos=FULL, workers=8):
    """Counts for every (status, media) combo, plus static = image + meme."""
    def one(sm):
        s, m = sm
        if pid:
            url = PAGE_URL.format(status=s, country=country, media=m, pid=pid)
        else:
            url = KEYWORD_URL.format(status=s, country=country, media=m,
                                     q=urllib.parse.quote(f'"{keyword}"'))
        return sm, total(url)
    res, page_name = {}, None
    with cf.ThreadPoolExecutor(min(workers, len(combos))) as ex:
        for (s, m), (n, name) in ex.map(one, combos):
            res[f"{s}_{m}"] = n
            page_name = page_name or name
    for s in ("active", "inactive"):
        if f"{s}_image" in res or f"{s}_meme" in res:
            res[f"{s}_static"] = res.pop(f"{s}_image", 0) + res.pop(f"{s}_meme", 0)
    return res, page_name


# ---------------------------------------------------------------- page resolution

def norm(s):
    return re.sub(r"[^a-z0-9]", "", (s or "").lower())


def site_facebook_links(domain):
    links = []
    for host in (f"https://www.{domain}/", f"https://{domain}/"):
        try:
            html = urllib.request.urlopen(urllib.request.Request(host, headers=UA), timeout=20).read().decode("utf-8", "ignore")
        except Exception:  # noqa: BLE001 - many sites block bots; the phrase search covers them
            continue
        for l in re.findall(r'https?://(?:www\.)?facebook\.com/[^"\'\s<>)?]+', html):
            if not re.search(r"sharer|share\.php|/tr$|plugins|dialog", l) and l.rstrip("/") not in [x.rstrip("/") for x in links]:
                links.append(l)
        if links:
            break
    return links[:2]


def find_page(name, domain="", country="US"):
    """Return {page_id, page_name, how, confidence}. Cheapest evidence first.

    1. Facebook links on the brand's own site -> probe each page's active count.
    2. Exact-phrase search on the brand name (10 ads) -> group by page, prefer a name match.
    A brand's site often links a page that runs NO ads while the ads run from another page
    (one brand: site page 0, real page 192), so a site page with 0 ads falls through to step 2.
    """
    n = norm(name)
    for link in (site_facebook_links(domain) if domain else []):
        items = actor({"startUrls": [{"url": link}], "onlyTotal": True, "activeStatus": "active"})
        with _spend_lock:
            SPEND["calls"] += 1
        it = items[0] if items else {}
        page = (it.get("pageInfo") or {}).get("page") or {}
        if page.get("id") and (it.get("totalCount") or 0) > 0:
            conf = "high" if n and (n in norm(page.get("name")) or norm(page.get("name")) in n) else "check"
            return {"page_id": str(page["id"]), "page_name": page.get("name"), "how": "site_link", "confidence": conf}
    url = KEYWORD_URL.format(status="active", country=country, media="all", q=urllib.parse.quote(f'"{name}"'))
    items = [x for x in actor({"startUrls": [{"url": url}], "resultsLimit": PHRASE_ADS})
             if isinstance(x, dict) and x.get("adArchiveID")]
    with _spend_lock:
        SPEND["ads"] += len(items)
    pages = Counter((x.get("pageName"), str(x.get("pageId"))) for x in items).most_common()
    if not pages:
        return {"page_id": "", "page_name": "", "how": "phrase_search", "confidence": "no_ads_found"}
    for (pname, pid), _ in pages:                      # a page whose name matches the brand wins
        pn = norm(pname)
        if n and pn and (pn == n or pn.startswith(n) or n.startswith(pn)):
            return {"page_id": pid, "page_name": pname, "how": "phrase_search", "confidence": "high"}
    (pname, pid), hits = pages[0]                      # else the page running most of the ads
    return {"page_id": pid, "page_name": pname, "how": "phrase_search",
            "confidence": "check" if hits >= len(items) / 2 else "low"}


# ---------------------------------------------------------------- keyword confidence

_WORDS = None


def keyword_confidence(term, domain, count):
    """Keyword counts are only as good as the term. Flag the ones that can't be trusted."""
    global _WORDS
    if _WORDS is None:
        try:
            _WORDS = {w.strip().lower() for w in open("/usr/share/dict/words")}
        except OSError:
            _WORDS = set()
    if count >= CAP:
        return "capped_generic_term"
    words = re.findall(r"[a-z0-9]+", term.lower())
    joined, stem = "".join(words), norm((domain or "").split(".")[0])
    if len(words) >= 4:
        return "long_name_may_undercount"
    if stem and len(joined) >= 4 and (joined == stem or stem.startswith(joined)):
        return "ok"                                     # "Cal AI" on calai.app is a brand, not two words
    if len(joined) <= 3 or all(w in _WORDS or w.rstrip("s") in _WORDS for w in words):
        return "generic_name_use_page_mode"
    return "ok"


def brand_term(app_or_name):
    """'Cal AI - Calorie Tracker' -> 'Cal AI'; 'Strava: Run, Bike' -> 'Strava'."""
    b = re.split(r"\s[-–—|:]\s|:\s|\s\|\s|–|—", app_or_name or "")[0]
    return re.sub(r"[®™©]", "", b).strip()


# ---------------------------------------------------------------- commands

def parse_brand(s):
    name, _, dom = s.partition("=")
    return name.strip(), dom.strip().lower().replace("https://", "").replace("http://", "").replace("www.", "").strip("/")


def cmd_whoami(a):
    me = call("GET", "/users/me")["data"]
    plan = me.get("plan") or {}
    print(f"account : {me.get('username')}")
    print(f"plan    : {plan.get('id')}   monthly usage cap: ${plan.get('maxMonthlyUsageUsd')}")
    try:
        u = call("GET", "/users/me/usage/monthly", retries=1)["data"]
        t = u.get("totalUsageCreditsUsdAfterVolumeDiscount") or u.get("totalUsageCreditsUsdBeforeVolumeDiscount")
        cyc = u.get("usageCycle") or {}
        if t is not None:
            print(f"spent   : ${float(t):.2f} this cycle ({(cyc.get('startAt') or '')[:10]} -> {(cyc.get('endAt') or '')[:10]})")
    except SystemExit:
        print("spent   : (usage endpoint unavailable for this token)")


def cmd_find_page(a):
    for b in a.brand:
        name, dom = parse_brand(b)
        r = find_page(name, dom, a.country)
        print(f"{name} ({dom or 'no domain'}): page_id={r['page_id']} name={r['page_name']!r} via {r['how']} confidence={r['confidence']}")
    print(f"\ncost ~${spent():.3f}")


def print_matrix(label, res, page_name=None):
    print(f"\n== {label}" + (f"  (page: {page_name})" if page_name else ""))
    for k in ("active_all", "active_video", "active_static", "inactive_all", "inactive_video", "inactive_static"):
        if k in res:
            print(f"   {k:16} {res[k]:>7}" + ("   <- at the Ad Library cap, term is too generic" if res[k] >= CAP else ""))


def cmd_count(a):
    combos = PRESETS[a.metrics]
    for pid in a.page:
        res, pname = matrix(pid=pid, country=a.country, combos=combos)
        print_matrix(f"page {pid}", res, pname)
    for b in a.brand:
        name, dom = parse_brand(b)
        p = find_page(name, dom, a.country)
        if not p["page_id"]:
            print(f"\n== {name}: no page found with active ads ({p['confidence']})")
            continue
        res, pname = matrix(pid=p["page_id"], country=a.country, combos=combos)
        print_matrix(f"{name} -> page {p['page_id']} via {p['how']}, confidence {p['confidence']}", res, pname)
    for kw in a.keyword:
        res, _ = matrix(keyword=kw, country=a.country, combos=combos)
        print_matrix(f'keyword "{kw}" (approximate: every page whose ads contain it)', res)
    print(f"\ncountry={a.country}  cost ~${spent():.3f}")


def cmd_bulk(a):
    combos = PRESETS[a.metrics]
    rows = list(csv.DictReader(open(a.inp, newline="", encoding="utf-8-sig")))
    if not rows:
        sys.exit("empty input")
    for col in [a.name_col] + ([a.domain_col] if a.domain_col else []) + ([a.page_col] if a.page_col else []):
        if col not in rows[0]:
            sys.exit(f"column {col!r} not in input. Columns: {list(rows[0])}")
    cache_path = a.out + ".cache.jsonl"
    done = {}
    if os.path.exists(cache_path):
        for l in open(cache_path):
            x = json.loads(l)
            done[x["_key"]] = x

    def key(r):
        return (r.get(a.domain_col) if a.domain_col else "") or r[a.name_col]

    todo = [r for r in rows if key(r) not in done and (r.get(a.name_col) or "").strip()]
    per_row = len(combos) * COST_PER_CALL
    if a.mode == "page":
        per_row += PHRASE_ADS * COST_PER_AD + COST_PER_CALL   # resolve the page first (worst case)
    est = len(todo) * per_row
    print(f"{len(rows)} rows, {len(done)} cached, {len(todo)} to run | mode={a.mode} metrics={a.metrics} "
          f"({len(combos)} counts/row) country={a.country}")
    print(f"estimate: up to ${est:.2f} (${per_row:.4f}/row)  ~{len(todo) * 9 / max(a.workers, 1) / 60:.0f} min at {a.workers} workers")
    if a.estimate:
        return
    if a.max_usd is None:
        sys.exit("Refusing to run without --max-usd. Show the estimate to the user and get a yes on the dollar figure.")
    if est > a.max_usd:
        print(f"estimate ${est:.2f} is over --max-usd {a.max_usd}; will stop when the budget is used up")

    stop = threading.Event()

    def work(r):
        if stop.is_set():
            return None
        if spent() >= a.max_usd:
            stop.set()
            return None
        name = brand_term(r[a.name_col]) if a.clean_names else r[a.name_col].strip()
        dom = (r.get(a.domain_col) or "").strip().lower() if a.domain_col else ""
        out = {"_key": key(r), "search_name": name}
        try:
            if a.mode == "page":
                pid = (r.get(a.page_col) or "").strip() if a.page_col else ""
                p = {"page_id": pid, "page_name": "", "how": "given", "confidence": "given"} if pid else find_page(name, dom, a.country)
                out.update({"page_id": p["page_id"], "page_name": p["page_name"], "page_found_via": p["how"],
                            "confidence": p["confidence"]})
                if p["page_id"]:
                    res, pname = matrix(pid=p["page_id"], country=a.country, combos=combos, workers=4)
                    out.update(res)
                    out["page_name"] = out["page_name"] or pname
            else:
                res, _ = matrix(keyword=name, country=a.country, combos=combos, workers=4)
                out.update(res)
                out["confidence"] = keyword_confidence(name, dom, max(res.values() or [0]))
        except SystemExit as e:
            out["error"] = str(e)[:200]
            if "403" in str(e):
                stop.set()
        return out

    with open(cache_path, "a") as f, cf.ThreadPoolExecutor(a.workers) as ex:
        for i, res in enumerate(ex.map(work, todo)):
            if res is None:
                continue
            f.write(json.dumps(res) + "\n")
            f.flush()
            done[res["_key"]] = res
            if i and i % 100 == 0:
                print(f"  {i}/{len(todo)}  ~${spent():.2f}", flush=True)

    metric_cols = []
    for s in ("active", "inactive"):
        for m in ("all", "video", "static"):
            if any(f"{s}_{m}" in v for v in done.values()):
                metric_cols.append(f"{s}_{m}")
    extra = ["search_name", "page_id", "page_name", "page_found_via", "confidence", "error"]
    fields = list(rows[0].keys()) + [c for c in metric_cols + extra if c not in rows[0]]
    with open(a.out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow({**r, **{k: v for k, v in done.get(key(r), {}).items() if k != "_key"}})
    stopped = " (STOPPED at --max-usd)" if stop.is_set() else ""
    print(f"\nwrote {a.out}  | this run ~${spent():.2f}{stopped}")
    print("confidence:", dict(Counter(v.get("confidence", "") for v in done.values())))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("whoami")

    p = sub.add_parser("find-page")
    p.add_argument("--brand", action="append", required=True, help='"Brand=domain.com" (repeatable)')
    p.add_argument("--country", default="US")

    p = sub.add_parser("count")
    p.add_argument("--page", action="append", default=[], help="Facebook page id (repeatable)")
    p.add_argument("--brand", action="append", default=[], help='"Brand=domain.com" (repeatable)')
    p.add_argument("--keyword", action="append", default=[], help="exact phrase (approximate count)")
    p.add_argument("--metrics", choices=list(PRESETS), default="full",
                   help="full = active+inactive x all/video/static (8 calls); active = active only (4); video = active video (1)")
    p.add_argument("--country", default="US", help="US (default) or ALL, or any 2-letter code")

    p = sub.add_parser("bulk")
    p.add_argument("--in", dest="inp", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--name-col", required=True, help="brand or app name column")
    p.add_argument("--domain-col", help="domain column (helps find the page and judge keyword confidence)")
    p.add_argument("--page-col", help="column that already holds Facebook page ids (skips page lookup)")
    p.add_argument("--mode", choices=["page", "keyword"], default="page",
                   help="page = exact, finds each brand's page (~$0.05+/row); keyword = cheap, approximate")
    p.add_argument("--metrics", choices=list(PRESETS), default="active")
    p.add_argument("--country", default="US")
    p.add_argument("--clean-names", action="store_true", help="cut app names at ' - ' / ':' ('Cal AI - Calorie Tracker' -> 'Cal AI')")
    p.add_argument("--workers", type=int, default=12)
    p.add_argument("--estimate", action="store_true", help="print cost and time, run nothing")
    p.add_argument("--max-usd", type=float, help="hard budget; required for a real run")

    a = ap.parse_args()
    {"whoami": cmd_whoami, "find-page": cmd_find_page, "count": cmd_count, "bulk": cmd_bulk}[a.cmd](a)


if __name__ == "__main__":
    main()
