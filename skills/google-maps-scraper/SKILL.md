---
name: google-maps-scraper
description: Scrape Google Maps for businesses with Apify (compass/crawler-google-places) from a plain-English request. Returns name, phone, website, address, category, rating and reviews as CSV. Use when someone asks to scrape Google Maps, pull local businesses, build a list of places ("every dentist in Denver", "law firms across Illinois", "coffee shops in Austin with a website"), or check Apify Google Maps cost or run status.
---

# Google Maps Scraper (Apify)

Turn a request like *"get me every personal injury firm in Illinois except Chicago"* into an Apify
Google Maps run, and hand back clean CSVs with a cost receipt.

Everything goes through `gmaps.py`, which sits next to this file (stdlib Python, no installs).
Run it as `python3 skills/google-maps-scraper/gmaps.py ...` from the repo root. The Apify token
(`APIFY_TOKEN`) is resolved by `gtm.cred` (environment, then `~/.magna-gtm-config`, then the
`api_keys` table). If it is missing, add it once with `python3 gtm.py set-key APIFY_TOKEN`
(value on stdin).

**In the GTM OS:** save output under the play (`--out-dir plays/<play-slug>/leads/companies/...`).
Google Maps is a sourcing tool for local businesses; it is not an enrichment provider, so emails
still come from AI Ark or Freckle.

## This spends real money, so follow the loop

Never go straight to a full run. Every scrape follows these steps:

1. **Understand the request.** Pull out:
   - **Search terms**: what you would type into Google Maps. Suggest variants when they help
     coverage ("family law firm" + "family law attorney"), and show the user the final list.
   - **Location**: free text such as `"Illinois, USA"` or `"Austin, Texas, USA"`.
   - **Size**: the most places to collect *per term*.
   - **Filters to apply afterwards**: cities to leave out, category keywords, must have a phone or website.
2. **Check the budget.** Run `gmaps.py whoami`. It shows this cycle's spend against the account's
   monthly cap. Tell the user how much is left before proposing a size.
3. **Estimate.** Run `gmaps.py estimate --terms ... --per-term N` and state the worst case in dollars.
4. **Pilot.** Run with `--pilot` (30 places per term), usually about $0.10 to $0.50. Report:
   - phone, website and address coverage
   - the **top categories**, which show the noise your filter will need to remove
   - whether each term hit 30. If every term hit 30, Google has more to give; if terms came back
     short, the full run will saturate early and cost much less than the worst case.
5. **Confirm with the user** the per-term limit and a `--max-usd` budget. Do not start the full run
   without an explicit yes on the dollar figure.
6. **Full run.** Up to about 5,000 places: run in the foreground. Bigger: use `--detach`, then poll
   `status`, then `fetch`. Report places and spend while it runs.
7. **Filter and deliver.** Build `--category-regex` from the categories the pilot showed.
   Give the user the final row count, the coverage, the final cost, and where the files are.
   Save to the folder the user names; default is `./gmaps-output/`.

## Commands

```bash
G="python3 skills/google-maps-scraper/gmaps.py"

$G whoami                                   # account, plan, spend this cycle vs cap
$G estimate --terms "dentist" "orthodontist" --per-term 2000

# pilot: 30 per term, cheap
$G run --terms "dentist" "orthodontist" --location "Denver, Colorado, USA" --pilot --max-usd 1

# full run with filters applied to the output
$G run --terms "family law firm" "family law attorney" \
       --location "Illinois, USA" --per-term 5000 --max-usd 40 \
       --category-regex "law|attorney|legal" --exclude-city Chicago \
       --out-dir ./gmaps-output/illinois-family-law

# preview the exact Apify input and cost without starting anything
$G run ... --dry-run

# long runs
$G run ... --detach        # prints the run id right away
$G status <RUN_ID>         # status, places so far, dollars so far
$G fetch  <RUN_ID> [filters] --out-dir DIR
$G abort  <RUN_ID>

# re-filter downloaded results for free (no new scrape)
$G filter --raw DIR/raw.json --category-regex "dent" --exclude-city Denver --name no-denver.csv
```

### `run` options

| Flag | Meaning |
|---|---|
| `--terms` / `--terms-file` | search terms (a file takes one per line) |
| `--location` | free-text place: `"Illinois, USA"`, `"Miami, Florida, USA"` |
| `--country` `--state` `--city` `--postal-code` | structured location instead of `--location` |
| `--per-term N` | **most places PER SEARCH TERM**, not in total |
| `--pilot` | caps at 30 per term |
| `--max-usd X` | **required.** Apify stops charging at this amount; minimum 0.50 |
| `--min-stars` | `two` `twoAndHalf` `three` `threeAndHalf` `four` `fourAndHalf` |
| `--website-filter` | `allPlaces` (default), `withWebsite`, `withoutWebsite` |
| `--search-matching` | `only_includes` = the place name must contain the term |
| `--include-closed` | keep closed places (skipped by default) |
| `--contacts` | **paid add-on**: crawls each website for emails and social links. Pilot it first to measure cost |
| `--category-regex` `--exclude-city` `--only-state` `--require-phone` `--require-website` | filters applied to the output files |
| `--detach` `--dry-run` `--out-dir` `--poll` | control how it runs |

### Output files

- `raw.json`: the full Apify records
- `places-all.csv`: every place, flattened
- `places-filtered.csv`: written only when a filter flag was given

Columns: `name, phone, website, domain, street, city, state, postal_code, country_code,
full_address, category, all_categories, search_term, rating, reviews, emails, google_maps_url,
place_id, lat, lng, temporarily_closed, permanently_closed`

## Cost

**About $0.00275 per place, all in** (measured over 7,790 places with closed places skipped).
Apify's API hides current prices, so don't quote the docs. After a pilot, divide the run's spend
by its place count and use that figure.

| Real run | Ceiling | Actual |
|---|---|---|
| 6 legal terms x 10,000, `Illinois, USA` | 60,000 places / $165 | **7,790 places / $21.42**, ~25 min |
| 6 legal terms x 30 (pilot) | 180 | 180 places / $0.50, 45 s |
| 1 term x 5, `Evanston, Illinois, USA` | 5 | 5 places / $0.01, 20 s |

## Gotchas (all hit in real runs)

1. **`--per-term` counts per search term, and there is no field for a total.** 6 terms x 10,000
   means up to 60,000 places. Always multiply before proposing a number. When a user says
   "limit 15,000", ask whether they mean in total (divide by the number of terms) or per term.
2. **Runs stop when Google runs out of results.** Illinois law firms topped out at 7,790 against a
   60,000 ceiling. The ceiling is a worst case, not a forecast; the pilot tells you which is likely.
3. **Results are de-duplicated across terms.** Each place appears once, tagged with the *first*
   term that found it. `search_term` shows how a place was found, not everything it does. To learn
   whether a business matches several terms, run each term separately.
4. **Broad terms pull in unrelated businesses.** "personal injury" returned chiropractors,
   physical therapists, accountants and private investigators (317 of 7,790). Always look at the
   pilot's top categories and filter with `--category-regex`.
5. **Google Maps lists locations, not companies.** A business with 5 offices appears 5 times, and
   solo professionals often list under their own name. Say this when reporting counts.
6. **To exclude a city, filter afterwards.** Search the whole region, then use `--exclude-city`.
   Matching is exact and case-insensitive on `city`. Some rows have a blank city (112 of 7,790),
   and `state` can be `Illinois`, `IL` or blank, so pass both forms to `--only-state`.
7. **The budget cap must be at least $0.50** (Apify rejects anything lower).
8. **Your Apify account has a monthly usage cap**, and every run on the token counts against it.
   Run `whoami` first. When the cap is reached, runs fail partway through.
9. **Emails are not included by default.** Google Maps has no emails; `--contacts` crawls websites
   for them and costs extra. Offer it; don't switch it on without asking.
10. **Location text:** keep it simple, like `City, State, Country` or `State, Country`.
    Whole-state runs are verified. Whole-country runs are not; pilot them, or split by state.
