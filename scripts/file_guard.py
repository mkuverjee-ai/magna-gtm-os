#!/usr/bin/env python3
"""Keep deliverables inside plays/<slug>/ or company/, as they are written, not at /save.

Claude Code hooks (stdin = hook JSON):
  file_guard.py --post-tool   after Write/Edit: a CSV/XLSX/PDF/DOCX/PPTX/HTML written outside
                              plays/ or company/ -> exit 2, which tells Claude to file it now
  file_guard.py --stop        when Claude finishes a turn: such files sitting in the repo but
                              outside plays/ and company/ (e.g. made by a Python script) -> exit 2, once

Each path is raised once (~/.magna-gtm-guard-seen), so scratch files don't nag forever.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
EXT = {".csv", ".xlsx", ".xls", ".tsv", ".pdf", ".docx", ".pptx", ".html"}
SEEN = Path.home() / ".magna-gtm-guard-seen"
FIX = ("File it now: python3 files.py add <play-slug|company> <file> "
       "--type contacts|companies|research|campaign|report --source <where it came from> "
       "--note \"what it is\". If it is throwaway scratch, say so and carry on.")


def seen() -> set:
    try:
        return set(SEEN.read_text().splitlines())
    except OSError:
        return set()


def remember(paths: list[str]) -> None:
    s = seen() | set(paths)
    SEEN.write_text("\n".join(sorted(s)[-2000:]))


def outside_work(p: Path) -> bool:
    try:
        rel = p.resolve().relative_to(REPO)
    except ValueError:
        return True                      # outside the repo entirely: /tmp, Downloads...
    return not str(rel).startswith(("plays/", "company/"))


def main() -> None:
    mode = sys.argv[1] if len(sys.argv) > 1 else ""
    try:
        data = json.loads(sys.stdin.read() or "{}")
    except ValueError:
        data = {}

    if mode == "--post-tool":
        ti = data.get("tool_input") or {}
        fp = ti.get("file_path") or ti.get("notebook_path")
        if not fp:
            return
        p = Path(fp)
        if p.suffix.lower() not in EXT or not outside_work(p) or str(p) in seen():
            return
        remember([str(p)])
        print(f"GTM OS: {p} is a deliverable outside plays/ and company/. {FIX}", file=sys.stderr)
        sys.exit(2)

    if mode == "--stop":
        if data.get("stop_hook_active"):
            return                       # already reminded this turn; never loop
        # --ignored matters: .gitignore hides CSVs outside plays/, which is exactly the
        # stranded case — plain `git status` never lists them.
        out = subprocess.run(["git", "status", "--porcelain", "-uall", "--ignored"], cwd=REPO,
                             capture_output=True, text=True).stdout
        paths = [l[3:].strip().strip('"') for l in out.splitlines() if l.strip()]
        skip = (".import/", ".venv/", "node_modules/", ".git/", "skills/")
        loose = [p for p in paths if not p.startswith(("plays/", "company/")) and not p.startswith(skip)
                 and Path(p).suffix.lower() in EXT and str(REPO / p) not in seen()]
        if not loose:
            return
        remember([str(REPO / p) for p in loose])
        print("GTM OS: these files are in the repo but outside plays/ and company/, so they won't reach "
              f"the team: {', '.join(loose[:6])}. {FIX}", file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
