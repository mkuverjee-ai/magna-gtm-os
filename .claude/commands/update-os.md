Pull the latest OS and your team's work into this session, without restarting.

## Steps

1. **Pull and report:**
   ```
   bash scripts/update_os.sh
   ```
   It rebases onto the latest (autostashing anything uncommitted), runs `gtm.py self-update`, and
   lists what changed: skills, commands, tools, plays, company context.

2. **Re-read what changed:**
   - `CLAUDE.md` changed → read it now (it only auto-loads at session start) and say in one line what
     changed in how you work.
   - `company/context.md` changed → re-read it before writing any copy.
   - A skill you are using changed → re-read its `SKILL.md`.
   - Slash commands and tools reload on their own.

3. **Say plainly what is not live:** `.claude/settings.json` (permissions and the autosave hooks)
   loads only at startup. If it changed, tell them to type `/exit` then `gtm-work`.

4. **If the pull failed** (a conflict with their own uncommitted work), leave it alone and say so.
   Never force, never discard their changes.
