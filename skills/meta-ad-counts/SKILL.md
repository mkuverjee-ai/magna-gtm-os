---
name: meta-ad-counts
description: Count how many Meta (Facebook/Instagram) ads a company runs, split active vs inactive and video vs static, from the Meta Ad Library via Apify. Counts only, $0.0042 per count, one company or a whole CSV. Use when someone asks how many ads / video ads a brand is running, wants to qualify or sort a list by Meta ad volume ("only companies with 10+ active video ads"), check whether a prospect advertises on Meta, find which Facebook page a brand advertises from, or add ad-count columns to a lead list.
---

# Meta Ad Counts (Meta Ad Library via Apify)

Answers "how many Meta ads does this company run?" for one company or a whole list:

| Column | Means |
|---|---|
| `active_all` / `inactive_all` | every ad on the page, live / stopped |
| `active_video` / `inactive_video` | video ads |
| `active_static` / `inactive_static` | image + meme ads (meme = image with text on it) |

Everything goes through `meta_ads.py` next to this file (stdlib Python, no installs). Run it from the
repo root as `python3 skills/meta-ad-counts/meta_ads.py ...`. The Apify token (`APIFY_TOKEN`) is
resolved by `gtm.cred` (environment, then `~/.magna-gtm-config`, then the `api_keys` table), the same
Apify account as `google-maps-scraper`. If it is missing: `python3 gtm.py set-key APIFY_TOKEN`.

It uses `apify~facebook-ads-scraper` in **`onlyTotal` mode**: the actor returns the count and never
downloads the ads, so a count costs the same **$0.0042** whether the page has 3 ads or 3,000.
Measured on 3,871 runs: $16.26.

## Two ways to count, and why it matters

**Page mode (default, exact).** Finds the Facebook page the brand actually advertises from, then
counts that page. The page is found cheapest-first:
1. Facebook links on the brand's own website (a page with 0 active ads is skipped, because brands
   often link a dormant page and advertise from another: one B2B software brand's site page had 0, its real page 192).
2. An exact-phrase Ad Library search for the brand name (10 ads, about $0.04), grouped by page;
   a page whose name matches the brand wins.

`confidence`: `high` = page name matches the brand · `check` = most ads come from a page with a
different name, so eyeball it · `low` = scattered across pages · `no_ads_found`.

**Keyword mode (cheap, approximate).** Counts every ad in the Ad Library containing the brand name
as an exact phrase. That's one call per metric, with no page lookup. It also counts affiliates, resellers,
review sites and anyone else using the words. Measured on Cal AI: keyword **706** active video vs
the real page **617**. Good for sorting a big list; not for quoting a number to a prospect.

Keyword `confidence` flags the counts you can't trust:
- `capped_generic_term`: hit the Ad Library ceiling of **50,001**. The name is a common word
  ("Magic", "Elevate"), not a giant advertiser.
- `generic_name_use_page_mode`: the name is made of dictionary words ("Calm", "Penny", "Waiter":
  5,003 ads, almost none theirs). Recount in page mode.
- `long_name_may_undercount`: 4+ words; app store names like "Slotomania Casino Slots Game"
  don't appear verbatim in ads and come back 0. Use `--clean-names` or a shorter brand.
- A name that equals its domain stem ("Cal AI" on `calai.app`) is treated as a brand, not two words.

Sensible pattern for a big list: **keyword mode for everyone, page mode for the rows that matter**
(the ones over your threshold, or flagged).

## This spends real money, so follow the loop

1. **Budget.** `meta_ads.py whoami`: this cycle's spend vs your account's monthly cap. Say what's left.
2. **Estimate.** `bulk ... --estimate` prints the worst case and the time. Page mode is about
   **$0.06/row** (lookup + 4 counts), keyword mode **$0.004-0.017/row** depending on `--metrics`.
3. **Pilot** 10-20 rows, read the `confidence` column, fix the name column if it's noisy.
4. **Confirm `--max-usd` with the user.** Do not run without an explicit yes on the dollar figure.
   `bulk` refuses to run without it and stops when it's spent.
5. **Run.** Resumable: results cache to `<out>.cache.jsonl`; re-run the same command after a stop or
   crash and it picks up where it left off. 12-18 workers is safe; measured 171 counts/min at 18.
6. **Deliver** the CSV under `plays/<play-slug>/leads/companies/`.

## Commands

```bash
M="python3 skills/meta-ad-counts/meta_ads.py"

$M whoami
$M find-page --brand "Cal AI=calai.app"                  # which page do they advertise from?
$M count --brand "Cal AI=calai.app"                      # page mode, full matrix (8 counts, ~$0.08)
$M count --page 311353912066626 --metrics active         # known page, active only (4 counts)
$M count --keyword "Cal AI" --metrics video              # quick approximate video count
$M count --brand "Strava=strava.com" --country ALL       # worldwide instead of US

# a list
$M bulk --in apps.csv --out apps-ad-counts.csv --name-col top_app --domain-col domain \
        --mode keyword --metrics video --clean-names --estimate
$M bulk --in apps.csv --out apps-ad-counts.csv --name-col top_app --domain-col domain \
        --mode keyword --metrics video --clean-names --workers 18 --max-usd 20
$M bulk --in shortlist.csv --out shortlist-exact.csv --name-col company --domain-col domain \
        --mode page --metrics active --max-usd 10
```

`--metrics`: `full` = active + inactive x all/video/static (8 counts) · `active` = active
all/video/static (4, the default for bulk) · `video` = active video only (1).
`--page-col` uses page ids you already have and skips the lookup.
`--country` defaults to `US`; `ALL` counts every country.

## Measured traps

- **`onlyTotal` on a bare facebook.com page URL counts ALL countries.** For a country count the
  script builds an Ad Library URL with `country=` and `view_all_page_id=`. Don't pass page URLs by hand.
- **Inactive counts are small and partial.** Cal AI: 660 active, 17 inactive (US). The Ad Library
  only surfaces part of a page's history, so treat inactive as "at least", not a lifetime total.
- **static = image + meme.** Cal AI US active: 617 video + 0 image + 43 meme = 660. Counting only
  `image` reports 0 static ads for a page that runs 43.
- **403 from Apify = your account's monthly cap.** The script stops immediately instead of retrying.
- **Apify 502s happen** (about 1 in 5 advertisers on one run); the script retries 5xx with backoff.
- **App Store names make bad search terms.** Cut at the first ` - ` / `:` (`--clean-names`):
  "Cal AI - Calorie Tracker" -> "Cal AI". 479 of 3,382 app names returned 0 until cleaned, and 283
  of those had ads.
- **A brand's own site often blocks bots**, so step 1 finds no link and step 2 (phrase search) does
  the work. That's normal.

## Where it came from

Built on a mobile-app list build: 3,382 top-grossing app companies counted for active US video
ads in about 30 minutes for $16.26, 1,573 with 10+.
