# AI Ark — official API context

Verbatim from AI Ark's own agent-context page (`https://docs.ai-ark.com`, updated 2026-09-08),
captured 2026-09-23. This is the vendor's reference: every endpoint, filter shape, credit
price, enum and response skeleton. `SKILL.md` next to it is how this OS uses it.

Live index: `https://docs.ai-ark.com/llms.txt` (append `.md` to any docs page for its markdown).
MCP server: `https://api.ai-ark.com/v1/mcp?token={YOUR-API-KEY}`

---

# AI Ark API — FULL CONTEXT FOR AI AGENTS

You are working with the **AI Ark API**, a B2B contact & company database (400M+ person profiles, 70M+ company profiles) used to build outbound lead lists with verified emails and mobile numbers.

## 1. Basics

* **Base URL:** `https://api.ai-ark.com/api/developer-portal`
* **Authentication:** every request needs the header `X-TOKEN: {API_KEY}`. Missing/invalid token → `401` from the gateway.
* **Content type:** every request needs the header `Content-Type: application/json`.
* All search/enrichment endpoints are `POST` with a JSON body. Status/result/history endpoints are `GET`; webhook re-sends are `PATCH`.
* **Rate limits:** 5 requests/second per token (default). Customers using >450,000 credits/month can request custom limits via support@ai-ark.com or the in-app chat.
* **Check balance any time (free):** `GET /v1/payments/credits` → `{ "total": 100 }`

## 2. Credit Pricing (memorize this before calling anything)

| Endpoint | Method & Path | Credits | Charged when |
|---|---|---|---|
| People Preview | `POST /v1/people/preview` | **1 per page (flat)** | Same filters as People Search. 1 credit whether the page has 25 or 100 results. Masked last names, no emails/phones, `has_*` availability flags. |
| People Search | `POST /v1/people` | **0.5 per result** | Per person returned. Full person + company data, **no email, no phone**. |
| Company Search (incl. Lookalike) | `POST /v1/companies` | **0.1 per result** | Per company returned (lookalike included). |
| Find Emails by Track ID | `POST /v1/people/email-finder` | **1 per found valid email (0.5 people data + 0.5 email), 0 if not found** | Only people with a found, BounceBan-verified email are charged. |
| Export People with Email | `POST /v1/people/export` | **0.5 per person + 0.5 per found valid email** | 0.5 for every exported person (found or not) + 0.5 extra per found email. |
| Export Single Person with Email (v1) | `POST /v1/people/export/single` | **1 if email found, 0 if not** | Only charged when a valid, BounceBan-verified email is returned. |
| Export Single Person with Email (v2, Clay) | `POST /v2/people/export/single` | **1 if email found, 0 if not** | Same as v1. `X-Credit` response header shows the charge. |
| Mobile Phone Finder (v1) | `POST /v1/people/mobile-phone-finder` | **5 per found phone number, 0 if none** | Charged only when a number is delivered (v1 returns `404` when none). |
| Mobile Phone Finder (v2, Clay) | `POST /v2/people/mobile-phone-finder` | **5 per found phone number, 0 if none** | Same as v1, with `X-Credit`. |
| Reverse People Lookup | `POST /v1/people/reverse-lookup` | **0.5 per request** | Per request. |
| Personality Analysis | `POST /v1/people/analysis` | **4 per request** | Per request. |
| Create/Update List | `POST /v1/lists` | **Free** | Never charged. |
| Fetch Credits | `GET /v1/payments/credits` | **Free** | Never charged. |
| All `/statistics`, `/inquiries`, `/submissions`, `/notify` endpoints | `GET` / `PATCH` | **Free** | Polling, fetching results, history and webhook re-sends never cost credits. |

**Cost math examples:**

* Preview, `size: 100`, any number of results → **1 credit** (the same 100 on People Search would cost 50).
* People Search, `size: 25`, 25 results → **12.5 credits**.
* Find Emails on those 25 people, 18 valid emails found → **18 credits** (the 7 without an email cost nothing).
* Export People with Email, `size: 1000`, 700 emails found → 1,000 × 0.5 + 700 × 0.5 = **850 credits**.
* Enriching 1 person via Export Single: **1 credit** (0 if no email found).
* Company Search, `size: 100`, 100 matches → **10 credits**.

**Automatic refunds (async jobs — Export People, Find Emails):** auto-refunded, no support ticket. Check `GET .../submissions` → `fullyRefunded: true` + `refundReason`:

| `refundReason` | Meaning | What to do |
|---|---|---|
| `SEARCH_NO_RESULTS` | The search matched nobody; fully refunded. | Broaden the filters. |
| `NO_EMAILS_FOUND` | People matched but no emails found; fully refunded. | Nothing — you paid 0. |
| `STUCK_HARD_REFUND` | Results not delivered within the time limit (≤10h); auto-refunded. | **Resubmit.** Track-ID endpoints return `403` (code `4031013`). |
| `STUCK_SOFT_REFUND` | Email-finding service did not respond; auto-refunded. | **Resubmit.** Track-ID endpoints return `403` (code `4031014`). |

## 3. Email Verification (applies everywhere emails are returned)

**Every email returned by any AI Ark endpoint (SMTP and CATCH_ALL) is verified in real time by BounceBan at the moment of the request.** All returned emails are safe to send — no re-verification with another tool is needed. Email charges only ever apply to emails that passed this real-time validation.

**Email output object** (identical shape everywhere emails appear):

```json
{
  "address": "jane.doe@acme.com",
  "found": true,
  "status": "VALID",
  "subStatus": "EMPTY",
  "domainType": "SMTP",
  "date": "2026-03-06T14:41:53.000474",
  "free": false,
  "generic": false,
  "mx": { "found": true, "record": "mx1.example.com", "google": false, "provider": "g-suite" }
}
```

`status`: `VALID` | `INVALID`. `subStatus`: `EMPTY` | `MAILBOX_NOT_FOUND` | `FAILED_SYNTAX_CHECK`. `domainType`: `SMTP` | `CATCH_ALL` | `UNKNOWN`. `mx.provider`: `microsoft` | `g-suite` | `mimecast` | `barracuda` | `proofpoint` | `cisco ironport` | `other` | null.

Use `generic` and `domainType` to segment sending. In async Export results the per-person wrapper is `"email": { "state": "PROCESSING" | "DONE", "output": [ ...email objects ] }`.

## 4. Which endpoint do I use? (decision guide)

| Goal | Use this |
|---|---|
| Cheaply check who/how many match an ICP before spending per-result credits | **People Preview** `POST /v1/people/preview` (1 credit/page, flat) |
| Build a list of people matching an ICP — data only, no emails yet | **People Search** `POST /v1/people` |
| Get emails for the people a search just returned | **Find Emails by Track ID** `POST /v1/people/email-finder` |
| One-shot: search an ICP **and** get emails, up to 10,000 people, async | **Export People with Email** `POST /v1/people/export` |
| Enrich ONE known person by AI-Ark ID or LinkedIn URL | **Export Single Person** `POST /v1/people/export/single` (`/v2/...` in Clay) |
| Get a mobile phone number for a known person | **Mobile Phone Finder** `POST /v1/people/mobile-phone-finder` (`/v2/...` in Clay) |
| I have an email address — who is this? | **Reverse People Lookup** `POST /v1/people/reverse-lookup` |
| Build target ACCOUNT lists, find similar companies, or companies that *employ* a role | **Company Search** `POST /v1/companies` (`lookalikeDomains`, `account.employee`) |
| Personality profile for message personalization | **Personality Analysis** `POST /v1/people/analysis` |
| Exclude already-contacted people/companies from future searches | **Create/Update List** `POST /v1/lists`, then the `lists` filter |
| Check remaining balance | `GET /v1/payments/credits` |

## 5. Standard Workflows (recipes)

### Recipe 0 — Always preview first (1 credit/page)

`POST /v1/people/preview` with your ICP filters. Check `totalElements` and sample quality; refine until right. The body is identical to People Search — when satisfied, send the same body to Recipe A or B.

Preview results include: each person's **real `id`** (accepted directly by Export Single Person), first name + **masked last name** (`Ba***e`), title, headline, location, department/functions/seniority, position history with dates, the **full company object**, and `has_*` availability flags (`has_mobile`, `has_skills`, `has_educations`, …) — see what data exists **before** paying to enrich; `has_mobile: true` means a Mobile Phone Finder call (5 credits) has something to find.

Preview returns **no emails, no phones, no `trackId`** (`trackId: null` — email finding chains off People Search only).

### Recipe A — Two-step list building (max control; pay only for found emails)

1. `POST /v1/people` with your ICP filters (`page`, `size` ≤ 100). Cost 0.5 × results. Response has the people, `totalElements`, and a `trackId`.
2. `POST /v1/people/email-finder` with that `trackId` and a `webhook` URL. Each `trackId` works **once** and **expires 6 hours** after the search response.
3. Poll `GET /v1/people/email-finder/{trackId}/statistics` until `state: DONE` (or wait for the webhook). Results are readable while running; unfinished items show `state: PROCESSING`.
4. Fetch results: `GET /v1/people/email-finder/{trackId}/inquiries?page=0&size=100`.

### Recipe B — One-step bulk export (up to 10,000 people)

1. `POST /v1/people/export` with the same filters as People Search, `size` up to **10000** (here `size` = total export size), plus a `webhook` URL. Returns a `trackId` and `state: PENDING`.
2. Poll `GET /v1/people/export/{trackId}/statistics` or wait for the webhook (re-trigger any time with `PATCH /v1/people/export/{trackId}/notify`).
3. Fetch results: `GET /v1/people/export/{trackId}/inquiries?page=0&size=100`. Returns `409` while still in progress — poll statistics until `state: DONE` first.

### Recipe C — Row-by-row enrichment (CRM / Clay / spreadsheets)

For each row call `POST /v1/people/export/single` (v1) or `POST /v2/people/export/single` (Clay) with `{ "id": "..." }` or `{ "url": "https://linkedin.com/in/..." }`. Add `POST /v1/people/mobile-phone-finder` if you also need mobile numbers (5 credits per found phone).

### Recipe D — Account-based (ABM)

1. `POST /v1/companies` to build the account list (0.1/result). Optionally seed `lookalikeDomains` (max 5 domains or LinkedIn company URLs), and/or `account.employee` to find companies that even *have* the role you sell to.
2. Take the returned company `id` values and use them in People Search under `contact.company.latest` / `.current`.
3. Continue with Recipe A or B for emails.

### Suppression & deep pagination (Lists)

* `POST /v1/lists` with `{ "type": "people_id", "values": [ ...ids ] }` → returns a list `id`.
* Reference it: `"lists": { "people_id": { "exclude": ["<list-id>"] } }` (people endpoints) / `"lists": { "company_id": { "exclude": ["<list-id>"] } }` (Company Search). **Max 10 lists per request.**
* **Retrieve more than 10,000 records:** a single search pages through at most 10,000 (`page` × `size`) though `totalElements` is uncapped. For a 38,000-match search: pull the first 10,000 → add their ids to a list → re-run excluding that list → repeat.
* Lists are free, reusable and updatable: same `id` with `mode: "APPEND"` (default) or `"REPLACE"`. Max 10,000 values per list, 50 lists per day, **lists expire after 24 hours**.

## 6. Endpoint Reference

### 6.0 People Preview — `POST /v1/people/preview`

**Purpose:** run any People Search cheaply to validate filters and volume before committing credits. The recommended first call of every list-building workflow.
**Credits:** 1 per page, flat.
**Body:** identical to People Search — `account`, `contact`, `lists`, plus required `page` (zero-based) and `size` (1–100, default 25). `totalElements` is the full match count; up to 10,000 records retrievable via pagination.
**Response:** person `id` (real), first name + masked last name, title, headline, location, department/seniority, position history, full company object, `has_*` flags, `last_updated`. **No emails, no phones, `trackId: null`.**

### 6.1 People Search — `POST /v1/people`

**Purpose:** search 400M+ person profiles by contact and/or account filters. Returns full person + company data. **Does NOT return emails or phones.**
**Credits:** 0.5 per result.
**Body:** `{ "account": {...}, "contact": {...}, "lists": {...}, "page": 0, "size": 25 }` — `page` and `size` **required** (`size` 1–100, default 10).
**Response:** `content[]`, Spring-style pagination (`totalElements`, `totalPages`, `size`, `number`, `pageable`, `first`, `last`, `empty`, `numberOfElements`), and `trackId` (**single-use, 6h expiry**).
**Errors:** `404` no matches (treat as empty, not failure); `501` unsupported filter (e.g. `socialMediaFollower` on a non-LinkedIn platform).

```bash
curl -X POST 'https://api.ai-ark.com/api/developer-portal/v1/people' \
  -H 'X-TOKEN: {API_KEY}' -H 'Content-Type: application/json' \
  -d '{
    "contact": {
      "experience": { "latest": { "title": { "any": { "include": { "mode": "SMART", "content": ["marketing manager"] } } } } },
      "seniority": { "any": { "include": ["manager", "director"] } },
      "location": { "any": { "include": ["Germany"] } }
    },
    "account": {
      "industries": { "any": { "include": { "mode": "WORD", "content": ["software development"] } } },
      "employeeSize": { "type": "RANGE", "range": [ { "start": 50, "end": 200 } ] }
    },
    "page": 0, "size": 25
  }'
```

### 6.2 Company Search — `POST /v1/companies`

**Purpose:** search 70M+ company profiles by account filters — ideal for ABM account lists. Also **Lookalike Search** via `lookalikeDomains`.
**Credits:** 0.1 per result.
**Body:** `{ "lookalikeDomains": [...], "account": {...}, "lists": {...}, "page": 0, "size": 25 }`.

**Lookalike:** up to **5** company domains or LinkedIn company URLs, combinable with `account` filters:

```json
{ "lookalikeDomains": ["raisin.com", "https://www.linkedin.com/company/n26"],
  "account": { "location": { "any": { "include": ["Germany"] } } }, "page": 0, "size": 25 }
```

**Company-Search-only filter — `account.employee` (Job Role):** find **companies by the people they employ**.

```json
"account": { "employee": {
  "title": { "any": { "exclude": { "mode": "SMART", "content": ["manager"] } } },
  "seniority": { "any": { "include": ["c_suite", "vp"] } },
  "departmentAndFunction": { "any": { "include": ["software_development"] } }
} }
```

**Response:** companies with `id` (UUID) — use these in People Search `contact.company` (`latest`/`current`/`previous`). Resolving a domain or LinkedIn company URL to an ID works for universities too (needed for `education.school`).

### 6.3 Find Emails by Track ID — `POST /v1/people/email-finder`

**Credits:** 1 per found valid email, 0 for people with no valid email.
**Critical:** each `trackId` is used **exactly once** and **expires 6 hours** after the People Search response. A used/expired id returns `404`.
**Body:** `{ "trackId": "<uuid>", "webhook": "https://..." }` — both required, webhook must be HTTPS.
**Response:** `{ trackId, statistics: { total, found }, state: "PENDING", webhook: { state, retry }, description }`.
**Concurrency (per token, per service):** max **500** in-flight submissions (`400 too many pending requests`); **10** processed in parallel. Auto-refund of undelivered charged jobs after up to 10h.

Sub-endpoints (free): `GET .../{trackId}/statistics` (poll to `DONE`; `403` if STUCK_*-refunded, `404` unknown/expired) · `GET .../{trackId}/inquiries?page=0&size=100` (readable while running; items carry `refId`, `state`, `input`, `output`) · `GET /v1/people/email-finder/submissions?state=&fullyRefunded=&page=&size=&sort=` · `PATCH .../{trackId}/notify` (re-send webhook).

### 6.4 Export People with Email — `POST /v1/people/export`

**Purpose:** one call = People Search + email finding, async, up to **10,000** people.
**Credits:** 0.5 per exported person (everyone, found or not) + 0.5 per found valid email.
**Body:** People Search filters + required `page`, `size` (1–10000, total export size) and `webhook`. `size` > 10,000 → `400 pagination limit exceeded`.
**Sub-endpoints (free):** `GET .../{trackId}/statistics` · `GET .../{trackId}/inquiries?page=0&size=100` (**`409 track id in progress`** until done) · `GET /v1/people/export/submissions` · `PATCH .../{trackId}/notify`.

### 6.5 Export Single Person with Email — `POST /v1/people/export/single` (v1) & `POST /v2/people/export/single` (v2)

**Credits:** 1 if a valid email is found, **0 if not**.
**Body:** `{ "id": "<ai-ark person id>" }` or `{ "url": "<linkedin profile url>" }` — at least one; `id` is looked up first. Both empty → `400`.
**v1 vs v2:** identical except not-found: v1 `404`; **v2 always returns HTTP 200** with `{ status, error, data }` (`data: null`) — recommended inside **Clay**. v2 adds the `X-Credit` header.

### 6.6 Mobile Phone Finder — `POST /v1/people/mobile-phone-finder` (v1) & `/v2/...` (v2)

**Credits:** 5 per found number, 0 if none.
**Body:** `{ "linkedin": "<full profile url>" }` **or** `{ "domain": "acme.com", "name": "Jane Doe" }` (domain and name together).
**Response:** `{ "id": ..., "linkedin": ..., "data": [ [ "+13152468945", ... ] ] }` — inner array can hold multiple numbers ordered by confidence, E.164.
**v1 vs v2:** v1 `404` when none; v2 HTTP 200 with `data: null` (Clay) + `X-Credit`.

### 6.7 Reverse People Lookup — `POST /v1/people/reverse-lookup`

Identify a person from an **email address**. **Credits:** 0.5 per request. **Body:** `{ "search": "jane@acme.com" }`. `404` = not in the database.

### 6.8 Personality Analysis — `POST /v1/people/analysis`

**Credits:** 4. **Body:** `{ "url": "https://www.linkedin.com/in/..." }`.
**Response:** `{ model, source, score, selling {...}, hiring {...}, assessments {...}, status, success }` — `selling`/`hiring` carry per-field email advice (subject, salutation, tone, length, bullets, closing), communication do/don't lists and `keyTraits`; `assessments` carries `archetype`, `ocean` and `disc` scores. `404 profile not found`.

### 6.9 Create or Update a List — `POST /v1/lists`

**Credits:** free. **Body:** `{ "id": "<optional uuid>", "type": "people_id" | "company_id", "values": [ ...≤10000 ], "mode": "APPEND" | "REPLACE" }`.
No `id` → new list. Existing `id` → update. Unknown `id` → new list created.
**Limits:** 50 lists/day, 10,000 values/list, **expire after 24 hours**.
**Usage:** `"lists": { "people_id": { "exclude": ["<list-id>"] } }` / `{ "company_id": { ... } }`, up to **10 lists per request**.

### 6.10 Fetch Your Credits — `GET /v1/payments/credits`

Free. `{ "total": 100 }`. Check before large jobs.

## 7. Complete Filter Reference (People Search, Preview, Export People; `account.*` also in Company Search)

### 7.1 Match modes, any/all, limits

Most filters: `{ "any": { "include": [...], "exclude": [...] }, "all": { "include": [...], "exclude": [...] } }`.
`any` = OR (broader), `all` = AND (narrower). A search cannot consist of `exclude` filters only.

Text filters wrap values with a match mode: `{ "mode": "SMART" | "WORD" | "STRICT", "content": ["..."] }`:
* `SMART` **(default)** — related concepts: `creative director` also finds `art director`, `head of creative`.
* `WORD` — exact phrase, extra words allowed: matches `associate creative director`, not `art director`.
* `STRICT` — exact characters only.

Plain-array filters (no match mode): domain, linkedin, socialMediaLink, phoneNumber, location, socialMedia, type, naics, technology (legacy), seniority, departmentAndFunction, profileBadge, company IDs, education.school IDs, account.language.

**Limits:** max **300 values** per include/exclude array; a search pages through at most **10,000 records** (`totalElements` is uncapped — use Lists).

**Range filters:** `{ "type": "RANGE", "range": [ { "start": X, "end": Y }, ... ] }` — an **array of bands, OR'd**. Omit `end` for "X+", omit `start` for "less than Y". (`foundedYear` takes a single `range` object; `foundedYear`/`revenue` also accept `type: "ALL"` / `"NONE"`.)

### 7.2 `account` filters (company attributes)

| Filter | Values / shape | Notes |
|---|---|---|
| `domain` | plain arrays | Website domain, case-insensitive; bare domain recommended. |
| `linkedin` | plain arrays | Company LinkedIn URL — **full URL**, not the slug. |
| `url` | match modes | Most tolerant identifier: bare domain, `www.`, full URL, or LinkedIn company URL. |
| `name` | match modes | Can hit unrelated same-name companies — prefer resolving to IDs. |
| `socialMediaLink` | plain arrays | A specific company social profile URL. |
| `phoneNumber` | plain arrays | E.164, e.g. `+18885335659`. |
| `industries` | match modes | 919 values — CSV: https://ai-ark.com/static/industries.csv?v=1 |
| `location` | plain arrays | Office locations — matches **any office**, not just HQ. Countries, states, cities, metros, regions. |
| `geoLocation` | `{ "position": { "lat": 53.5511, "lng": 9.9937 }, "radius": 50, "unit": "km" }` | Radius search (`km` or `mi`). |
| `productAndServices` | match modes | What the company offers, from public positioning. |
| `socialMedia` | plain arrays | `FACEBOOK`, `INSTAGRAM`, `TWITTER`, `LINKEDIN`. |
| `type` | plain arrays | `PRIVATELY_HELD`, `SELF_OWNED`, `SELF_EMPLOYED`, `PARTNERSHIP`, `PUBLIC_COMPANY`, `NON_PROFIT`, `EDUCATIONAL`, `GOVERNMENT_AGENCY`. |
| `foundedYear` | `{ "type": "RANGE", "range": { "start": 2015, "end": 2022 } }` | Also `ALL` / `NONE`. |
| `employeeSize` | `{ "type": "RANGE", "range": [ { "start": 51, "end": 200 } ] }` | Headcount; bands OR'd. |
| `retailSize` | range array | Physical locations worldwide. |
| `revenue` | range array | Annual revenue USD; `ALL` / `NONE` supported. |
| `funding` | see below | Funding history. |
| `language` | plain arrays + `range` | Languages the company operates in (48 values). `range` filters HOW MANY. |
| `keyword` | sources shape | Sources (5): `NAME`, `KEYWORD`, `SEO`, `DESCRIPTION`, `INDUSTRY`. |
| `metric` | see below | Employees by department + headcount growth. |
| `technologies` | match modes | **Use this one.** 16,000+ values — CSV: https://ai-ark.com/static/technologies.csv?v=1 |
| `technology` | plain arrays | Legacy, no match modes. Prefer `technologies`. |
| `naics` | plain arrays | e.g. `454110`. |
| `employee` | **Company Search only** | Job Role filter — see 6.2. |

`funding` — all sub-fields optional:

```json
"funding": {
  "type": ["SEED", "SERIES_A"],
  "totalAmount": { "start": 1000000, "end": 20000000 },
  "lastAmount":  { "start": 500000,  "end": 2000000 },
  "duration":    { "start": "1620847800000", "end": "1747168200000" }
}
```

`type` — 30 round types (`PRE_SEED`, `SEED`, `SERIES_A`…`SERIES_J`, `VENTURE_ROUND`, `ANGEL`, `PRIVATE_EQUITY`, `DEBT_FINANCING`, `CONVERTIBLE_NOTE`, `GRANT`, `CORPORATE_ROUND`, `EQUITY_CROWDFUNDING`, `PRODUCT_CROWDFUNDING`, `SECONDARY_MARKET`, `POST_IPO_EQUITY`, `POST_IPO_DEBT`, `POST_IPO_SECONDARY`, `NON_EQUITY_ASSISTANCE`, `INITIAL_COIN_OFFERING`, `UNDISCLOSED`, `SERIES_UNKNOWN`, `FUNDING_ROUND`). `duration` = date of the most recent round as an **epoch-milliseconds string range**.

`metric` — department-level headcount. `function` takes one of 27 values: `sales`, `marketing`, `engineering`, `finance`, `human_resources`, `information_technology`, `operations`, `business_development`, `customer_success_and_support`, `product_management`, `accounting`, `legal`, `consulting`, `education`, `research`, `purchasing`, `real_estate`, `media_and_communication`, `quality_assurance`, `arts_and_design`, `healthcare_services`, `entrepreneurship`, `community_and_social_services`, `administrative`, `military_and_protective_services`, `program_and_project_management`, `support`.

```json
"metric": {
  "employee": [ { "function": ["engineering"], "start": 10, "end": 50 } ],
  "growth":   [ { "function": ["marketing"], "start": 10, "end": 15, "timeFrame": "SIX" } ]
}
```

`growth` is a **percentage** change; `timeFrame` in months: `ONE`, `THREE`, `SIX`, `TWELVE`, `TWENTY_FOUR`.

`keyword` (account):

```json
"keyword": { "any": { "include": {
  "sources": [ { "mode": "SMART", "source": "DESCRIPTION" }, { "mode": "SMART", "source": "SEO" } ],
  "content": ["carbon accounting"]
} } }
```

### 7.3 `contact` filters (person attributes)

| Filter | Values / shape | Notes |
|---|---|---|
| `fullName` | match modes | Combine with `contact.company` or `account.domain` to disambiguate. |
| `linkedin` | plain arrays | Person's LinkedIn profile URL (**full URL**). |
| `socialMediaLink` | plain arrays | A specific personal social profile URL. |
| `company` | company **IDs (UUIDs)**, scoped | `{ "latest": {...}, "current": {...}, "previous": {...} }`. `latest` = primary active role; `current` = ALL active roles; `previous` = past employers. Max 300 IDs. |
| `experience` | see below | Job titles + tenure by scope. |
| `seniority` | plain arrays | `founder`, `owner`, `partner`, `c_suite`, `vp`, `director`, `head`, `manager`, `senior`, `mid-level`, `entry`, `intern`. Based on the **current** role. |
| `departmentAndFunction` | plain arrays | **592 values** — CSV: https://ai-ark.com/static/departments-and-functions.csv?v=2 |
| `location` | plain arrays | Where the person **lives**. For the employer use `account.location`. |
| `language` | **match modes** + `range` | Unlike `account.language`. `range` = number of languages spoken. |
| `skill` | match modes | With `all`, require several at once. |
| `certification` | match modes | e.g. `pmp`, `aws certified solutions architect`. |
| `education` | see below | School (by company ID), degree, field of study, study period. |
| `keyword` | sources shape | **Max 5 sources per request.** 15 sources: `HEADLINE`, `SUMMARY`, `SKILL`, `CERTIFICATION`, `COURSE`, `PROJECTS`, `PUBLICATION`, `PATENT`, `AWARD`, `ORGANIZATION`, `VOLUNTEERING`, `TEST_SCORE`, `WORK_HISTORY_DESCRIPTION`, `EDUCATION_DESCRIPTION`, `LANGUAGE_SKILL`. |
| `socialMedia` | plain arrays | `FACEBOOK`, `INSTAGRAM`, `TWITTER`, `LINKEDIN`. |
| `profileBadge` | plain arrays | `VERIFIED`, `PREMIUM`, `OPEN_TO_WORK`, `INFLUENCER`, `CREATOR`, `HIRING`. |
| `socialMediaFollower` | see below | LinkedIn follower/connection counts. **LinkedIn only** — others → `501`. |

`contact.experience` — three scopes: `latest` (primary active role), `current` (all active roles — catches advisors, board members, multi-role founders), `previous` (past roles only).

```json
"experience": {
  "latest": {
    "title": { "any": { "include": { "mode": "SMART", "content": ["creative director"] } } },
    "duration": {
      "latestCompany": { "min": { "year": 1, "month": 0 }, "max": { "year": 4, "month": 0 } },
      "latestJob":     { "min": { "year": 0, "month": 0 }, "max": { "year": 0, "month": 6 } },
      "total":         { "min": { "year": 3, "month": 0 }, "max": { "year": 8, "month": 0 } }
    }
  }
}
```

`latestJob.max: {year: 0, month: 6}` = **new in role**, a strong outreach trigger.

`contact.education`:

```json
"education": {
  "school":       { "any": { "include": ["49c9a269-b00e-28ac-eeb6-f74d3fd32a00"] } },
  "degree":       { "any": { "include": { "mode": "SMART", "content": ["mba"] } } },
  "fieldOfStudy": { "any": { "include": { "mode": "SMART", "content": ["computer science"] } } },
  "date":         { "start": 2011, "end": 2015, "present": false }
}
```

`school` takes **AI Ark company IDs** (universities are companies — resolve via Company Search).

`contact.socialMediaFollower` — LinkedIn only:

```json
"socialMediaFollower": { "linkedin": {
  "followers":   { "type": "RANGE", "range": [ { "start": 5000, "end": 10000 }, { "start": 30000 } ] },
  "connections": { "type": "RANGE", "range": [ { "start": 1500, "end": 4200 } ] }
} }
```

In responses these appear under `statistics.network.followers_count` / `.connections_count` (absence ≠ zero).

### 7.4 `lists` filter

`{ "people_id": { "exclude": ["<list-id>"] } }` on people endpoints / `{ "company_id": { "exclude": [...] } }` on Company Search. Up to **10 lists per request**, 10,000 items each.

## 8. Accepted Enum Values (quick reference)

* **Seniority (12):** `founder`, `owner`, `partner`, `c_suite`, `vp`, `director`, `head`, `manager`, `senior`, `mid-level`, `entry`, `intern`
* **Profile badge (6):** `VERIFIED`, `PREMIUM`, `OPEN_TO_WORK`, `INFLUENCER`, `CREATOR`, `HIRING`
* **Company type (8):** `PRIVATELY_HELD`, `SELF_OWNED`, `SELF_EMPLOYED`, `PARTNERSHIP`, `PUBLIC_COMPANY`, `NON_PROFIT`, `EDUCATIONAL`, `GOVERNMENT_AGENCY`
* **Match modes:** `SMART`, `WORD`, `STRICT`
* **Social media:** `FACEBOOK`, `INSTAGRAM`, `TWITTER`, `LINKEDIN`
* **Contact keyword sources (15, max 5/request):** `HEADLINE`, `SUMMARY`, `SKILL`, `CERTIFICATION`, `COURSE`, `PROJECTS`, `PUBLICATION`, `PATENT`, `AWARD`, `ORGANIZATION`, `VOLUNTEERING`, `TEST_SCORE`, `WORK_HISTORY_DESCRIPTION`, `EDUCATION_DESCRIPTION`, `LANGUAGE_SKILL`
* **Account keyword sources (5):** `NAME`, `KEYWORD`, `SEO`, `DESCRIPTION`, `INDUSTRY`
* **Headcount-growth timeframes:** `ONE`, `THREE`, `SIX`, `TWELVE`, `TWENTY_FOUR`
* **Metric department functions (27):** see §7.2
* **Funding round types (30):** see §7.2
* **Languages (48):** english, spanish, french, portuguese, german, dutch, italian, chinese, turkish, polish, russian, swedish, arabic, indonesian, danish, czech, norwegian, japanese, korean, romanian, ukrainian, thai, hindi, malay, tagalog, vietnamese, finnish, persian, greek, hungarian, bengali, marathi, telugu, panjabi, serbian, slovak, croatian, lithuanian, latvian, albanian, icelandic, armenian, bosnian, tamil, javanese, malayalam, kannada, burmese. (`contact.language` wraps values in a match mode; `account.language` takes plain arrays.)
* **Industries:** 919 values — https://ai-ark.com/static/industries.csv?v=1
* **Technologies:** 16,000+ — https://ai-ark.com/static/technologies.csv?v=1
* **Departments & functions:** 592 — https://ai-ark.com/static/departments-and-functions.csv?v=2
* **Locations:** free-form and forgiving — countries, states, plain city names, metro areas, regions.

## 9. Response Object Skeletons (for writing parsers)

**Person object** (People Search / Export results / Export Single / Reverse Lookup; Preview returns a reduced + masked variant plus `has_*` flags):

```
id                      — AI Ark person UUID (use in Export Single, Lists)
identifier              — LinkedIn slug
profile { first_name, last_name, full_name, headline, title, picture.source, background.source, birth_date, summary }
link { linkedin, twitter, github, facebook }
location { country, state, city, position, default, short }
languages { primary_locale {country, language}, supported_locales[], profile_languages }
industry                — person's industry label
educations[] { school {id, name, logo, url}, degree_name, field_of_study, grade, date {start, end} }
certifications[] { name, authority, url, license_number, display_source, company, date }
organizations[] { name, position, date }
volunteer_experiences[] { role, company, cause, description, date }
position_groups[] { company {id, name, logo, url, employees {start, end}}, date {start, end},
                    profile_positions[] { company, description, title, employment_type, location, date } }
skills[]                — strings
member_badges { creator, hiring, open_to_work, premium, verified, influencer }
company { id, summary { name, legal_name, description, overview, seo, founded_year, type, industry,
                        staff { total, range {start, end} }, logo.source },
          link { website, domain, domain_ltd, linkedin, facebook, twitter, crunchbase },
          financial { revenue.annual {start, end, amount}, funding {...}, ipo {...},
                      exit {...}, acquisition {...}, investment {...}, diversity_investment {...},
                      aberdeen.it_spend },
          location { headquarter {...}, locations[] },
          technologies[] { name, category }, industries[], keywords[], hashtags[], languages[],
          sub_organizations[], sic[], naics[], last_updated }
department { departments[], sub_departments[], functions[], seniority }
statistics { network { followers_count, connections_count } }     — may be absent
email { state: "PROCESSING"|"DONE", output: [ ...email objects, §3 ] }   — export endpoints only
last_updated
```

**Pagination envelope** (Spring style): `content[]`, `totalElements`, `totalPages`, `size`, `number`, `numberOfElements`, `pageable {...}`, `sort`, `first`, `last`, `empty` — plus `trackId` on People Search.

## 10. Webhooks (async jobs: Find Emails by Track ID & Export People)

1. Call the endpoint with a `webhook` field (HTTPS callback URL).
2. The API responds immediately with a `trackId` and `state: "PENDING"`.
3. On completion a `POST` with the **full results** is sent to your URL.

**Payload:** top level `trackId`, `state: "DONE"`, `description`, `statistics { total, found }`, `data[]`. Find Emails items: `{ refId, state, input { firstname, lastname, domain }, output: [ ...email objects ] }`. Export People items: the full person object including `email { state, output }`.

**Delivery:** retried automatically; a webhook may be delivered **more than once** — deduplicate by `trackId`. Respond `200 OK` quickly.

**Re-send — `PATCH .../{trackId}/notify`** (free): inspect the returned `WebhookDeliveryResult`, not the HTTP status. `delivered: true` = your endpoint accepted. `delivered: false, fault: "WEBHOOK"` = your endpoint failed. `delivered: false, fault: "SERVICE"` = AI Ark side. HTTP `403` = the submission was auto-refunded for non-delivery — resubmit.

## 11. Job States, Errors & Rate Limits

**Async job states:** `PENDING` → processing → `DONE`. Submission history: `PENDING` → `SETTLED`.

| Code | Meaning | Agent action |
|---|---|---|
| 400 | Invalid filters/fields, `id and url cannot be both empty`, `both domain and name are required`, `pagination limit exceeded` (>10,000), `too many pending requests` (500 in-flight), list limits | Fix the payload; for the pending cap, wait and retry. |
| 401 | Missing/invalid `X-TOKEN` | Check the API key. |
| 402 | Not enough balance | Stop; check credits; ask the user to top up. |
| 403 | trackId auto-refunded (`4031013` / `4031014`) and not retrievable | Resubmit; check `/submissions`. |
| 404 | No data / not found; for trackId endpoints "not found, expired, or already used" | Treat as "no result". Use v2 endpoints in Clay. |
| 409 | Export results not ready (**Export People only**) | Poll statistics until `DONE`. |
| 429 | Rate limit exceeded | Back off (5 req/s per token). |
| 500 | Unexpected server error | Retry with backoff. |
| 501 | Filter not supported (e.g. `socialMediaFollower` on a non-LinkedIn platform) | Remove the filter. |

**Async submissions:** max 500 in flight per token **per service**, 10 processed in parallel.

## 12. Rules of Thumb for Agents

1. **Preview first** (1 credit/page) before spending per-result credits; size the job from `totalElements` and use `has_*` flags to decide what is worth enriching.
2. **Estimate cost before big calls** and check credits for anything over ~100 credits.
3. **Never re-verify AI Ark emails** — BounceBan-verified in real time. Segment on `domainType` and `generic`.
4. **Use the `trackId` immediately** — single use, 6-hour expiry.
5. **Prefer Export People with Email** for bulk; prefer **v2** endpoints inside Clay.
6. **Deduplicate with Lists** (free): maintain a `people_id` exclusion list; rebuild daily (24h expiry). Lists are also how you page past 10,000 results.
7. **Company targeting:** Company Search → company `id`s → People Search `contact.company`.
8. **Mine the intent signals:** `metric.growth`, `funding.duration`, `experience.duration.latestJob` max 6 months, `profileBadge: HIRING`.
9. **Handle refunds automatically:** on `403` from a trackId endpoint, resubmit; check `/submissions` before assuming credits were lost.
10. **Errors are often "no result":** a `404` from sync endpoints means not found, and cost nothing.
