---
name: ocean-lookalike
description: Find companies that look like a company you already have - clone a closed-won customer, a competitor's customer, or any seed domain into a list of similar companies. Use when someone says "find more like X", "lookalikes", "companies similar to our best customer", or wants a target list built from an account rather than from filters.
---

# Ocean.io lookalikes

One seed domain in, companies like it out. This is how the OS asks **"who looks
like this company"**. AI Ark answers *"who matches these filters"*, which is a different
question and a different tool.

```bash
O="python3 skills/ocean-lookalike/ocean.py"
$O count acme.com                                      # how many exist (0.2 credits)
$O count acme.com --size 51-200,201-500 --country US,GB
$O find  acme.com --limit 50 --out plays/<play-slug>/leads/companies/x.csv
$O find  acme.com,stripe.com --limit 100 --out x.csv   # up to 5 seeds, blended
```

Ocean.io is optional. If you have a key: `python3 gtm.py set-key OCEAN_API_KEY` once, and the
script reads it with `gtm.cred()`. Without one, use AI Ark's `lookalikeDomains` (max 5 seeds, at
the ROOT of the Company Search body) as the fallback.

## Size it before you spend

**0.2 credits per company returned, measured.** `count` runs a single-row search and reads the
full `total`, so it tells you the size of the set for 0.2 credits before you commit to the
whole thing. A 280-company pull is about 56 credits; know that before you run it.

Filters narrow the lookalike set, they do not replace it: `--size` takes Ocean's bands
(`11-50`, `51-200`, `201-500`, `501-1000`, `1001-5000`) and `--country` takes ISO-2 codes.

## When to use this instead of AI Ark

| The question | Tool |
|---|---|
| "Find more companies like our best customer" | **Ocean** - similarity IS the filter |
| "Find heads of sales at US SaaS companies, 51-200" | AI Ark - you already know the shape |
| "Who could ever buy from us" (a whole TAM) | AI Ark, `icp-tam-mapper` |
| "Do we already have them?" | the CSVs already in `plays/*/leads/` (`skills/list-dedup`), free |

**Ocean returns companies, never people.** Once you have the list, contacts and emails come
from `ai-ark` (via `aiark.py`). Ocean is the top of that chain, not the whole chain.

## What it gives you per company

name, domain, country, size band, headcount (Ocean's own and LinkedIn's), revenue band, year
founded, LinkedIn industry, the full industry keyword list, LinkedIn URL, city and region,
the last funding round with type, date and USD, plus Ocean's own `relevance` score and the
description.

## Traps

- **`locations` is a LIST of objects, not a dict**, and `medias.linkedin` is an **object with
  a `.url`**, not a string. Both crash a naive parser on the first row. The script handles it.
- **Field names are validated and a wrong one 422s the whole call.** `employeeCount`,
  `industry` and `linkedinUrl` are not fields; `employeeCountOcean`, `industries` and
  `medias.linkedin` are. The script only sends known-good names.
- **A seed domain is required.** Ocean without `lookalikeDomains` is not this tool.
- **Save the CSV under the play** (`plays/<play-slug>/leads/companies/`). Ocean rows carry no
  AI Ark id, so de-dup them against other lists by domain (`skills/list-dedup`).
- The seed matters more than the filters. A vague seed (a huge conglomerate, a holding
  company) produces a vague list. Seed on a real customer with a real shape.

## Before a big pull

State the count and the credit cost from `count`, and get a yes from whoever owns the Ocean
budget. There is no per-run cap to catch a mistake.
