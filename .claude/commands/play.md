Load one play (a segment or a campaign) and get oriented.

Play requested: **$ARGUMENTS**

Usage: `/play <name>`, e.g. `/play saudi-banks-fraud`, `/play sea hospitality`. With no name, list the
plays and ask which one. With a name that doesn't exist yet, offer to start it.

## Steps

1. **Company first.** If you have not read `company/context.md` this session, read it now. It holds
   the ICP, positioning, proof points, offers and the message rules every play inherits. If it still
   carries the DRAFT banner, say so: nothing in it has been confirmed by the team yet.

2. **Find the play.** `python3 gtm.py plays` lists them. Match loosely ("sea hospitality" →
   `sea-hospitality-200plus`). Nothing matches → ask whether to start one:
   `python3 gtm.py new-play <slug> --title "..."`, then fill in `PLAY.md` together (segment, offer,
   platform, success bar) before building anything.

3. **Load it.**
   ```
   python3 gtm.py play <slug>
   ```
   Then read `plays/<slug>/PLAY.md` and skim what is in `research/`, `leads/`, `campaigns/`, `reports/`.
   `leads/REGISTER.md` says where every list came from.

4. **Live numbers.** If `PLAY.md` names campaigns, pull them: `python3 gtm.py campaigns`, then the
   detail with the platform skill (`skills/instantly`, `skills/lemlist-reporting`). Report who replied,
   who didn't, which step and variant is working, and bounce rate. Never invent a number the API did
   not return.

5. **What worked before.** `python3 gtm.py intel --play <slug>` and `python3 gtm.py intel` for the
   company-wide log. If a past insight explains what you see, say so instead of re-deriving it.

6. **Recent calls** (only if the team records them): `python3 gtm.py meetings --limit 3`. Look for
   campaign ideas or open action items that touch this play.

7. **Brief, tightly, in this order:**
   - One line: who this play targets and with what offer
   - Where it stands: built / drafted / live / paused, with the numbers
   - Anything that looks wrong (bounce protect, unhealthy sending accounts, zero replies after 300+ sends)
   - What you'd do next, and which skill you'd use for it

8. **Ask what they want to do.** Don't start work unprompted.

## Rules

- Never invent a company fact, proof point or metric. If `company/context.md` doesn't say it, ask.
- Pitch undelivered use cases as capabilities, never as case studies (see company/context.md).
- A play with no `PLAY.md` is a folder, not a play. Write one before building.
