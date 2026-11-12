#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────
# Autosave: snapshot this checkout to your own branch on GitHub.
#
#   scripts/autosave.sh --throttle 300   # from the Stop hook: at most every 5 min
#   scripts/autosave.sh --final          # from the SessionEnd hook
#
# Writes refs/heads/autosave/<name> on origin and nothing else: not main, not the
# working tree, not the index, not their own commits. It builds the snapshot in a
# throwaway index, so a half-staged /save in progress is never disturbed.
# The commit guard runs first; a key or a >25MB file means no autosave (logged).
# Recover:  git fetch origin autosave/<name> && git checkout origin/autosave/<name> -- <path>
# ─────────────────────────────────────────────────────────────
set -u
REPO="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO" || exit 0
LOG="$HOME/.magna-gtm-autosave.log"
STAMP="$HOME/.magna-gtm-autosave-stamp"
log() { echo "$(date '+%Y-%m-%d %H:%M:%S') $*" >> "$LOG"; }

THROTTLE=0; FINAL=0
while [ $# -gt 0 ]; do
  case "$1" in
    --throttle) THROTTLE="${2:-300}"; shift 2 ;;
    --final) FINAL=1; shift ;;
    *) shift ;;
  esac
done

git rev-parse --is-inside-work-tree >/dev/null 2>&1 || exit 0
git remote get-url origin >/dev/null 2>&1 || exit 0   # nowhere to push yet

now=$(date +%s)
if [ "$FINAL" = 0 ] && [ "$THROTTLE" -gt 0 ] && [ -f "$STAMP" ]; then
  last=$(cat "$STAMP" 2>/dev/null || echo 0)
  [ $((now - last)) -lt "$THROTTLE" ] && exit 0
fi
echo "$now" > "$STAMP"

# Nothing uncommitted = nothing to protect.
[ -z "$(git status --porcelain 2>/dev/null)" ] && exit 0

NAME=$(python3 -c "
import json,os,re
try: n=json.load(open(os.path.expanduser('~/.magna-gtm-config'))).get('name') or ''
except Exception: n=''
print(re.sub(r'[^a-z0-9]+','-',n.lower()).strip('-') or 'unknown')" 2>/dev/null)
BRANCH="autosave/$NAME"

TMPIDX=$(mktemp -t magna-autosave-idx) || exit 0
trap 'rm -f "$TMPIDX"' EXIT
export GIT_INDEX_FILE="$TMPIDX"
git read-tree HEAD 2>/dev/null || exit 0
git add -A 2>/dev/null

# Same guard as a real commit: size + leaked keys, against this throwaway index.
if [ -x .githooks/pre-commit ] && ! .githooks/pre-commit >/dev/null 2>&1; then
  log "skipped: commit guard refused the snapshot (a key or a >25MB file). Fix it before /save."
  exit 0
fi

TREE=$(git write-tree) || exit 0
PREV=$(git rev-parse -q --verify "refs/autosave/$NAME" 2>/dev/null || true)
if [ -n "$PREV" ] && [ "$(git rev-parse "$PREV^{tree}")" = "$TREE" ]; then
  exit 0   # identical to the last snapshot
fi

MSG="autosave $(date '+%Y-%m-%d %H:%M') $NAME$( [ "$FINAL" = 1 ] && echo ' (session end)')"
if [ -n "$PREV" ] && git merge-base --is-ancestor HEAD "$PREV" 2>/dev/null; then
  COMMIT=$(git commit-tree "$TREE" -p "$PREV" -m "$MSG") || exit 0
elif [ -n "$PREV" ]; then
  # They committed since the last snapshot: record both, so the branch still fast-forwards.
  COMMIT=$(git commit-tree "$TREE" -p "$PREV" -p HEAD -m "$MSG") || exit 0
else
  COMMIT=$(git commit-tree "$TREE" -p HEAD -m "$MSG") || exit 0
fi
unset GIT_INDEX_FILE
git update-ref "refs/autosave/$NAME" "$COMMIT"

# Push in the background so the session never waits on the network.
(
  if git push -q origin "$COMMIT:refs/heads/$BRANCH" 2>>"$LOG"; then
    log "saved $(git rev-parse --short "$COMMIT") -> $BRANCH"
  else
    log "push failed for $BRANCH (kept locally at refs/autosave/$NAME)"
  fi
) >/dev/null 2>&1 &
exit 0
