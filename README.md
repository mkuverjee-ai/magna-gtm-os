# Magna GTM OS

Magna AI's outbound, run from Claude Code. Build the list, find the trigger, sharpen the offer,
write the sequence, load it into Instantly or Lemlist, work the replies and read the numbers,
without leaving the terminal. Everything one person builds is there for the next person on their
next launch.

**New here? Read [SETUP.md](SETUP.md)**, or drop it into Claude Code and say "set me up".

## Daily

```bash
gtm-work
```

It pulls the latest OS and your team's work, checks your setup, loads the company context and
what is live in Instantly and Lemlist, and opens Claude Code already knowing all of it.

| Command | What it does |
|---|---|
| `/play <name>` | Load one segment or campaign: context, live numbers, what worked before |
| `/status` | Every campaign, problems first (bounce protect, unhealthy accounts, unanswered replies) |
| `/launch` | Take a list and copy, build the campaign in Instantly or Lemlist, as a draft |
| `/report` | Live numbers for one campaign, one play, or all of them |
| `/import` | Find your scattered lists and decks on this laptop and file them in the repo |
| `/update-os` | Pull the latest OS without restarting |
| `/save` | Commit, push, and log the session so a teammate can pick it up |

Or just ask in plain words: *"find me CISOs at Saudi banks with an active AI initiative"*,
*"pull the two campaign ideas out of this call and draft copy"*, *"what did the SEA campaign do this week?"*

## Layout

```
magna-gtm-os/
├── CLAUDE.md          how Claude works in this repo (loaded automatically)
├── SETUP.md           onboarding, for a new teammate
├── TECH-STACK.md      what to subscribe to, what's optional, alternatives
├── gtm-work           the session launcher
├── onboard            one-time setup
├── gtm.py             keys, plays, live campaigns, calls, the what-worked log
├── files.py           file a list or deliverable with its provenance
├── import_files.py    pull files off a laptop into the repo
├── company/           context.md (ICP, positioning, proof, offers) + your decks and docs
├── plays/<slug>/      one folder per segment or campaign
├── skills/            60 GTM skills, loaded on demand
├── db/schema.sql      the optional team database
└── .claude/commands/  the slash commands
```

## Rules

- **Nothing sends on its own.** Campaigns are created as drafts. You open them, read them, press go.
- **Every write to Instantly or Lemlist, and every paid data pull, is confirmed with you first.**
- **Never commit** a `.env`, a raw provider dump, or anything with a key in it. The commit guard
  blocks keys and files over 25MB, but it isn't a substitute for looking.
- Keys are set once with `python3 gtm.py set-key NAME` and never pasted into a command or a file.
- `/save` before you finish.
