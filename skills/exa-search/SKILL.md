---
name: exa-search
description: Exa.ai Search API — semantic and keyword web search for LinkedIn profile discovery, company research, and content finding. Full API reference with proven search strategies, gotchas, and cost breakdown.
---

# Exa.ai Search API Skill

## Overview

Exa (`api.exa.ai`) is a search API optimized for finding specific types of web content. Its killer use case for outbound is **LinkedIn profile discovery** — finding people at target companies by searching for their profiles semantically or by keyword.

**Base URL:** `https://api.exa.ai`
**Auth:** `x-api-key` header
**Docs:** https://docs.exa.ai
**Dashboard:** https://dashboard.exa.ai
**Key:** Exa is optional. If you have a key: `python3 gtm.py set-key EXA_API_KEY`, then read it in code with `gtm.cred("EXA_API_KEY")`.

---

## Endpoints

### `POST /search` — Core Search

The main endpoint. Searches the web and returns URLs + metadata.

```json
{
  "query": "PIMCO compliance officer London site:linkedin.com/in",
  "type": "keyword",
  "numResults": 15,
  "includeDomains": ["linkedin.com"],
  "contents": {
    "text": {"maxCharacters": 500},
    "highlights": true
  }
}
```

**Parameters:**

| Param | Type | Description |
|-------|------|-------------|
| `query` | string | Search query (required) |
| `type` | string | `"keyword"` or `"neural"` (default: auto) |
| `numResults` | int | Results to return, 1-100 (default: 10) |
| `includeDomains` | string[] | Only return results from these domains |
| `excludeDomains` | string[] | Never return results from these domains |
| `startPublishedDate` | string | ISO date — only content published after this |
| `endPublishedDate` | string | ISO date — only content published before this |
| `startCrawlDate` | string | ISO date — only content crawled after this |
| `endCrawlDate` | string | ISO date — only content crawled before this |
| `contents` | object | Optional: request text/highlights with results |
| `contents.text` | object | `{"maxCharacters": 500}` — page text extract |
| `contents.highlights` | bool | Return relevant text snippets |

**Response:**

```json
{
  "results": [
    {
      "title": "John Smith - Chief Compliance Officer - PIMCO | LinkedIn",
      "url": "https://uk.linkedin.com/in/john-smith-12345",
      "publishedDate": "2024-01-15",
      "score": 0.85,
      "text": "Chief Compliance Officer at PIMCO. London, United Kingdom...",
      "highlights": ["Chief Compliance Officer at PIMCO"]
    }
  ],
  "autopromptString": "...",
  "requestId": "..."
}
```

### `POST /findSimilar` — Find Similar Pages

Find pages similar to a given URL. Useful for "find more people like this."

```json
{
  "url": "https://uk.linkedin.com/in/example-cco",
  "numResults": 10,
  "includeDomains": ["linkedin.com"]
}
```

### `POST /contents` — Get Page Contents

Retrieve text content for a list of URLs (up to 100).

```json
{
  "ids": ["https://uk.linkedin.com/in/john-smith"],
  "text": {"maxCharacters": 1000},
  "highlights": true
}
```

---

## Search Types: Keyword vs Neural

### `"keyword"` — Use This for LinkedIn Profile Discovery

- Literal string matching, like traditional search
- Respects `site:` operators in the query
- Best for finding specific LinkedIn profiles
- Predictable, precise results
- **This is what works for contact discovery**

### `"neural"` — Use for Content/Article Discovery

- Semantic/meaning-based search
- Better for finding articles, blog posts, research
- **DO NOT use for LinkedIn profiles** — returns company posts, articles, job listings instead of individual profiles
- Useful for: finding competitor content, industry articles, news mentions

---

## Proven Search Strategies for LinkedIn Contact Discovery

### The Winning Formula

```
"{Company Name}" {title keywords} {location} site:linkedin.com/in
```

With `includeDomains: ["linkedin.com"]` and `type: "keyword"`.

### Strategy: 4 Queries Per Company

For each target company, run these 4 queries:

```python
queries = [
    f'{company} compliance officer London site:linkedin.com/in',
    f'{company} compliance regulatory Dublin OR Luxembourg site:linkedin.com/in',
    f'{company} CFO OR CCO OR COO site:linkedin.com/in',
    f'{company} "head of compliance" OR "head of risk" OR MLRO site:linkedin.com/in',
]
```

### Company Name: Use the Brand, Not the Legal Entity

**CRITICAL:** LinkedIn profiles list the parent brand, not the legal entity.

| Legal Entity (from spreadsheet) | What People Put on LinkedIn | What to Search |
|---|---|---|
| Pimco Global Advisors (Ireland) Limited | PIMCO | Pimco |
| HSBC Investment Funds (Luxembourg) S.A. | HSBC Asset Management | Hsbc |
| abrdn Fund Managers Limited | abrdn | Abrdn |

**Best approach:** Extract the brand from the domain name (e.g., `pimco.com` → "Pimco") and use that as the primary search term. Fall back to the entity name only if the domain-derived name gets 0 results.

### Location Filtering: Use LinkedIn Country Subdomains

LinkedIn uses country-specific subdomains that reliably indicate where a person is based:

| Subdomain | Country |
|-----------|---------|
| `uk.linkedin.com` | United Kingdom |
| `ie.linkedin.com` | Ireland |
| `lu.linkedin.com` | Luxembourg |
| `de.linkedin.com` | Germany |
| `fr.linkedin.com` | France |

**Filter by parsing the URL subdomain** — this is more reliable than text-based location extraction.

**DO NOT** put country subdomains in `includeDomains` — it returns 0 results:
```json
// BAD — returns nothing
{"includeDomains": ["uk.linkedin.com", "ie.linkedin.com"]}

// GOOD — returns all LinkedIn results, filter by URL after
{"includeDomains": ["linkedin.com"]}
```

### Parsing LinkedIn Page Titles

LinkedIn profile titles follow this pattern:
```
{Full Name} - {Job Title} - {Company} | LinkedIn
{Full Name} - {Job Title} at {Company} | LinkedIn
```

Parse with:
```python
import re

def parse_linkedin_title(title):
    clean = re.sub(r"\s*[-|]\s*LinkedIn\s*$", "", title).strip()
    parts = re.split(r"\s+-\s+", clean, maxsplit=1)
    full_name = parts[0].strip()
    job_title = parts[1].strip() if len(parts) >= 2 else ""
    return full_name, job_title
```

---

## What Does NOT Work

1. **Neural search for profiles** — returns company pages, job posts, articles
2. **Country subdomains in `includeDomains`** — Exa doesn't recognize them, returns 0
3. **Long complex OR queries** — `"PIMCO" compliance OR regulatory OR CFO OR CCO OR COO OR risk London OR Dublin OR Luxembourg` → 0-1 results. Keep queries simpler.
4. **Formal legal entity names** — "Pimco Global Advisors (Ireland) Limited" → 1 result. "Pimco" → 21 results.
5. **Expecting structured data** — Exa returns web search results, not structured contact records. You must parse names and titles from page titles/text.

---

## Cost Breakdown

Exa charges per search based on features used:

| Feature | Cost per Search |
|---------|----------------|
| Basic search (URL + title only) | ~$0.0025 |
| Search + text content | ~$0.005 |
| Search + text + highlights | ~$0.0085 |
| `/contents` endpoint | ~$0.001 per URL |
| `/findSimilar` | Same as search |

### Cost Example: one real contact-discovery project (fund managers, UK/IE/LU)

- 96 companies × 4 queries each = 384 searches
- At ~$0.0025 per search (no text content) = **~$0.96 total**
- With text content (~$0.005 each) = **~$1.92 total**
- Result: 1,827 raw contacts → 1,196 after filtering → 153 strict-title matches

**Extremely cost-effective** compared to a structured people database (e.g. AI Ark at 0.5 credits per result).

---

## Rate Limits

- No hard published rate limit, but respect reasonable usage
- Recommended: 0.3-0.5 second delay between requests
- Batch in groups of 10 companies with 1-second breaks
- If you get 429s, back off exponentially

---

## Python Example: LinkedIn Contact Discovery

```python
import re
import sys
import time

import requests

sys.path.insert(0, "<repo root>")  # the folder holding gtm.py
import gtm

EXA_API_KEY = gtm.cred("EXA_API_KEY")  # add it with: python3 gtm.py set-key EXA_API_KEY

def search_exa(query, num_results=15):
    """Search Exa.ai and return results."""
    resp = requests.post(
        "https://api.exa.ai/search",
        json={
            "query": query,
            "type": "keyword",
            "numResults": num_results,
            "includeDomains": ["linkedin.com"],
        },
        headers={
            "Content-Type": "application/json",
            "x-api-key": EXA_API_KEY,
        },
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json().get("results", [])


def get_country_from_url(url):
    """Extract country from LinkedIn subdomain."""
    subdomain = url.split("/")[2]
    if subdomain.startswith("uk."):
        return "United Kingdom"
    elif subdomain.startswith("ie."):
        return "Ireland"
    elif subdomain.startswith("lu."):
        return "Luxembourg"
    return ""


def parse_linkedin_title(title):
    """Parse name and job title from LinkedIn page title."""
    clean = re.sub(r"\s*[-|]\s*LinkedIn\s*$", "", title).strip()
    parts = re.split(r"\s+-\s+", clean, maxsplit=1)
    full_name = parts[0].strip()
    job_title = parts[1].strip() if len(parts) >= 2 else ""
    return full_name, job_title


def find_contacts_at_company(company_name, domain=""):
    """Find LinkedIn profiles of people at a company."""
    # Use domain-derived brand name for better results
    brand = domain.split(".")[0].title() if domain else company_name

    queries = [
        f'{brand} compliance officer London site:linkedin.com/in',
        f'{brand} compliance regulatory Dublin OR Luxembourg site:linkedin.com/in',
        f'{brand} CFO OR CCO OR COO site:linkedin.com/in',
        f'{brand} "head of compliance" OR "head of risk" OR MLRO site:linkedin.com/in',
    ]

    contacts = {}
    for query in queries:
        results = search_exa(query, num_results=15)
        for r in results:
            url = r.get("url", "")
            if "/in/" in url and url not in contacts:
                country = get_country_from_url(url)
                if country:  # Only keep UK/IE/LU
                    name, title = parse_linkedin_title(r.get("title", ""))
                    contacts[url] = {
                        "full_name": name,
                        "title": title,
                        "linkedin_url": url,
                        "country": country,
                    }
        time.sleep(0.3)

    return list(contacts.values())
```

---

## Exa vs AI Ark — When to Use Which

| Factor | Exa.ai | AI Ark (`skills/ai-ark`) |
|--------|--------|-----------|
| **Best for** | Discovery — finding unknown people at companies | Enrichment — getting full data on known people/companies |
| **Data source** | Web crawl (LinkedIn pages, company sites, etc.) | Structured B2B people + company database |
| **Structured data** | No — raw search results, must parse titles/URLs | Yes — full name, title, company, location, start dates |
| **Email finding** | No | Yes (verified work emails) |
| **Company filtering** | Keyword matching (brand name in query) | Exact domain / company id filter |
| **Title filtering** | Keyword matching (in query) | Title + seniority + department filters |
| **Location filtering** | URL subdomain or text parsing | Structured location filter |
| **Cost for contact discovery** | ~$0.01 per company (4 queries) | 0.5 credits per result (preview 1 credit/page) |
| **Batch support** | No — sequential API calls | Yes — pages of up to 100, async export up to 10,000 |
| **LinkedIn URL required?** | No — searches by company name | No — domain is enough |
| **Result quality** | Noisy — need post-processing and filtering | Clean — structured, verified LinkedIn data |

**Use Exa when:**
- AI Ark's coverage of the company is thin or missing
- You need to cast a wide net and discover who works where
- Budget is tight and you need to search many companies cheaply
- Companies are small/obscure and may not have clean LinkedIn pages

**Use AI Ark (the default) when:**
- You have domains or company ids
- You need structured, clean contact data (name, title, location, start date)
- You want exact title / seniority filtering
- You need emails alongside the contact discovery
- You're doing batch operations on large lists (>100 companies)

---

## Common Gotchas

1. **Always use `type: "keyword"` for LinkedIn profiles** — neural returns noise
2. **Always use `includeDomains: ["linkedin.com"]`** — not country subdomains
3. **Keep `site:linkedin.com/in` in the query itself** — this forces individual profile results vs company pages
4. **Short company names work better** — "Pimco" not "Pimco Global Advisors (Ireland) Limited"
5. **Simple queries > complex queries** — don't chain too many OR operators
6. **Rate limit yourself** — 0.3s between calls, 1s between company batches
7. **Deduplicate by URL** — same profile often appears across multiple queries
8. **Filter after, not during** — get all results, then filter by country/title in code
9. **Multiple entities per domain** — if a parent company has 3 legal entities sharing a domain, don't duplicate contacts across all 3. Map to one row per person with combined entity names.
