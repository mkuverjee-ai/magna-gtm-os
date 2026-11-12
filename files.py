#!/usr/bin/env python3
"""
Magna GTM OS: file a lead list or deliverable where the team will find it.

    python3 files.py add <play-slug|company> <file> --type contacts|companies|research|campaign|report \
        --source ai-ark --note "what this list is"
    python3 files.py check [<play-slug>]

`add` COPIES the file to plays/<slug>/<subfolder>/YYYY-MM-DD-<name>.<ext> and, for a lead
list, appends a row to leads/REGISTER.md (date, file, rows, source, who, why). A list with
no provenance is close to useless to whoever picks the play up next.

`check` lists deliverables sitting outside plays/ and company/, files over the 25MB commit
limit, and lead CSVs missing from their play's register.
"""
from __future__ import annotations

import argparse
import csv
import datetime
import re
import shutil
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent
sys.path.insert(0, str(REPO))
import gtm  # noqa: E402

SUB = {"contacts": "leads/contacts", "companies": "leads/companies", "research": "research",
       "campaign": "campaigns", "report": "reports"}
DELIVERABLE = {".csv", ".xlsx", ".xls", ".tsv", ".pdf", ".docx", ".pptx", ".html"}
MAX = 25 * 1024 * 1024


def root_for(target: str) -> Path:
    if target == "company":
        return REPO / "company"
    p = REPO / "plays" / target
    if not p.is_dir():
        sys.exit(f"No play '{target}'. Create it: python3 gtm.py new-play {target}")
    return p


def rows(p: Path) -> int:
    if p.suffix.lower() != ".csv":
        return 0
    with p.open(newline="", encoding="utf-8-sig", errors="replace") as fh:
        return max(sum(1 for _ in csv.reader(fh)) - 1, 0)   # csv, never wc -l: quoted newlines


def cmd_add(a) -> None:
    src = Path(a.file).expanduser()
    if not src.is_file():
        sys.exit(f"No file at {src}")
    root = root_for(a.target)
    today = datetime.date.today().isoformat()
    stem = re.sub(r"[^a-z0-9]+", "-", src.stem.lower()).strip("-")
    if not re.match(r"\d{4}-\d{2}-\d{2}", stem):
        stem = f"{today}-{stem}"
    dst = root / SUB[a.type] / f"{stem}{src.suffix.lower()}"
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.exists():
        sys.exit(f"{dst.relative_to(REPO)} already exists. Rename the source or remove the old one first.")
    shutil.copy2(src, dst)
    n = rows(dst)
    print(f"  filed {dst.relative_to(REPO)}" + (f" ({n:,} rows)" if n else ""))
    if a.type in ("contacts", "companies"):
        reg = root / "leads" / "REGISTER.md"
        if not reg.exists():
            reg.write_text("# Lead register\n\nEvery list in this play, where it came from, and why.\n\n"
                           "| Date | File | Type | Rows | Source | Added by | Note |\n|---|---|---|---|---|---|---|\n")
        with reg.open("a") as fh:
            fh.write(f"| {today} | `{dst.relative_to(root)}` | {a.type} | {n or '-'} | {a.source or '-'} | "
                     f"{gtm.me() or '-'} | {a.note or ''} |\n")
        print(f"  logged in {reg.relative_to(REPO)}")
    if dst.stat().st_size > MAX:
        print("  ! over 25MB: the commit guard will block it. Trim it (dedupe, drop raw columns) first.")


def cmd_check(a) -> None:
    out = subprocess.run(["git", "status", "--porcelain", "-uall", "--ignored"], cwd=REPO,
                         capture_output=True, text=True).stdout
    paths = [l[3:].strip().strip('"') for l in out.splitlines() if l.strip()]
    loose = [p for p in paths if Path(p).suffix.lower() in DELIVERABLE
             and not p.startswith(("plays/", "company/", "skills/", ".import/"))]
    for p in loose:
        print(f"  outside plays/ and company/: {p}")
    plays = [REPO / "plays" / a.slug] if a.slug else [p for p in (REPO / "plays").glob("*") if p.is_dir()]
    for play in plays:
        reg = play / "leads" / "REGISTER.md"
        listed = reg.read_text() if reg.exists() else ""
        for f in sorted((play / "leads").rglob("*.csv")) if (play / "leads").exists() else []:
            if f.stat().st_size > MAX:
                print(f"  over 25MB: {f.relative_to(REPO)}")
            if f.name not in listed:
                print(f"  not in {play.name}'s REGISTER.md: {f.relative_to(REPO)}")
    if not loose:
        print("  nothing stranded")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = ap.add_subparsers(dest="cmd", required=True)
    p = sp.add_parser("add")
    p.add_argument("target"); p.add_argument("file")
    p.add_argument("--type", required=True, choices=sorted(SUB))
    p.add_argument("--source"); p.add_argument("--note")
    p.set_defaults(fn=cmd_add)
    p = sp.add_parser("check"); p.add_argument("slug", nargs="?"); p.set_defaults(fn=cmd_check)
    a = ap.parse_args()
    a.fn(a)


if __name__ == "__main__":
    main()
