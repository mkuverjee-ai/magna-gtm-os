Live campaign numbers, for one campaign, one play or all of them.

Request: **$ARGUMENTS**

Usage: `/report` (everything, last 7 days) · `/report <play or campaign> [days]`

## Steps

1. **Find the campaigns.** `python3 gtm.py campaigns`, matched to the request (or to the campaigns
   listed in `plays/<slug>/PLAY.md`).

2. **Pull the numbers** with the platform skill, which carries the real endpoints and traps:
   `skills/instantly` (analytics) and `skills/lemlist-reporting`. Per campaign: sent, replies,
   positive replies, bounces, meetings if tracked, and per step / per variant where available.
   For "why" questions (which angle, which persona, which step) use
   `skills/campaign-performance-diagnostic`.

3. **Check the log first:** `python3 gtm.py intel --play <slug>`. If something already explains what
   you see, cite it.

4. **Write it to** `plays/<slug>/reports/YYYY-MM-DD-report.md` (company-wide: `company/reports/`):
   - **Per campaign:** the numbers
   - **Working:** best performers and *why* you think so
   - **Not working:** zero-reply steps, high bounce, a persona that never answers
   - **Do next:** pause X, scale Y, rewrite step 2 of Z

5. **Offer to log what you learned** with `python3 gtm.py log-intel` if the numbers show something
   reusable, with sample size and reply rate.

## Rules

- Reply rate is the signal; open rate is unreliable when open tracking is off.
- Benchmarks from a few hundred B2B campaigns: median reply 0.64%, top decile 2.75%, ~25% of replies
  positive. Event and inbound audiences run far higher; don't average them in with cold.
- Out-of-office replies are not replies. Strip them before quoting a rate, and note return dates.
- Under ~200 sends, say so. Never fabricate a number; if the API didn't return it, say "unavailable".
