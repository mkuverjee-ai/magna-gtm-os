#!/usr/bin/env python3
"""LinkedIn scraper: posts from profiles, and the people who engaged with them.

Built on two Apify actors (posts + engagers); writes CSVs. Stdlib only.

    L="python3 skills/linkedin-scraper/linkedin.py"
    $L whoami                                              # Apify spend vs cap
    $L posts    URL [URL ...] --window week --max-posts 10 --out posts.csv
    $L engagers POST_URL [POST_URL ...] --out engagers.csv [--no-comments]
    $L harvest  URL [URL ...] --window week --out engagers.csv      # posts -> engagers
    $L ... --urls-file profiles.txt                        # one URL per line instead of args

Every paid command takes --max-usd (required) and stops charging at that amount.
The token (APIFY_TOKEN) is resolved by gtm.cred: environment, ~/.magna-gtm-config, api_keys table.
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))

POSTS_ACTOR = "A3cAPGpwBEG8RJwse"
REACTIONS_ACTOR = "harvestapi~linkedin-post-reactions"
COMMENTS_ACTOR = "harvestapi~linkedin-post-comments"
# The post actor accepts coarse tokens only. "7d" / "30d" return HTTP 400.
WINDOWS = ["24h", "week", "month", "year"]


def token() -> str:
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


def _get(path: str) -> dict:
    req = urllib.request.Request(f"https://api.apify.com/v2/{path}",
                                 headers={"Authorization": f"Bearer {token()}"})
    return json.load(urllib.request.urlopen(req, timeout=30))["data"]


def run_actor(actor: str, payload: dict, max_usd: float, timeout: int = 600) -> list:
    """Run synchronously and return the dataset. Raises on failure: an Apify error must
    never look like 'no posts' (that once hid a dead key for three weeks)."""
    url = (f"https://api.apify.com/v2/acts/{actor}/run-sync-get-dataset-items"
           f"?maxTotalChargeUsd={max_usd}")
    req = urllib.request.Request(url, data=json.dumps(payload).encode(), method="POST",
                                 headers={"Content-Type": "application/json",
                                          "Authorization": f"Bearer {token()}"})
    last = ""
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            last = f"HTTP {e.code}: {e.read()[:300]!r}"
            if e.code in (400, 401, 402, 403):
                break
        except Exception as e:  # noqa: BLE001
            last = str(e)
        time.sleep(5 * (attempt + 1))
    sys.exit(f"Apify {actor} failed: {last}")


# ------------------------------------------------------------------ posts

def fetch_posts(profile: str, window: str, max_posts: int, max_usd: float) -> list[dict]:
    items = run_actor(POSTS_ACTOR, {
        "targetUrls": [profile], "postedLimit": window, "maxPosts": max_posts,
        "includeQuotePosts": True, "includeReposts": True,
        "scrapeComments": False, "scrapeReactions": False,
        "maxComments": 0, "maxReactions": 0,
        "postNestedComments": False, "postNestedReactions": False,
    }, max_usd)
    out, seen = [], set()
    for it in items:
        url = it.get("linkedinUrl") or it.get("url") or ""
        # The actor sometimes returns a post twice; dedupe on the URN, not the URL text.
        key = it.get("shareUrn") or it.get("entityId") or url
        if not url or key in seen:
            continue
        seen.add(key)
        pa = it.get("postedAt") if isinstance(it.get("postedAt"), dict) else {}
        ts = pa.get("timestamp")
        eng = it.get("engagement") or {}
        author = it.get("author") or {}
        author_url = author.get("linkedinUrl") or author.get("url") or ""
        # A reshare carries the ORIGINAL post's engagement (inflated a count 70x once).
        is_repost = bool(it.get("repostedBy") or it.get("isRepost") or it.get("reshared"))
        out.append({
            "profile": profile,
            "post_url": url,
            "posted_at": datetime.fromtimestamp(ts / 1000, timezone.utc).isoformat(timespec="seconds") if ts else "",
            "author": author.get("name") or "",
            "author_url": author_url,
            "is_repost": is_repost,
            "reactions": eng.get("likes") or eng.get("reactions") or "",
            "comments": eng.get("comments") or "",
            "shares": eng.get("shares") or "",
            "content": (it.get("content") or "").replace("\n", " ")[:1000],
        })
    return out


# ------------------------------------------------------------------ engagers

def _slug(url: str) -> str:
    m = re.search(r"/in/([^/?#]+)", url or "")
    return m.group(1).lower() if m else (url or "").lower()


def fetch_engagers(post_url: str, comments: bool, max_per_post: int, max_usd: float) -> list[dict]:
    rows: dict[str, dict] = {}

    def add(a: dict, kind: str, text: str = "") -> None:
        url = a.get("linkedinUrl") or a.get("publicUrl") or a.get("url") or ""
        name = a.get("name") or f"{a.get('firstName', '')} {a.get('lastName', '')}".strip()
        if not url and not name:
            return
        loc = a.get("location") or a.get("locationName") or ""
        if isinstance(loc, dict):
            loc = loc.get("linkedinText") or loc.get("name") or ""
        key = _slug(url) if url else name.lower()
        if key in rows:
            if text and not rows[key]["comment_text"]:
                rows[key]["comment_text"] = text
                rows[key]["engagement_type"] += "+comment"
            return
        parts = name.split()
        rows[key] = {
            "post_url": post_url, "name": name,
            "first_name": parts[0] if parts else "",
            "last_name": " ".join(parts[1:]),
            "headline": a.get("position") or a.get("headline") or a.get("occupation") or "",
            "linkedin_url": url, "location": loc,
            "engagement_type": kind, "comment_text": text,
        }

    for it in run_actor(REACTIONS_ACTOR, {
        "posts": [post_url], "maxItems": max_per_post,
        "reactionTypeFilter": ["ALL"], "profileScraperMode": "short",
    }, max_usd):
        add(it.get("actor") or it.get("profile") or it, (it.get("reactionType") or "reaction").lower())
    if comments:
        for it in run_actor(COMMENTS_ACTOR, {"posts": [post_url], "maxItems": max_per_post}, max_usd):
            a = it.get("actor") or it.get("author") or it.get("commenter") or it.get("profile") or it
            add(a, "comment", (it.get("commentText") or it.get("text") or "").replace("\n", " "))
    return list(rows.values())


# ------------------------------------------------------------------ io

def urls_from(args) -> list[str]:
    urls = list(args.urls or [])
    if getattr(args, "urls_file", None):
        urls += [l.strip() for l in open(args.urls_file) if l.strip() and not l.startswith("#")]
    if not urls:
        sys.exit("Give at least one URL (or --urls-file).")
    return list(dict.fromkeys(urls))


def write_csv(path: str, rows: list[dict]) -> None:
    if not rows:
        print(f"  0 rows, nothing written to {path}")
        return
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print(f"  {len(rows)} rows -> {path}")


def spent() -> float:
    try:
        return float(_get("users/me/usage/monthly").get("totalUsageCreditsUsdAfterVolumeDiscount") or 0)
    except Exception:  # noqa: BLE001
        return -1.0


def cmd_whoami(_a) -> None:
    me = _get("users/me")
    plan = me.get("plan") or {}
    print(f"account : {me.get('username')}   plan: {plan.get('id')}")
    used = spent()
    print(f"spent   : ${used:.2f} of ${plan.get('maxMonthlyUsageUsd')} this cycle" if used >= 0
          else "spent   : unknown")
    print("Every run on this token counts against the cap. Check the headroom before a big run.")


def cmd_posts(a) -> None:
    rows = []
    for u in urls_from(a):
        got = fetch_posts(u, a.window, a.max_posts, a.max_usd)
        print(f"  {len(got):3d} posts  {u}")
        rows += got
    if a.originals_only:
        rows = [r for r in rows if not r["is_repost"]]
    write_csv(a.out, rows)


def cmd_engagers(a) -> None:
    rows = []
    for u in urls_from(a):
        got = fetch_engagers(u, not a.no_comments, a.max_per_post, a.max_usd)
        print(f"  {len(got):4d} engagers  {u}")
        rows += got
    write_csv(a.out, rows)


def cmd_harvest(a) -> None:
    posts = []
    for u in urls_from(a):
        got = fetch_posts(u, a.window, a.max_posts, a.max_usd)
        if a.originals_only:
            got = [p for p in got if not p["is_repost"]]
        print(f"  {len(got):3d} posts  {u}")
        posts += got
    if a.posts_out:
        write_csv(a.posts_out, posts)
    rows: dict[str, dict] = {}
    for p in posts:
        for e in fetch_engagers(p["post_url"], not a.no_comments, a.max_per_post, a.max_usd):
            key = _slug(e["linkedin_url"]) or e["name"].lower()
            if key in rows:  # one row per person; count how many posts they engaged with
                rows[key]["posts_engaged"] += 1
                continue
            rows[key] = {**e, "engaged_with_profile": p["profile"], "posts_engaged": 1}
        print(f"      {len(rows):5d} unique engagers so far")
    write_csv(a.out, list(rows.values()))


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("whoami").set_defaults(fn=cmd_whoami)

    def common(p, what):
        p.add_argument("urls", nargs="*", help=what)
        p.add_argument("--urls-file")
        p.add_argument("--out", required=True)
        p.add_argument("--max-usd", type=float, required=True,
                       help="Apify stops charging at this amount, per actor call")

    p = sub.add_parser("posts"); common(p, "profile or company URLs")
    p.add_argument("--window", choices=WINDOWS, default="week")
    p.add_argument("--max-posts", type=int, default=10)
    p.add_argument("--originals-only", action="store_true", help="drop reshares")
    p.set_defaults(fn=cmd_posts)

    p = sub.add_parser("engagers"); common(p, "post URLs")
    p.add_argument("--no-comments", action="store_true")
    p.add_argument("--max-per-post", type=int, default=1000)
    p.set_defaults(fn=cmd_engagers)

    p = sub.add_parser("harvest"); common(p, "profile or company URLs")
    p.add_argument("--window", choices=WINDOWS, default="week")
    p.add_argument("--max-posts", type=int, default=5)
    p.add_argument("--originals-only", action="store_true")
    p.add_argument("--no-comments", action="store_true")
    p.add_argument("--max-per-post", type=int, default=1000)
    p.add_argument("--posts-out", help="also save the post list")
    p.set_defaults(fn=cmd_harvest)

    a = ap.parse_args()
    before = spent() if a.cmd != "whoami" else -1
    a.fn(a)
    if before >= 0:
        after = spent()
        if after >= 0:
            print(f"  Apify spend this run: ~${after - before:.2f} (usage can lag a minute)")


if __name__ == "__main__":
    main()
