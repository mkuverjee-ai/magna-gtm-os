#!/usr/bin/env python3
"""
Magna GTM OS: the command-line helper everything else runs on.

One company, one team, one repo. There is no client roster:
the unit of work is a *play* (one segment or one campaign) in plays/<slug>/,
and the company's own context lives in company/context.md.

Credentials resolve in this order, for every name:
    1. environment variable
    2. ~/.magna-gtm-config   (JSON, chmod 600, never committed)
    3. the `api_keys` table in your own database (if one is configured)

The only thing a teammate ever holds locally is the database key (or, with no
database, the tool keys themselves in ~/.magna-gtm-config). Rotating a tool key
is one `set-key` and reaches everyone on their next command.

Logs (sessions, what-worked intelligence, call transcripts) go to the database
when one is configured, otherwise to JSONL files under log/ that are committed
with /save, so the team still shares them.

Usage:
    python3 gtm.py whoami
    python3 gtm.py team
    python3 gtm.py company                    # context + which keys are present
    python3 gtm.py keys                       # every known key, present or missing (masked)
    echo -n '<key>' | python3 gtm.py set-key INSTANTLY_API_KEY [--local] [--yes]
    python3 gtm.py campaigns [--platform instantly|lemlist] [--json]
    python3 gtm.py plays
    python3 gtm.py play <slug>
    python3 gtm.py new-play <slug> [--title "..."]
    python3 gtm.py meetings [--limit 5]
    python3 gtm.py transcript --date 2026-10-16
    python3 gtm.py log-session --summary "..." [--play slug] [--files a,b] [--skills x,y]
    python3 gtm.py log-intel --play slug --category copy_angle --label "..." --insight "..."
    python3 gtm.py intel [--play slug] [--category x]
    python3 gtm.py doctor
"""

from __future__ import annotations

import argparse
import base64
import datetime
import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Optional

# The python.org macOS installer ships without root certificates, so every HTTPS
# call fails with CERTIFICATE_VERIFY_FAILED until "Install Certificates.command"
# is run. If certifi is importable, point the whole process at its bundle.
if not os.environ.get("SSL_CERT_FILE"):
    try:
        import certifi
        os.environ["SSL_CERT_FILE"] = certifi.where()
    except ImportError:
        pass

REPO = Path(__file__).resolve().parent
CONFIG_PATH = Path.home() / ".magna-gtm-config"
LOG_DIR = REPO / "log"
FLAGS_PATH = Path.home() / ".magna-gtm-flags.json"

# Every key the OS knows about, what it unlocks, and whether you can work without it.
KNOWN_KEYS = [
    ("INSTANTLY_API_KEY", "Instantly: email campaigns, leads, inboxes, numbers", "must"),
    ("LEMLIST_API_KEY", "Lemlist: email + LinkedIn sequences, inbox, numbers", "must"),
    ("AI_ARK_API_KEY", "AI Ark: companies, people and emails (the list-building source)", "must"),
    ("APIFY_TOKEN", "Apify: Google Maps, LinkedIn engagers, Meta ad counts", "optional"),
    ("EXA_API_KEY", "Exa: web research and signal search", "optional"),
    ("OCEAN_API_KEY", "Ocean.io: lookalike companies from a seed domain", "optional"),
    ("FIREFLIES_API_KEY", "Fireflies: pull call transcripts into the meetings log", "optional"),
    ("ANTHROPIC_API_KEY", "Claude API, only for scripts that call a model headless", "optional"),
    ("FLOQER_API_KEY", "Floqer workflows", "optional"),
    ("RAILWAY_WORKSPACE_TOKEN", "Railway: host a daily job, webhook or dashboard", "optional"),
    ("CRM_PROVIDER", "Which CRM: salesforce or hubspot", "must"),
    ("CRM_API_KEY", "CRM token (HubSpot private-app token, or Salesforce access token)", "must"),
    ("CRM_INSTANCE_URL", "Salesforce only: https://<your-domain>.my.salesforce.com", "optional"),
]
_BOOTSTRAP = {"MAGNA_DB_URL", "MAGNA_DB_KEY"}

INTEL_CATEGORIES = ["copy_angle", "subject_line", "segment", "persona", "send_time", "offer",
                    "cta", "channel", "list_source", "deliverability", "event", "signal"]

_UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
       "(KHTML, like Gecko) Chrome/126.0 Safari/537.36")


# ── config ──────────────────────────────────────────────────────────────────

def _config() -> dict:
    try:
        return json.loads(CONFIG_PATH.read_text())
    except (OSError, ValueError):
        return {}


def _write_config(cfg: dict) -> None:
    CONFIG_PATH.write_text(json.dumps(cfg, indent=2) + "\n")
    os.chmod(CONFIG_PATH, 0o600)


def me() -> str:
    return os.environ.get("GTM_NAME") or _config().get("name") or ""


def has_db() -> bool:
    return bool(_raw_cred("MAGNA_DB_URL") and _raw_cred("MAGNA_DB_KEY"))


def _raw_cred(name: str) -> Optional[str]:
    val = os.environ.get(name)
    if not val:
        cfg = _config()
        val = cfg.get(name) or cfg.get(name.lower())
    return (val or "").strip() or None


_db_keys: Optional[dict] = None


def _db_key_table() -> dict:
    """The api_keys table, fetched once per process and never written to disk."""
    global _db_keys
    if _db_keys is None:
        _db_keys = {}
        if has_db():
            try:
                for row in get("api_keys?select=name,value"):
                    _db_keys[row["name"]] = row["value"]
            except SystemExit:
                pass
    return _db_keys


def cred(name: str, required: bool = True) -> Optional[str]:
    """Environment -> ~/.magna-gtm-config -> api_keys in your database."""
    val = _raw_cred(name)
    if not val and name not in _BOOTSTRAP:
        val = _db_key_table().get(name)
    if not val and required:
        sys.exit(f"Missing credential: {name}\n"
                 f"  Add it with:  python3 gtm.py set-key {name}   (paste the value, then Ctrl-D)\n"
                 f"  It goes to the team database if one is set up, otherwise to {CONFIG_PATH}.")
    return val


def mask(secret: Optional[str]) -> str:
    return f"…{secret[-4:]} ({len(secret)} chars)" if secret else "missing"


# ── database (Supabase REST) ────────────────────────────────────────────────

def _request(method: str, path: str, body: Any = None, extra: Optional[dict] = None) -> Any:
    url = cred("MAGNA_DB_URL").rstrip("/") + "/rest/v1/" + path
    key = cred("MAGNA_DB_KEY")
    headers = {"apikey": key, "Authorization": f"Bearer {key}", "Content-Type": "application/json"}
    headers.update(extra or {})
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            raw = r.read()
            return json.loads(raw) if raw else []
    except urllib.error.HTTPError as e:
        sys.exit(f"Database {method} {path.split('?')[0]} failed [{e.code}]: {e.read().decode()[:300]}")
    except urllib.error.URLError as e:
        if "CERTIFICATE_VERIFY_FAILED" in str(e.reason):
            sys.exit("Python can't verify HTTPS certificates. Fix:  python3 -m pip install --user certifi")
        sys.exit(f"Can't reach the database: {e.reason}")


def get(path: str) -> Any:
    return _request("GET", path)


def post(table: str, payload: Any, upsert: bool = False) -> Any:
    prefer = "return=representation" + (",resolution=merge-duplicates" if upsert else "")
    return _request("POST", table, payload, {"Prefer": prefer})


def _log(table: str, row: dict) -> str:
    """Write a log row to the database, or to log/<table>.jsonl when there is none."""
    row = {k: v for k, v in row.items() if v not in (None, "", [])}
    if has_db():
        post(table, row)
        return "database"
    LOG_DIR.mkdir(exist_ok=True)
    row.setdefault("at", datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"))
    with open(LOG_DIR / f"{table}.jsonl", "a") as f:
        f.write(json.dumps(row) + "\n")
    return f"log/{table}.jsonl"


def _read(table: str, query: str = "", limit: int = 50) -> list:
    if has_db():
        sep = "&" if query else ""
        return get(f"{table}?{query}{sep}order=at.desc&limit={limit}")
    p = LOG_DIR / f"{table}.jsonl"
    if not p.exists():
        return []
    rows = [json.loads(l) for l in p.read_text().splitlines() if l.strip()]
    return list(reversed(rows))[:limit]


# ── sending platforms (read-only) ───────────────────────────────────────────

def _http_json(url: str, auth: str) -> Any:
    # Instantly and Lemlist sit behind Cloudflare and reject urllib's default
    # User-Agent with a 403 that looks exactly like a bad key. Pin a browser UA.
    req = urllib.request.Request(url, headers={"Authorization": auth, "User-Agent": _UA,
                                               "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def _lemlist_auth(key: str) -> str:
    return "Basic " + base64.b64encode(f":{key}".encode()).decode()


def verify_key(name: str, key: str) -> tuple:
    """Live read-only check for the two sending keys. (ok, message); ok None = not checkable."""
    try:
        if name == "INSTANTLY_API_KEY":
            _http_json("https://api.instantly.ai/api/v2/campaigns?limit=1", f"Bearer {key}")
            return True, "Instantly accepted it"
        if name == "LEMLIST_API_KEY":
            team = _http_json("https://api.lemlist.com/api/team", _lemlist_auth(key))
            return True, f"Lemlist team: {team.get('name') or 'ok'}"
    except urllib.error.HTTPError as e:
        if e.code in (401, 403):
            return False, f"rejected (HTTP {e.code}): wrong key or wrong workspace"
        if e.code == 402:
            return False, "HTTP 402: the key is real but billing has lapsed"
        return None, f"HTTP {e.code}, couldn't confirm"
    except Exception as e:  # noqa: BLE001
        return None, f"couldn't reach the API ({e.__class__.__name__})"
    return None, "no live check for this key, saved as given"


INSTANTLY_STATUS = {0: "draft", 1: "active", 2: "paused", 3: "completed", 4: "running subsequences",
                    -99: "suspended", -1: "accounts unhealthy", -2: "bounce protect"}


def instantly_campaigns() -> list:
    key = cred("INSTANTLY_API_KEY", required=False)
    if not key:
        return []
    out, cursor = [], None
    for _ in range(20):
        url = "https://api.instantly.ai/api/v2/campaigns?limit=100" + (
            f"&starting_after={urllib.parse.quote(cursor)}" if cursor else "")
        body = _http_json(url, f"Bearer {key}")
        for c in body.get("items", []):
            out.append({"platform": "instantly", "id": c.get("id"), "name": c.get("name"),
                        "status": INSTANTLY_STATUS.get(c.get("status"), str(c.get("status"))),
                        "updated": (c.get("timestamp_updated") or c.get("timestamp_created") or "")[:10]})
        cursor = body.get("next_starting_after")
        if not cursor:
            break
    return out


def lemlist_campaigns() -> list:
    key = cred("LEMLIST_API_KEY", required=False)
    if not key:
        return []
    body = _http_json("https://api.lemlist.com/api/campaigns?version=v2&limit=100", _lemlist_auth(key))
    items = body.get("campaigns", body) if isinstance(body, dict) else body
    out = []
    for c in items or []:
        out.append({"platform": "lemlist", "id": c.get("_id"), "name": c.get("name"),
                    "status": c.get("status") or ("archived" if c.get("archived") else "unknown"),
                    "updated": (c.get("createdAt") or "")[:10]})
    return out


# ── commands ────────────────────────────────────────────────────────────────

def cmd_whoami(_a) -> None:
    print(f"  you       : {me() or '(not set, run ./onboard)'}")
    print(f"  config    : {CONFIG_PATH} {'(present)' if CONFIG_PATH.exists() else '(missing)'}")
    print(f"  database  : {'connected' if has_db() else 'none, logging to log/*.jsonl in the repo'}")


def cmd_team(_a) -> None:
    names = []
    if has_db():
        try:
            names = [r["name"] for r in get("team?select=name&active=eq.true&order=name")]
        except SystemExit:
            names = []
    if not names:
        p = REPO / "company" / "team.md"
        if p.exists():
            names = [l[2:].split("|")[0].strip() for l in p.read_text().splitlines() if l.startswith("- ")]
    for n in names:
        print(n)


def cmd_keys(_a) -> None:
    db = _db_key_table() if has_db() else {}
    print(f"  {'key':<26} {'need':<9} {'where':<9} value")
    for name, what, need in KNOWN_KEYS:
        where = "env" if os.environ.get(name) else "local" if _raw_cred(name) else "database" if db.get(name) else "-"
        print(f"  {name:<26} {need:<9} {where:<9} {mask(cred(name, required=False))}   {what}")
    extra = sorted(set(db) - {k for k, _, _ in KNOWN_KEYS})
    for name in extra:
        print(f"  {name:<26} {'custom':<9} {'database':<9} {mask(db[name])}")


def cmd_key(a) -> None:
    """Prints a key ONLY with --raw, for $(...) inside a command. Never echo it to the chat."""
    val = cred(a.name)
    print(val if a.raw else mask(val))


def cmd_set_key(a) -> None:
    name = a.name.upper()
    if sys.stdin.isatty():
        print(f"Paste the value for {name}, then press Enter and Ctrl-D:", file=sys.stderr)
    val = sys.stdin.read().strip()
    if not val:
        sys.exit("Nothing on stdin. Usage: echo -n '<key>' | python3 gtm.py set-key NAME")
    ok, msg = verify_key(name, val)
    print(f"  check: {msg}")
    if ok is False:
        sys.exit("  Not saved.")
    to_db = has_db() and not a.local
    if not a.yes and sys.stdin.isatty():
        if input(f"  Save {name} to {'the team database' if to_db else CONFIG_PATH}? [y/N] ").lower() != "y":
            sys.exit("  Not saved.")
    if to_db:
        post("api_keys?on_conflict=name", {"name": name, "value": val, "updated_by": me() or None,
                                           "updated_at": datetime.datetime.now(datetime.timezone.utc).isoformat()},
             upsert=True)
        print(f"  saved {name} to the team database ({mask(val)}). Everyone has it on their next command.")
    else:
        cfg = _config()
        cfg[name] = val
        _write_config(cfg)
        print(f"  saved {name} to {CONFIG_PATH} ({mask(val)}). Only this laptop has it.")


def _context_summary() -> str:
    p = REPO / "company" / "context.md"
    if not p.exists():
        return "  company/context.md is missing. Create it before writing any copy."
    text = p.read_text()
    flag = "  (carries a DRAFT banner: not yet confirmed by the team)\n" if "DRAFT" in text[:400] else ""
    heads = [l.strip("# ").strip() for l in text.splitlines() if l.startswith("## ")]
    return f"  company/context.md, {len(text):,} chars\n{flag}  sections: {', '.join(heads)}"


def cmd_company(_a) -> None:
    print(_context_summary())
    missing = [n for n, _, need in KNOWN_KEYS if need == "must" and not cred(n, required=False)]
    print(f"  must-have keys missing: {', '.join(missing) or 'none'}")
    print(f"  plays: {len(_plays())}   database: {'yes' if has_db() else 'no (log/ files)'}")


def _plays() -> list:
    root = REPO / "plays"
    return sorted(p for p in root.iterdir() if p.is_dir() and not p.name.startswith("_")) if root.exists() else []


def _play_meta(p: Path) -> dict:
    meta = {"slug": p.name, "title": p.name, "status": "?", "platform": "", "updated": ""}
    readme = p / "PLAY.md"
    if readme.exists():
        for line in readme.read_text().splitlines():
            m = re.match(r"\|\s*\*\*(\w[\w ]*)\*\*\s*\|\s*(.*?)\s*\|", line)
            if m:
                meta[m.group(1).strip().lower()] = m.group(2).strip()
            if line.startswith("# ") and meta["title"] == p.name:
                meta["title"] = line[2:].strip()
    out = subprocess.run(["git", "log", "-1", "--format=%cs", "--", str(p)], cwd=REPO,
                         capture_output=True, text=True).stdout.strip()
    meta["updated"] = out or "uncommitted"
    return meta


def cmd_plays(_a) -> None:
    plays = _plays()
    if not plays:
        print("  No plays yet. Start one with:  python3 gtm.py new-play <slug>")
        return
    for p in plays:
        m = _play_meta(p)
        print(f"  {m['slug']:<34} {m.get('status', '?'):<10} {m.get('platform', ''):<18} {m['updated']}")


def cmd_play(a) -> None:
    p = REPO / "plays" / a.slug
    if not p.is_dir():
        near = [x.name for x in _plays() if a.slug.lower() in x.name]
        sys.exit(f"No play '{a.slug}'." + (f" Did you mean: {', '.join(near)}" if near else
                                           " List them with: python3 gtm.py plays"))
    m = _play_meta(p)
    print(f"  {m['title']}  ({m['slug']}, last change {m['updated']})")
    for k in ("status", "platform", "segment", "offer", "campaigns"):
        if m.get(k):
            print(f"  {k:<10}: {m[k]}")
    for sub in ("research", "leads/companies", "leads/contacts", "campaigns", "reports"):
        files = sorted(x.name for x in (p / sub).glob("*") if x.is_file() and x.name != ".gitkeep") \
            if (p / sub).exists() else []
        print(f"  {sub + '/':<17} {len(files)} file(s)" + (f": {', '.join(files[-4:])}" if files else ""))
    intel = [r for r in _read("intelligence", f"play=eq.{a.slug}", 10) if r.get("play") == a.slug]
    if intel:
        print("  what worked:")
        for r in intel[:5]:
            print(f"    [{r.get('category')}] {r.get('label')}: {r.get('insight', '')[:110]}")


def cmd_new_play(a) -> None:
    slug = re.sub(r"[^a-z0-9]+", "-", a.slug.lower()).strip("-")
    dst = REPO / "plays" / slug
    if dst.exists():
        sys.exit(f"plays/{slug} already exists.")
    tpl = REPO / "plays" / "_template"
    for sub in ("research", "leads/companies", "leads/contacts", "campaigns", "reports"):
        (dst / sub).mkdir(parents=True, exist_ok=True)
        (dst / sub / ".gitkeep").touch()
    text = (tpl / "PLAY.md").read_text() if (tpl / "PLAY.md").exists() else "# {title}\n"
    today = datetime.date.today().isoformat()
    (dst / "PLAY.md").write_text(text.replace("{title}", a.title or slug.replace("-", " ").title())
                                 .replace("{owner}", me() or "?").replace("{date}", today))
    print(f"  created plays/{slug}/  (PLAY.md + research, leads, campaigns, reports)")


def cmd_campaigns(a) -> None:
    rows = []
    for plat, fn in (("instantly", instantly_campaigns), ("lemlist", lemlist_campaigns)):
        if a.platform and a.platform != plat:
            continue
        try:
            rows += fn()
        except urllib.error.HTTPError as e:
            print(f"  {plat}: HTTP {e.code}, couldn't list campaigns", file=sys.stderr)
        except Exception as e:  # noqa: BLE001
            print(f"  {plat}: {e.__class__.__name__}, couldn't list campaigns", file=sys.stderr)
    if a.json:
        print(json.dumps(rows, indent=2))
        return
    if not rows:
        print("  No campaigns returned (check `python3 gtm.py keys`).")
        return
    for r in sorted(rows, key=lambda r: (r["platform"], r["status"], r["name"] or "")):
        print(f"  {r['platform']:<10} {r['status']:<20} {r['name']}")


def cmd_meetings(a) -> None:
    rows = _read("meetings", "select=at,title,summary", a.limit)
    if not rows:
        print("  No calls logged. Optional: if you record calls (Fireflies, Granola), see "
              "skills/fireflies-usage to pull them in.")
        return
    for r in rows:
        print(f"  {str(r.get('at', ''))[:10]}  {r.get('title', '')}")
        if r.get("summary"):
            print("     " + r["summary"].replace("\n", " ")[:220])


def cmd_transcript(a) -> None:
    rows = _read("meetings", f"at=gte.{a.date}T00:00:00&at=lt.{a.date}T23:59:59", 5)
    rows = [r for r in rows if str(r.get("at", "")).startswith(a.date)]
    if not rows:
        sys.exit(f"No call logged on {a.date}.")
    for r in rows:
        print(f"# {r.get('title')}  ({r.get('at')})\n")
        print(r.get("transcript") or r.get("summary") or "(no text stored)")


def cmd_log_session(a) -> None:
    where = _log("sessions", {"who": a.who or me(), "play": a.play, "summary": a.summary,
                              "files": _csv(a.files), "skills": _csv(a.skills)})
    print(f"  session logged ({where})")


def cmd_log_intel(a) -> None:
    if a.category not in INTEL_CATEGORIES:
        sys.exit(f"category must be one of: {', '.join(INTEL_CATEGORIES)}")
    where = _log("intelligence", {
        "who": a.who or me(), "play": a.play, "category": a.category, "label": a.label,
        "insight": a.insight, "recommendation": a.recommendation, "sample_size": a.sample_size,
        "reply_rate": a.reply_rate, "confidence": a.confidence, "status": a.status})
    print(f"  intelligence logged ({where})")


def cmd_intel(a) -> None:
    q = "&".join(f for f in (f"play=eq.{a.play}" if a.play else "",
                             f"category=eq.{a.category}" if a.category else "") if f)
    rows = _read("intelligence", q, 50)
    rows = [r for r in rows if (not a.play or r.get("play") == a.play)
            and (not a.category or r.get("category") == a.category)]
    if not rows:
        print("  Nothing logged yet. /save offers to log what worked after each campaign.")
        return
    for r in rows:
        n = f" n={r['sample_size']}" if r.get("sample_size") else ""
        rr = f" reply={r['reply_rate']}%" if r.get("reply_rate") else ""
        print(f"  {str(r.get('at', ''))[:10]} [{r.get('category')}] {r.get('play') or '-'}: "
              f"{r.get('label')}{n}{rr}\n      {r.get('insight')}")


def _csv(v: Optional[str]) -> Optional[list]:
    return [x.strip() for x in v.split(",") if x.strip()] if v else None


def cmd_doctor(_a) -> int:
    problems, notes = [], []
    if not me():
        problems.append("No name set. Run ./onboard.")
    if not (REPO / "company" / "context.md").exists():
        problems.append("company/context.md is missing.")
    elif "DRAFT" in (REPO / "company" / "context.md").read_text()[:400]:
        notes.append("company/context.md still carries the DRAFT banner. Confirm it and delete the banner.")
    for name, _, need in KNOWN_KEYS:
        if need == "must" and not cred(name, required=False):
            problems.append(f"{name} is not set:  python3 gtm.py set-key {name}")
    for name in ("INSTANTLY_API_KEY", "LEMLIST_API_KEY"):
        k = cred(name, required=False)
        if k:
            ok, msg = verify_key(name, k)
            (notes if ok else problems).append(f"{name}: {msg}")
    if not has_db():
        notes.append("No database configured: keys are per laptop and logs go to log/*.jsonl (shared via /save).")
    if subprocess.run(["git", "config", "core.hooksPath"], cwd=REPO, capture_output=True,
                      text=True).stdout.strip() != ".githooks":
        problems.append("Commit guard not installed. Run ./onboard (or: git config core.hooksPath .githooks).")
    for n in notes:
        print(f"  · {n}")
    for p in problems:
        print(f"  ✗ {p}")
    if not problems:
        print("  ✓ nothing blocking")
    return 1 if problems else 0


def cmd_self_update(_a) -> None:
    """The half of an update git can't deliver. Idempotent; safe to run every launch."""
    subprocess.run(["git", "config", "core.hooksPath", ".githooks"], cwd=REPO, capture_output=True)
    if CONFIG_PATH.exists():
        os.chmod(CONFIG_PATH, 0o600)
    for sub in ("plays", "company", "log"):
        (REPO / sub).mkdir(exist_ok=True)


def _flag(msg: str) -> None:
    try:
        flags = json.loads(FLAGS_PATH.read_text())
    except (OSError, ValueError):
        flags = []
    flags.append({"at": datetime.datetime.now().isoformat(timespec="minutes"), "msg": msg})
    FLAGS_PATH.write_text(json.dumps(flags[-20:]))


def cmd_flags(_a) -> None:
    try:
        flags = json.loads(FLAGS_PATH.read_text())
    except (OSError, ValueError):
        return
    for f in flags:
        print(f"  {f['at']}  {f['msg']}")
    FLAGS_PATH.unlink(missing_ok=True)


def cmd_session_end(_a) -> None:
    """SessionEnd hook: if work in plays/ or company/ was never /saved, say so next launch."""
    out = subprocess.run(["git", "status", "--porcelain", "--", "plays", "company", "log"], cwd=REPO,
                         capture_output=True, text=True).stdout
    if out.strip():
        n = len(out.strip().splitlines())
        _flag(f"{n} changed file(s) in plays/ or company/ were not /saved. They are on your "
              f"autosave branch; run /save to share them.")


def main() -> None:
    ap = argparse.ArgumentParser(description="Magna GTM OS helper")
    sp = ap.add_subparsers(dest="cmd", required=True)
    sp.add_parser("whoami").set_defaults(fn=cmd_whoami)
    sp.add_parser("team").set_defaults(fn=cmd_team)
    sp.add_parser("company").set_defaults(fn=cmd_company)
    sp.add_parser("keys").set_defaults(fn=cmd_keys)
    p = sp.add_parser("key"); p.add_argument("name"); p.add_argument("--raw", action="store_true")
    p.set_defaults(fn=cmd_key)
    p = sp.add_parser("set-key"); p.add_argument("name"); p.add_argument("--local", action="store_true")
    p.add_argument("--yes", action="store_true"); p.set_defaults(fn=cmd_set_key)
    p = sp.add_parser("campaigns"); p.add_argument("--platform", choices=["instantly", "lemlist"])
    p.add_argument("--json", action="store_true"); p.set_defaults(fn=cmd_campaigns)
    sp.add_parser("plays").set_defaults(fn=cmd_plays)
    p = sp.add_parser("play"); p.add_argument("slug"); p.set_defaults(fn=cmd_play)
    p = sp.add_parser("new-play"); p.add_argument("slug"); p.add_argument("--title")
    p.set_defaults(fn=cmd_new_play)
    p = sp.add_parser("meetings"); p.add_argument("--limit", type=int, default=5)
    p.set_defaults(fn=cmd_meetings)
    p = sp.add_parser("transcript"); p.add_argument("--date", required=True)
    p.set_defaults(fn=cmd_transcript)
    p = sp.add_parser("log-session")
    for f in ("--summary",):
        p.add_argument(f, required=True)
    for f in ("--who", "--play", "--files", "--skills"):
        p.add_argument(f)
    p.set_defaults(fn=cmd_log_session)
    p = sp.add_parser("log-intel")
    for f in ("--category", "--label", "--insight"):
        p.add_argument(f, required=True)
    for f in ("--who", "--play", "--recommendation", "--confidence"):
        p.add_argument(f)
    p.add_argument("--status", default="observed", choices=["observed", "testing", "proven", "retired"])
    p.add_argument("--sample-size", type=int); p.add_argument("--reply-rate", type=float)
    p.set_defaults(fn=cmd_log_intel)
    p = sp.add_parser("intel"); p.add_argument("--play"); p.add_argument("--category")
    p.set_defaults(fn=cmd_intel)
    sp.add_parser("doctor").set_defaults(fn=cmd_doctor)
    sp.add_parser("self-update").set_defaults(fn=cmd_self_update)
    sp.add_parser("flags").set_defaults(fn=cmd_flags)
    sp.add_parser("session-end").set_defaults(fn=cmd_session_end)
    a = ap.parse_args()
    rc = a.fn(a)
    sys.exit(rc or 0)


if __name__ == "__main__":
    main()
