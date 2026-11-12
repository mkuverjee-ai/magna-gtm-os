#!/usr/bin/env python3
"""
Magna GTM OS: pull scattered files off this laptop into company/ or a play folder.

    python3 import_files.py scan  [--also "other name,brand"] [--path ~/Desktop/x]
    python3 import_files.py apply --into company --pick 1,3,5-7 [--dry-run]
    python3 import_files.py apply --into <play-slug> --all

`scan` searches the laptop (Spotlight, plus a direct walk of Google Drive / Dropbox /
OneDrive folders, which Spotlight often does not index) for folders and files whose NAME
matches the company's names (company/import-terms.txt, plus --also), and prints numbered candidates. Nothing is
touched. The plan is saved to .import/scan.json (gitignored).

`apply` COPIES the picked candidates into the standard subfolders (leads/contacts,
leads/companies, research, campaigns, reports, transcripts, assets). Originals are never
moved or deleted. Skipped, with a reason: secrets and .env files, anything that looks like
it holds an API key, files over 25MB (the commit guard's limit), code (unless
--include-code), caches and exact duplicates of a file already in the destination. Lead
CSVs are logged in leads/REGISTER.md; everything lands in IMPORT-LOG.md.
"""

from __future__ import annotations

import argparse
import csv
import datetime
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent
TERMS_FILE = REPO / "company" / "import-terms.txt"
DEFAULT_TERMS = ["magna ai", "magnaai", "magnaverse", "magna forge"]
PLANS = REPO / ".import"
HOME = Path.home()
MAX_BYTES = 25 * 1024 * 1024
sys.path.insert(0, str(REPO))

# Never walk into these, anywhere.
SKIP_DIRS = {".git", "node_modules", ".venv", "venv", "__pycache__", ".next", "site-packages",
             ".cache", ".Trash", "dist", "build", ".idea", ".pytest_cache", ".mypy_cache"}
SKIP_PREFIXES = [HOME / "Library", HOME / ".Trash", HOME / ".claude", HOME / ".local",
                 HOME / ".npm", HOME / ".cache", HOME / "Movies", HOME / "Music", HOME / "Pictures",
                 Path("/Applications")]
CLOUD_ROOT = HOME / "Library" / "CloudStorage"      # Google Drive, Dropbox, OneDrive, Box

SECRET_NAMES = re.compile(r"(^\.env|\.env$|credentials|secret|token|\.pem$|\.p12$|\.key$|id_rsa|"
                          r"keys?\.(txt|json|env)$|service[-_]?account)", re.I)
# Same families the commit guard blocks (built from parts so this file doesn't trip it).
_P = ["sk" + "-ant-[A-Za-z0-9_-]{20,}", "xox" + "[abp]-[0-9A-Za-z-]{20,}", "pat-" + "na[0-9]-[a-f0-9-]{30,}",
      "sb_" + "secret_[A-Za-z0-9_-]{20,}", "gh" + "p_[A-Za-z0-9]{30,}", "AKIA" + "[0-9A-Z]{16}",
      "ey" + "J[A-Za-z0-9_-]{20,}\\.ey" + "J[A-Za-z0-9_-]{20,}"]
KEY_RE = re.compile("|".join(_P))

CODE_EXT = {".py", ".js", ".ts", ".tsx", ".jsx", ".sh", ".ipynb", ".sql", ".rb", ".go"}
DOC_EXT = {".pdf", ".docx", ".doc", ".pptx", ".md", ".txt", ".rtf", ".html"}
SHEET_EXT = {".csv", ".xlsx", ".xls", ".tsv"}
IMG_EXT = {".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp"}
IGNORE_EXT = {".pyc", ".log", ".tmp", ".lock", ".ds_store", ".jsonl", ".db", ".sqlite",
              ".sqlite3", ".zip", ".gz", ".tar", ".dmg", ".pkg", ".app", ".key", ".pages",
              ".numbers", ".mp4", ".mov", ".mp3", ".wav"}

KW = [  # checked in order against the file's path, lowercase
    ("transcripts", r"transcript|fireflies|call[-_ ]|meeting|recap|kickoff|kick-off|check-in|sync"),
    ("reports", r"report|analytic|performance|results|dashboard|stats"),
    ("campaigns", r"campaign|sequence|copy|email[-_ ]|outreach|playbook|cadence|script|brief"),
    ("research", r"icp|tam|research|matrix|persona|competitor|segment|tier|scoring|market|signal"),
]


# ── helpers ────────────────────────────────────────────────────────────────

def slugify(s: str) -> str:
    s = re.sub(r"[^a-zA-Z0-9.]+", "-", s).strip("-").lower()
    return re.sub(r"-+", "-", s)


def human(n: float) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024:
            return f"{n:.0f}{unit}"
        n /= 1024
    return f"{n:.0f}TB"


def sha1(p: Path) -> str:
    h = hashlib.sha1()
    with p.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def skipped_path(p: Path) -> bool:
    if any(part in SKIP_DIRS for part in p.parts):
        return True
    for pre in SKIP_PREFIXES:
        if pre == HOME / "Library" and str(p).startswith(str(CLOUD_ROOT)):
            continue
        if str(p).startswith(str(pre) + os.sep) or p == pre:
            return True
    return False


def inside_gtm_os(p: Path) -> bool:
    """Any clone of this repo (the live one or an old copy) is not a source."""
    for parent in [p] + list(p.parents):
        if (parent / "import_files.py").exists() and (parent / "gtm.py").exists():
            return True
        if parent == HOME:
            break
    return False


def search_terms(extra: list[str]) -> list[str]:
    """company/import-terms.txt (one per line) if present, else the defaults, plus --also."""
    terms = set(DEFAULT_TERMS)
    if TERMS_FILE.exists():
        terms = {l.strip().lower() for l in TERMS_FILE.read_text().splitlines()
                 if l.strip() and not l.startswith("#")}
    terms |= {t.strip().lower() for t in extra if t.strip()}
    # Very short terms match half the laptop. A bare "magna" is too common to search on.
    return sorted(t for t in terms if len(t) >= 4)


WEAK: set[str] = set()   # terms that are just the first word of a multi-word name


def strong_match(name: str, terms: list[str]) -> bool:
    return name_matches(name, [t for t in terms if t not in WEAK])


def name_matches(name: str, terms: list[str]) -> bool:
    low = name.lower()
    flat = re.sub(r"[^a-z0-9]", "", low)
    for t in terms:
        tf = re.sub(r"[^a-z0-9]", "", t)
        if re.search(r"(^|[^a-z0-9])" + re.escape(t) + r"($|[^a-z0-9])", low) or (len(tf) >= 6 and tf in flat):
            return True
    return False


# ── discovery ──────────────────────────────────────────────────────────────

def spotlight(terms: list[str]) -> set[Path]:
    hits: set[Path] = set()
    for t in terms:
        try:
            out = subprocess.run(["mdfind", "-onlyin", str(HOME), "-name", t],
                                 capture_output=True, text=True, timeout=60).stdout
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return hits
        hits |= {Path(l) for l in out.splitlines() if l.strip()}
    return hits


def walk(roots: list[Path], terms: list[str], max_depth: int = 6) -> set[Path]:
    hits: set[Path] = set()
    for root in roots:
        if not root.exists():
            continue
        base = len(root.parts)
        for dirpath, dirnames, filenames in os.walk(root):
            d = Path(dirpath)
            dirnames[:] = [x for x in dirnames if x not in SKIP_DIRS and not x.startswith(".")]
            if len(d.parts) - base >= max_depth:
                dirnames[:] = []
            for n in dirnames + filenames:
                if name_matches(n, terms):
                    hits.add(d / n)
    return hits


def collect(folder: Path) -> list[Path]:
    out = []
    for dirpath, dirnames, filenames in os.walk(folder):
        dirnames[:] = [x for x in dirnames if x not in SKIP_DIRS and not x.startswith(".")]
        for f in filenames:
            if not f.startswith("."):
                out.append(Path(dirpath) / f)
    return out


def scan(extra: list[str], paths: list[str]) -> dict:
    terms = search_terms(extra)
    found = spotlight(terms)
    cloud = [p for p in CLOUD_ROOT.iterdir()] if CLOUD_ROOT.exists() else []
    found |= walk(cloud, terms)
    # Spotlight can be off on some laptops: always walk the usual places too.
    found |= walk([HOME / "Desktop", HOME / "Documents", HOME / "Downloads"], terms, max_depth=5)
    found = {p for p in found if p.exists() and not skipped_path(p) and not inside_gtm_os(p)
             and name_matches(p.name, terms)}
    for p in paths:
        pp = Path(p).expanduser().resolve()
        if pp.exists():
            found.add(pp)

    # A matched folder swallows everything matched inside it.
    folders = sorted([p for p in found if p.is_dir()], key=lambda p: len(p.parts))
    top: list[Path] = []
    for f in folders:
        if not any(str(f).startswith(str(t) + os.sep) for t in top):
            top.append(f)
    loose = sorted(p for p in found if p.is_file() and not any(str(p).startswith(str(t) + os.sep) for t in top))

    cands = []
    for f in top:
        files = [x for x in collect(f) if not skipped_path(x)]
        if not files:
            continue
        size = sum(x.stat().st_size for x in files if x.exists())
        kinds: dict[str, int] = {}
        for x in files:
            kinds[x.suffix.lower() or "(none)"] = kinds.get(x.suffix.lower() or "(none)", 0) + 1
        newest = max((x.stat().st_mtime for x in files if x.exists()), default=0)
        cands.append({"path": str(f), "kind": "folder", "files": len(files), "bytes": size,
                      "types": dict(sorted(kinds.items(), key=lambda kv: -kv[1])[:6]),
                      "modified": datetime.date.fromtimestamp(newest).isoformat() if newest else ""})
    for f in loose:
        if f.suffix.lower() in IGNORE_EXT:
            continue
        st = f.stat()
        cands.append({"path": str(f), "kind": "file", "files": 1, "bytes": st.st_size,
                      "types": {f.suffix.lower(): 1},
                      "modified": datetime.date.fromtimestamp(st.st_mtime).isoformat()})
    # Strong matches (full name, slug, domain) first; first-word-only matches after, flagged.
    for cnd in cands:
        cnd["weak"] = not strong_match(Path(cnd["path"]).name, terms)
    cands.sort(key=lambda c: c["weak"])
    for i, cnd in enumerate(cands, 1):
        cnd["n"] = i
    plan = {"terms": terms, "weak_terms": sorted(WEAK),
            "candidates": cands,
            "scanned_at": datetime.datetime.now().isoformat(timespec="seconds")}
    PLANS.mkdir(exist_ok=True)
    (PLANS / "scan.json").write_text(json.dumps(plan, indent=2))
    return plan


# ── classification ─────────────────────────────────────────────────────────

ACTIVITY_RE = re.compile(r"send|repl|activit|event|timeline|log|created|skipped|existed|verify|"
                         r"match|bounce|open|click|unsub|analytic|stats|report", re.I)
LIST_RE = re.compile(r"lead|contact|compan|account|prospect|list|tam|tal|target|people", re.I)


def csv_kind(p: Path) -> str:
    # Activity exports (sends, replies, HubSpot push results) carry emails too, but they are
    # a record of what happened, not a list to work. They go to reports/, off the register.
    if ACTIVITY_RE.search(p.stem) and not LIST_RE.search(p.stem):
        return "reports"
    try:
        with p.open(newline="", encoding="utf-8-sig", errors="replace") as fh:
            header = [h.strip().lower() for h in next(csv.reader(fh), [])]
    except OSError:
        return "research"
    h = " ".join(header)
    person = any(k in h for k in ("email", "first name", "first_name", "firstname", "last name",
                                  "full name", "title", "person linkedin"))
    company = any(k in h for k in ("domain", "website", "company", "industry", "employees"))
    if person:
        return "leads/contacts"
    if company:
        return "leads/companies"
    return "reports" if re.search(KW[1][1], p.name.lower()) else "research"


def destination(p: Path, rel: str, include_code: bool) -> tuple[str | None, str]:
    ext = p.suffix.lower()
    low = rel.lower()
    if ext in IGNORE_EXT:
        return None, "ignored type"
    if SECRET_NAMES.search(p.name):
        return None, "looks like a secret / credentials file"
    if ext in CODE_EXT:
        return ("tools", "") if include_code else (None, "code (use --include-code)")
    if ext in (".csv", ".tsv"):
        return csv_kind(p), ""
    if ext in (".xlsx", ".xls"):
        # Only research/ keeps spreadsheets in git (.gitignore); lead xlsx lands there too.
        return "research", ""
    if ext in IMG_EXT:
        return "assets", ""
    if ext == ".md" and re.match(r"(status|context|readme|notes?|overview|handover)$", p.stem, re.I):
        return ".", ""
    if ext in DOC_EXT or ext == ".json":
        if ext == ".json" and not re.search(r"icp|config|plan|brief", low):
            return None, "json data dump"
        for folder, rx in KW:
            if re.search(rx, low):
                return folder, ""
        return "assets", ""
    return None, f"unhandled type {ext or '(none)'}"


def has_key(p: Path) -> bool:
    if p.suffix.lower() not in {".txt", ".md", ".csv", ".json", ".py", ".js", ".ts", ".sh", ".env",
                                ".tsv", ".sql", ".yaml", ".yml", ".toml", ".ipynb"}:
        return False
    try:
        with p.open("r", errors="ignore") as fh:
            return bool(KEY_RE.search(fh.read(2_000_000)))
    except OSError:
        return False


# ── apply ──────────────────────────────────────────────────────────────────

def parse_pick(s: str, n: int) -> list[int]:
    out: set[int] = set()
    for part in s.split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            a, b = part.split("-", 1)
            out |= set(range(int(a), int(b) + 1))
        else:
            out.add(int(part))
    bad = [x for x in out if x < 1 or x > n]
    if bad:
        sys.exit(f"No candidate(s) {bad}; the scan found 1-{n}.")
    return sorted(out)


def dest_for(into: str) -> Path:
    """company -> company/, anything else -> plays/<slug>/ (created from the template)."""
    if into == "company":
        return REPO / "company"
    root = REPO / "plays" / into
    if not root.exists():
        import gtm
        gtm.cmd_new_play(argparse.Namespace(slug=into, title=None))
    return root


def apply(into: str, pick: list[int] | None, dry: bool, include_code: bool, by: str) -> None:
    pf = PLANS / "scan.json"
    if not pf.exists():
        sys.exit("No scan yet. Run: python3 import_files.py scan")
    plan = json.loads(pf.read_text())
    cands = plan["candidates"]
    chosen = [c for c in cands if pick is None or c["n"] in pick]
    dest_root = dest_for(into)
    where = dest_root.relative_to(REPO)

    existing = {}
    for x in collect(dest_root):
        try:
            existing[sha1(x)] = x
        except OSError:
            pass

    today = datetime.date.today().isoformat()
    copied, skipped, dupes = [], [], []
    planned: set[Path] = set()
    for cnd in chosen:
        src = Path(cnd["path"])
        files = collect(src) if cnd["kind"] == "folder" else [src]
        for f in files:
            if skipped_path(f) or not f.exists():
                continue
            rel = str(f.relative_to(src.parent)) if cnd["kind"] == "folder" else f.name
            sub, why = destination(f, rel, include_code)
            if not sub:
                skipped.append((f, why))
                continue
            size = f.stat().st_size
            if size > MAX_BYTES:
                skipped.append((f, f"{human(size)}, over the 25MB commit limit (left where it is)"))
                continue
            if has_key(f):
                skipped.append((f, "contains something that looks like an API key"))
                continue
            digest = sha1(f)
            if digest in existing:
                dupes.append((f, existing[digest]))
                continue
            stem = slugify(f.stem)
            if sub == ".":
                stem = f"imported-{stem}"
            # Keep the folders inside the matched folder (lemlist-2026-09-16/replies.csv says
            # far more than replies.csv), minus noise segments like data/ or exports/.
            inner = []
            if cnd["kind"] == "folder":
                inner = [slugify(x) for x in f.relative_to(src).parent.parts
                         if slugify(x) not in ("data", "exports", "export", "files", "")]
            target = dest_root / sub / Path(*inner) / (stem + f.suffix.lower()) if inner \
                else dest_root / sub / (stem + f.suffix.lower())
            k = 2
            while target.exists() or target in planned:
                target = target.with_name(f"{stem}-{k}{f.suffix.lower()}")
                k += 1
            planned.add(target)
            if not dry:
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(f, target)
            existing[digest] = target
            copied.append((f, target, sub, size))

    word = "Would copy" if dry else "Copied"
    print(f"\n  {word} {len(copied)} files into {where}/")
    by_sub: dict[str, int] = {}
    for _, _, sub, _ in copied:
        by_sub[sub] = by_sub.get(sub, 0) + 1
    for sub, n in sorted(by_sub.items()):
        print(f"    {('(folder root)' if sub == '.' else sub):18s} {n}")
    if dupes:
        print(f"  Identical copies skipped (already in the folder, or the same file twice): {len(dupes)}")
    if skipped:
        print(f"  Skipped: {len(skipped)}")
        reasons: dict[str, int] = {}
        for _, why in skipped:
            key = why.split(",")[0] if "MB" not in why else "over 25MB"
            reasons[key] = reasons.get(key, 0) + 1
        for why, n in sorted(reasons.items(), key=lambda kv: -kv[1]):
            print(f"    {n:4d}  {why}")
        big = [(f, w) for f, w in skipped if "MB" in w]
        for f, w in big[:5]:
            print(f"          {f}  ({w.split(',')[0]})")
    if dry:
        for f, t, _, _ in copied[:40]:
            print(f"    {str(f)[-70:]:70s} -> {t.relative_to(REPO)}")
        if len(copied) > 40:
            print(f"    ... {len(copied) - 40} more")
        print("\n  Dry run: nothing written.")
        return
    if not copied:
        return

    # Provenance: lead lists in the register, everything in the import log.
    leads = [(f, t) for f, t, sub, _ in copied if sub.startswith("leads/") and t.suffix == ".csv"]
    if leads:
        reg = dest_root / "leads" / "REGISTER.md"
        if not reg.exists():
            reg.parent.mkdir(parents=True, exist_ok=True)
            reg.write_text("# Lead register\n\nEvery list added here, where it came from, and why.\n\n"
                           "| Date | File | Type | Rows | Source | Added by | Note |\n"
                           "|---|---|---|---|---|---|---|\n")
        with reg.open("a") as fh:
            for f, t in leads:
                try:
                    with t.open(newline="", encoding="utf-8-sig", errors="replace") as c:
                        rows = max(sum(1 for _ in csv.reader(c)) - 1, 0)
                except OSError:
                    rows = 0
                kind = "contacts" if "contacts" in str(t) else "companies"
                fh.write(f"| {today} | `{t.relative_to(dest_root)}` | {kind} | {rows or '—'} | "
                         f"imported | {by or '—'} | from `{str(f).replace(str(HOME), '~')}` |\n")
    log = dest_root / "IMPORT-LOG.md"
    new = not log.exists()
    with log.open("a") as fh:
        if new:
            fh.write("# Import log\n\nFiles pulled into this folder from teammates' laptops by "
                     "`import_files.py`. Originals were copied, not moved.\n")
        fh.write(f"\n## {today}, by {by or 'unknown'}\n\n")
        for f, t, _, size in copied:
            fh.write(f"- `{t.relative_to(dest_root)}` ← `{str(f).replace(str(HOME), '~')}` ({human(size)})\n")
        if skipped:
            fh.write(f"\nLeft behind: {len(skipped)} files (secrets, code, >25MB, dumps).\n")
    try:
        import gtm
        gtm._log("sessions", {"who": by or None, "play": None if into == "company" else into,
                              "summary": f"/import: copied {len(copied)} file(s) from a laptop into {where}/",
                              "files": [str(t.relative_to(REPO)) for _, t, _, _ in copied][:200]})
    except SystemExit:
        pass
    print(f"\n  Logged in {where}/IMPORT-LOG.md" + (" and leads/REGISTER.md" if leads else "")
          + ", and in the session log")
    print("  Originals are untouched. Review, then /save to share it with the team.\n")


# ── CLI ────────────────────────────────────────────────────────────────────

def print_plan(plan: dict) -> None:
    cands = plan["candidates"]
    print(f"\n  Searched for: {', '.join(plan['terms'])}")
    if not cands:
        print("  Nothing found. Add terms with --also, or point at a folder with --path.\n")
        return
    print(f"  {len(cands)} candidates. Nothing has been copied.\n")
    shown_weak = False
    for c in cands:
        if c.get("weak") and not shown_weak:
            shown_weak = True
            print(f"\n  Weaker matches: only the word {', '.join(repr(w) for w in plan.get('weak_terms', []))}"
                  " matched. Often unrelated; check before picking.\n")
        p = c["path"].replace(str(HOME), "~")
        types = " ".join(f"{k}×{v}" for k, v in c["types"].items())
        tag = "DIR " if c["kind"] == "folder" else "FILE"
        print(f"  {c['n']:3d}  {tag} {p}")
        print(f"        {c['files']} file(s), {human(c['bytes'])}, newest {c['modified']}   {types}")
    print("\n  Next: python3 import_files.py apply --into company|<play-slug> --pick 1,3-5 --dry-run\n")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("scan")
    s.add_argument("--also", default="", help="extra search terms, comma-separated")
    s.add_argument("--path", action="append", default=[], help="a folder to include explicitly")
    s = sub.add_parser("apply")
    s.add_argument("--into", required=True, help="company, or a play slug")
    g = s.add_mutually_exclusive_group(required=True)
    g.add_argument("--pick")
    g.add_argument("--all", action="store_true")
    s.add_argument("--dry-run", action="store_true")
    s.add_argument("--include-code", action="store_true")
    s.add_argument("--by", default="")
    a = ap.parse_args()

    if a.cmd == "scan":
        print_plan(scan(a.also.split(","), a.path))
    else:
        import gtm
        pf = PLANS / "scan.json"
        n = len(json.loads(pf.read_text())["candidates"]) if pf.exists() else 0
        by = a.by or gtm.me()
        apply(a.into, None if a.all else parse_pick(a.pick, n), a.dry_run, a.include_code, by)


if __name__ == "__main__":
    main()
