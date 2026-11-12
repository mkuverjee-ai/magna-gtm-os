---
name: linkedin-scraper
description: Scrape LinkedIn posts from profiles or company pages, and everyone who reacted to or commented on them, with Apify. Returns CSVs. Use when someone asks who engaged with a post, wants a competitor's or founder's post engagers as a list, wants recent posts from a set of people, or asks about "engagers", "post reactions", "LinkedIn signals from posts".
---

# LinkedIn Scraper (Apify)

A post and engager pipeline built on two Apify actors. It writes CSVs into the play folder.

Everything goes through `linkedin.py` next to this file. The Apify token (`APIFY_TOKEN`) is
resolved by `gtm.cred` (environment, then `~/.magna-gtm-config`, then the `api_keys` table).
If it is missing, add it once with `python3 gtm.py set-key APIFY_TOKEN` (value on stdin).

```bash
python3 skills/linkedin-scraper/linkedin.py whoami         # your Apify account spend vs cap
```

## Three jobs

| Ask | Command |
|---|---|
| "What has X posted this week?" | `posts URL... --window week --max-posts 10` |
| "Who engaged with this post?" | `engagers POST_URL... [--no-comments]` |
| "Everyone engaging with these people's posts" | `harvest URL... --window week --originals-only` |

```bash
L=skills/linkedin-scraper/linkedin.py
python3 $L posts https://www.linkedin.com/in/jane-doe-example/ --window month --max-posts 10 \
    --max-usd 1 --out plays/<play-slug>/reports/jane-doe-posts.csv

python3 $L engagers https://www.linkedin.com/posts/... --max-usd 2 \
    --out plays/<play-slug>/leads/contacts/2026-09-22-post-engagers.csv

python3 $L harvest --urls-file competitors.txt --window week --max-posts 5 --originals-only \
    --max-usd 5 --out plays/<play-slug>/leads/contacts/2026-09-22-competitor-engagers.csv \
    --posts-out plays/<play-slug>/reports/competitor-posts.csv
```

`harvest` writes **one row per person** with `posts_engaged` counting how many of the posts
they touched. That count is the strongest intent field in the file; sort by it.

## This spends real money, so follow the loop

1. `whoami`: shows your Apify account's spend this cycle against its monthly cap. The same
   account also pays for the Google Maps and Meta ad scrapers. Say how much headroom is left.
2. Start small: one profile, `--max-posts 3`, or one post with `--max-per-post 50`.
3. Show the user the counts and a few rows, then confirm the full run and its `--max-usd`.
   Do not start the full run without an explicit yes on the dollar figure.
4. Save the output under `plays/<play-slug>/leads/contacts/`.

Measured cost: a 40-person engager pull and a 3-post pull both rounded to $0.00. A daily
24h post sweep runs about $0.007 to $0.011 per profile per day. Big posts (1,000+
reactions) cost real money; `--max-per-post` caps each post.

## What comes back

- **posts**: `profile, post_url, posted_at, author, is_repost, reactions, comments, shares, content`
- **engagers**: `post_url, name, first_name, last_name, headline, linkedin_url, location,
  engagement_type (like / empathy / praise / comment ...), comment_text`

No emails. Engagers are a sourcing list; enrich them with AI Ark or Freckle afterwards.

## Traps (all measured)

- **`--window` takes only `24h`, `week`, `month`, `year`.** `7d` or `30d` returns HTTP 400.
- **Reshares carry the ORIGINAL author's engagement.** A repost once inflated a count 70x. The
  `is_repost` column flags them (the actor's `repostedBy` field); use `--originals-only` when
  you are measuring someone's own reach.
- **Reactor URLs are member-ID URLs** (`linkedin.com/in/ACoAA...`) because the reactions actor
  runs in cheap `short` mode. Commenters come back with vanity URLs. The same person who both
  reacted and commented can therefore appear twice. Both URL forms resolve in a browser and in
  enrichment.
- **The actor sometimes returns a post twice.** Deduped on `shareUrn`/`entityId`, not URL.
- **An Apify failure stops the script.** Never read "0 posts" as "no activity" without seeing
  the command finish cleanly; a scheduled harvester once reported success for three weeks
  on a dead key.

## Not for

- Profile enrichment (job history, email): AI Ark or Freckle.
- Company-page follower lists or Sales Navigator searches: not supported.
- Automated daily monitoring: this is an on-demand tool. For a recurring sweep, re-run `harvest`
  with `--window 24h` on the schedule you choose and dedupe against the previous CSV.
