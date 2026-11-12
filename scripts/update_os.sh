#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────
# Pull the latest OS into a session that is already running, and say exactly
# what changed and what (if anything) still needs a restart.
#
#   scripts/update_os.sh
#
# Safe mid-session: it autostashes uncommitted work, rebases, restores it.
# ─────────────────────────────────────────────────────────────
set -u
REPO="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO" || exit 1
B='\033[1m'; G='\033[1;32m'; Y='\033[1;33m'; D='\033[90m'; R='\033[0m'

BEFORE=$(git rev-parse HEAD 2>/dev/null) || { echo "Not a git checkout."; exit 1; }
BRANCH=$(git rev-parse --abbrev-ref HEAD)

echo ""
if [ "$BRANCH" != "main" ]; then
  echo -e "  ${Y}!${R} You are on branch '$BRANCH', not main. Pulling anyway."
fi

out=$(git pull --rebase --autostash origin main 2>&1)
if [ $? -ne 0 ]; then
  echo -e "  ${Y}!${R} Could not pull:"
  echo "$out" | tail -3 | sed 's/^/      /'
  echo -e "      Your work is safe. Never force it; sort the conflict first.\n"
  exit 1
fi
AFTER=$(git rev-parse HEAD)

if [ "$BEFORE" = "$AFTER" ]; then
  echo -e "  ${G}✓${R} Already up to date."
  python3 "$REPO/gtm.py" self-update 2>/dev/null
  python3 "$REPO/gtm.py" flags 2>/dev/null
  echo ""
  exit 0
fi

N=$(git rev-list --count "$BEFORE..$AFTER")
echo -e "  ${G}✓${R} Pulled ${B}${N}${R} new commit(s):"
git log --no-merges --format="      %s" "$BEFORE..$AFTER" | cut -c1-96 | head -12
echo ""

FILES=$(git diff --name-only "$BEFORE..$AFTER")
say() { [ -n "$2" ] && { echo -e "  ${B}$1${R}"; echo "$2" | sed 's/^/      /'; }; }

say "Skills changed (re-read the ones you use):" "$(echo "$FILES" | grep '^skills/.*/' | cut -d/ -f1-2 | sort -u)"
say "Slash commands changed (they reload on next use):" "$(echo "$FILES" | grep '^\.claude/commands/' | sed 's#.claude/commands/##;s#\.md$##;s#^#/#')"
say "Tools changed:" "$(echo "$FILES" | grep -E '^[a-z_]+\.py$|^scripts/' | sort -u)"
say "Plays changed:" "$(echo "$FILES" | grep '^plays/' | cut -d/ -f2 | sort -u | tr '\n' ' ')"
say "Company context changed (re-read it):" "$(echo "$FILES" | grep '^company/')"

# The half git cannot deliver: local config, the commit guard.
echo ""
python3 "$REPO/gtm.py" self-update 2>/dev/null
python3 "$REPO/gtm.py" flags 2>/dev/null

# These two only load when a session starts. Everything else is live now.
RESTART=""
echo "$FILES" | grep -q '^CLAUDE.md$' && RESTART="CLAUDE.md (the rules and routing)"
if echo "$FILES" | grep -q '^\.claude/settings.json$'; then
  RESTART="${RESTART:+$RESTART and }settings.json (permissions, autosave hooks)"
fi
echo ""
if [ -n "$RESTART" ]; then
  echo -e "  ${Y}!${R} ${B}$RESTART${R} changed, and that only loads at session start."
  echo -e "      Claude will re-read CLAUDE.md now so the rules apply here, but for the hooks and"
  echo -e "      permissions: type ${B}/exit${R} then ${B}gtm-work${R} (same terminal, no new tab)."
else
  echo -e "  ${G}✓${R} Everything is live in this session. No restart needed."
fi
echo ""
