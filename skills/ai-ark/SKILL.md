---
name: ai-ark
description: AI Ark - 400M people and 70M companies. Build TAM and target lists, size a market, find lookalike companies, pull contacts at named accounts, enrich one person, find a mobile number. Use for any sourcing or company/person search work.
---

# AI Ark

**`reference.md` next to this file is AI Ark's own full API context** (every endpoint, every filter
shape, every credit price, updated 2026-09-08). Read it before writing a request body; it is the
source of truth. This file is how we use it inside the GTM OS.

The key is `AI_ARK_API_KEY`, read with `gtm.cred()` (environment, then `~/.magna-gtm-config`,
then the `api_keys` table in your own database). Missing? `python3 gtm.py set-key AI_ARK_API_KEY`.

## Call it through `aiark.py`. Always.

```bash
A="python3 skills/ai-ark/aiark.py"
$A credits                                              # free
$A preview   --body b.json                              # 1 credit/page
$A people    --body b.json --size 50 --out plays/<play-slug>/leads/contacts/x.csv
$A companies --body b.json --size 100 --out plays/<play-slug>/leads/companies/x.csv
$A person    --id <uuid>                                # export single
```

`--body` is a JSON file holding the request body from this file and `reference.md`. The script
pages for you, goes through curl (see below), and flattens every record into a clean CSV whose
`ai_ark_people_id` / `ai_ark_account_id` columns carry AI Ark's own ids. **Save every pull's CSV
under the play's `leads/` folder** - those files are your record of what you already paid for.

A preview masks last names and returns no LinkedIn URL, so a preview CSV is for judging a list,
never for outreach.

## `--known` and `--new-only`: don't pay twice for the next step

Pass earlier pulls with `--known` and the run prints the overlap:

```
  already in your --known CSVs: 2,950 of 4,104 companies (72%)
```

⚠️ **This does NOT make the search cheaper, and nothing can.** AI Ark bills the query, and
which records match is only knowable by running it. The check happens on the way back.

**Where it actually saves money is the step after.** Add `--new-only` and the output CSV holds
only records not already in those files, so Exa deep research, email finding and every other
per-row cost runs over the new rows instead of the whole list. Measured on one real pull: 4,104
companies, **2,950 already held**, and a $0.012/company deep pass had run across all of them.

So the order is: pull -> read the overlap line -> if it is high, re-run with
`--known <old csvs> --new-only` before spending anything per row. Better still, check a known list
of domains against your existing CSVs BEFORE you search at all (`skills/list-dedup`).

```
Base:  https://api.ai-ark.com/api/developer-portal
Auth:  X-TOKEN: <key>          Content-Type: application/json
Free:  GET /v1/payments/credits     ->  {"total": N}
```

## ⚠️ Call it with curl, not urllib

macOS system Python 3.9 ships LibreSSL 2.8.3 and **cannot negotiate AI Ark's TLS**: `urllib` fails
with `TLSV1_ALERT_PROTOCOL_VERSION` even though the key is fine. Use `curl`, or
`skills/icp-tam-mapper/airk.py`, which falls back to curl. **Never conclude the key is dead from a
Python TLS error.**

## Preview first. Always.

`POST /v1/people/preview` takes the **same body as People Search** and costs **1 credit per page,
flat**, whatever the page size. It returns `totalElements` (the real match count), masked last
names, the full company object, the person's real `id`, and `has_*` flags (`has_mobile` etc).

So the loop is: preview → read `totalElements` and eyeball 25 rows → fix the filters → preview
again → only then spend per-result credits. Two or three previews cost 2-3 credits and routinely
save hundreds.

## What things cost

| Call | Price | Note |
|---|---|---|
| `POST /v1/people/preview` | **1 / page** | flat. Validate here. |
| `POST /v1/people` | 0.5 / result | data only, **no emails** |
| `POST /v1/companies` | 0.1 / result | lookalikes included |
| `POST /v1/people/email-finder` | 1 / **found** email | chains off a search `trackId` |
| `POST /v1/people/export` | 0.5 / person **+** 0.5 / found email | bulk, ≤10,000, async |
| `POST /v1/people/export/single` | 1 if an email is found, else 0 | one person |
| `POST /v1/people/mobile-phone-finder` | **5** / found phone | check `has_mobile` first |
| `POST /v1/people/reverse-lookup` | 0.5 | email -> person |
| `POST /v1/people/analysis` | 4 | personality profile |
| Lists, credits, statistics, inquiries | free | |

**State the estimate before anything over ~100 credits**, and check the balance first.
A 1,000-person export is up to 1,000 credits.

## In the GTM OS, use it for sourcing AND emails

1. **Do we already have them?** Check the CSVs already sitting in `plays/*/leads/` before paying
   AI Ark for the same people (`--known`, or `skills/list-dedup`).
2. **Sourcing is AI Ark's job**: people search, company search, lookalikes, market sizing.
3. **Emails come from AI Ark too.** Single person: `aiark.py person --id <uuid>` (Export Single,
   1 credit only if an email is found). A whole searched list: `POST /v1/people/email-finder`
   chained off the search `trackId` (1 credit per found email), or the bulk async
   `POST /v1/people/export` (≤10,000, 0.5/person + 0.5/found email). See `reference.md`.
4. Sizing a market end to end: `skills/icp-tam-mapper` (TAM → SAM → SOM with live counts).

## The four shapes worth memorising

```jsonc
// filters live under "account" (company) and "contact" (person). NOT "accountFilter".
{"account": {...}, "contact": {...}, "lists": {...}, "page": 0, "size": 25}

// text filter: a match mode wrapper, not a bare array
"industries": {"any": {"include": {"mode": "SMART", "content": ["software development"]}}}
//   SMART = related concepts (default) · WORD = exact phrase, extra words ok · STRICT = exact only

// plain-array filter (location, seniority, departmentAndFunction, domain, linkedin, type, naics)
"seniority": {"any": {"include": ["c_suite", "vp"]}}

// range filter: an ARRAY of bands, OR'd
"employeeSize": {"type": "RANGE", "range": [{"start": 51, "end": 200}]}
```

`any` = OR (more values, broader). `all` = AND (more values, narrower). Max 300 values per array.
A search cannot be exclude-only.

## Traps we have actually hit

- **`latest` vs `current` job title.** `current` covers *every* simultaneously-active role, so an
  advisor gig or a side project matches and pollutes the list. For "their job today" use
  `contact.experience.latest`. (Measured; this one silently widens a TAM.)
- **`lookalikeDomains` sits at the ROOT of the Company Search body**, not inside `account`. Max 5.
- **Company targeting by name is unreliable** (same-name companies). Resolve the domain to a company
  `id` with Company Search, then use `contact.company.latest/current/previous` with that UUID.
  Universities resolve the same way, which is how `education.school` works.
- **A search pages through at most 10,000 records** even when `totalElements` is far higher. Past
  that: push the returned ids into a free List and re-run excluding it (see reference.md §5).
  Lists expire after **24 hours**.
- **`trackId` is single-use and expires in 6 hours.** Search, then submit email finding immediately.
- **404 usually means "no result", not failure** (no match, no email, no phone). Don't retry blindly.
- **429 can be account-wide.** Every call including the free credits endpoint has been seen
  returning `API rate limit exceeded` for minutes when another job was sharing the same token.
  Back off; it is not a bad key. Limit is 5 requests/second per token.
- **The email object's address field is `address`, NOT `email`** - and the provider lives inside
  `mx`, not at the top level. The real shape is
  `{address, status, subStatus, domainType, free, generic, found, date, mx:{record, provider, google, found}}`.
  Reading `email` returns nothing while `status` and `domainType` still arrive, so a row looks
  complete and is missing the one thing you paid for. This once shipped broken in `aiark.py` for
  six days; the script now reads `address`.
- **Never re-verify an AI Ark email.** Every returned address is BounceBan-verified in real time.
  Segment on `domainType` (`SMTP` vs `CATCH_ALL`) and `generic` instead.
- **Counting:** a `size: 1` search returns the true `totalElements` for 0.5 credits (people) or
  0.1 (companies), which is cheaper than a preview page when you only want the number. Preview wins
  when you also want to see who is in the set.

## Intent signals worth filtering on

`metric.growth` (department headcount growth over 1-24 months) · `funding.duration` (epoch-ms range
of the last round) · `contact.experience.latest.duration.latestJob.max` of 6 months (new in role) ·
`profileBadge: HIRING` · `account.employee` in Company Search (which accounts even employ this role).

## The old "filters are broken, use MCP" note was wrong

The 2026-03 version of this skill claimed contact-level filters are silently ignored by the API and
that people search had to go through the MCP server. **Re-tested 2026-09-23 and that is false.**
A `preview` with `contact.experience.latest.title` (WORD "head of sales") + `seniority` [head, vp]
+ `location` Germany + `account.employeeSize` 51-200 returned `totalElements: 2400` and five rows
that all matched every filter (Head of Sales titles, seniority `head`, Germany, 53-199 staff).

The old note used the key **`contactFilter`**, which is not a field — the API ignores unknown keys
and returns the unfiltered database, which is exactly the symptom it described. Use `contact` and
`account`, nested as in `reference.md`.

MCP is still available if you prefer it: `https://api.ai-ark.com/v1/mcp?token=<key>`.

## Reading a preview result

`full_name` comes back **empty** and the last name is masked — that is the point of preview. Title,
seniority, location, company, `has_*` flags and the real `id` are all there, which is enough to
judge a list. Take the `id` straight to Export Single to enrich the ones you want.

## Balance

Run `aiark.py credits` (free) before any job over ~1,000 credits and state the estimate first.
The key is `AI_ARK_API_KEY` via `gtm.cred()` — **never hard-code one**, or you silently spend a
different account's credits.
