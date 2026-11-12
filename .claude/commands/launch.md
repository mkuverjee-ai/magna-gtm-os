Build a campaign from a list and copy, and load it into Instantly or Lemlist as a DRAFT.

Request: **$ARGUMENTS**

Usage: `/launch` (ask what to launch) · `/launch <play>` · or just say it in plain words:
"take this list and this copy and make an Instantly campaign".

## Steps

1. **Confirm the three inputs exist.** All three, or stop and say which is missing:
   - **A list:** a CSV in `plays/<slug>/leads/contacts/` with emails (email campaigns) or LinkedIn URLs
     (LinkedIn steps). Dedupe it (`skills/list-dedup`) and check it against live campaigns so nobody
     gets mailed twice.
   - **Copy:** a sequence in `plays/<slug>/campaigns/`. Every merge field it uses must exist as a
     column in the list. Check that, row by row on a sample of 10, before loading.
   - **A sending key:** `python3 gtm.py keys` shows whether `INSTANTLY_API_KEY` / `LEMLIST_API_KEY` is set.

2. **Pick the platform.**
   - Email only → **Instantly** (`skills/instantly`, `skills/instantly-api`)
   - Email plus LinkedIn in one sequence, or LinkedIn only → **Lemlist**
     (`skills/lemlist-campaign-builder`, `skills/linkedin-campaign-complete`, `skills/linkedin-limits-warmup`)
   - Both → one campaign on each, same list split so no one is in both

3. **Show the plan before writing anything:** platform, campaign name, number of leads, steps and
   delays, sending accounts, daily limit, schedule and time zone (the prospects', not yours).
   Ask for a yes.

4. **Create it as a DRAFT.** Nothing sends on its own, ever. Load the leads, set senders and the
   schedule, leave it paused/draft. Every write to Instantly or Lemlist is confirmed first.

5. **Record it.** Add the campaign name and id to `plays/<slug>/PLAY.md` and set its status to
   `draft`.

6. **Hand it back:** tell them to open the campaign in the platform, read every step on a real
   lead, and press go themselves. Activating a campaign from here needs an explicit "launch it live"
   in this conversation, never inferred.

## Rules

- No campaign is created, no lead is uploaded, nothing is activated without a yes in this session.
- Never put an API key in a command argument or a file. Scripts read it via `gtm.cred`.
- A merge field that is empty for a row sends the raw `{{field}}` or a blank. Fix the data or give it
  a fallback before loading.
- Then `/save`, so the team sees the campaign, the list and the copy together.
