# Setting up the Magna GTM OS

About ten minutes the first time, two minutes for each new teammate after that. If you would rather
not read this: open Claude Code in an empty folder, drop this file in, and say *"set me up"*.
Claude will walk you through every step and stop where it needs you.

---

## Part 1: once, for the whole team (whoever owns the OS)

### 1. Get the repo

The repo lives on GitHub as a private repository. Ask for it to be **transferred to your company's
GitHub organisation** (Settings → Transfer), or accept the collaborator invite. Then invite each
teammate to it. Clone URLs below use `<org>/magna-gtm-os`: substitute wherever it lives.

### 2. Decide: shared database, or not

| | With a database (recommended) | Without |
|---|---|---|
| API keys | set once, everyone has them | each person sets their own |
| Session + what-worked logs | queryable table | files in `log/`, shared by `/save` |
| Setup | ~5 minutes | nothing |

**With one:** create a free Supabase project, open the SQL editor, paste `db/schema.sql`, run it.
Keep the project URL and the `service_role` key (Settings → API). Optionally create a `team.env`
in the repo folder (it is gitignored) and send it to teammates privately, so `./onboard` fills
itself in:

```
MAGNA_DB_URL=https://<project>.supabase.co
MAGNA_DB_KEY=<service_role key>
```

Then add your team to the `team` table (name, email) so `./onboard` can offer a pick-list.

### 3. Add the tool keys (once)

```bash
python3 gtm.py set-key INSTANTLY_API_KEY     # paste, Enter, Ctrl-D
python3 gtm.py set-key LEMLIST_API_KEY
python3 gtm.py set-key AI_ARK_API_KEY
echo -n salesforce | python3 gtm.py set-key CRM_PROVIDER --yes    # or hubspot
python3 gtm.py set-key CRM_API_KEY           # HubSpot private-app token or Salesforce access token
python3 gtm.py set-key CRM_INSTANCE_URL      # Salesforce only
python3 gtm.py keys                          # shows what is present and missing
```

Instantly and Lemlist keys are checked live before they are saved. Optional keys are listed in
`TECH-STACK.md`. With a database, these reach everyone immediately; without one, each person
repeats this step.

### 4. Fill in the company context

`company/context.md` is a blank template: ICP, positioning, proof points, offers, message rules.
Run `/import` to bring your decks, use-case documents and one-pagers into `company/`, ask Claude to
draft the context from them, correct it, and delete the DRAFT banner. Every play reads this file
before any copy is written, so it is the highest-leverage ten minutes in the setup.

---

## Part 2: each teammate

```bash
npm install -g @anthropic-ai/claude-code     # if you don't have Claude Code
brew install gh && gh auth login             # choose HTTPS when it asks

gh repo clone <org>/magna-gtm-os
cd magna-gtm-os
./onboard
```

`./onboard` checks prerequisites, connects to the team database if there is one, asks who you are,
puts `gtm-work` on your PATH, installs the commit guard, and shows which keys are present. It is
safe to re-run.

Use `gh repo clone`, not an SSH URL: SSH only works if you have added a key to GitHub.

From then on, start every session with:

```bash
gtm-work
```

## Optional

- **Miro:** inside Claude Code, type `/mcp`, pick `miro`, sign in once.
- **Clay CLI:** `claude plugin marketplace add clay-run/agent-plugins`, then `! clay login`.
- **Call transcripts:** if the team records calls (Fireflies, Granola), add `FIREFLIES_API_KEY` and
  see `skills/fireflies-usage`. Confidential calls can be stored summary-only.

## If something goes wrong

| Symptom | Fix |
|---|---|
| `CERTIFICATE_VERIFY_FAILED` | `python3 -m pip install --user --upgrade certifi` |
| `/save` can't push | `gh auth login` (HTTPS), then re-clone with `gh repo clone` |
| "Missing credential: X" | `python3 gtm.py set-key X` |
| AI Ark `TLSV1_ALERT_PROTOCOL_VERSION` | not a bad key: macOS system Python. `aiark.py` uses curl for this; use it instead of raw Python |
| Anything else | `python3 gtm.py doctor` names what is missing |
