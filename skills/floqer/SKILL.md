---
name: floqer
description: Floqer GTM workflow and enrichment platform — the API, actions, sources, and build loop. Use when building a Floqer workflow.
---

# Floqer — GTM Workflow & Enrichment Platform (Skill)

> **What Floqer is:** a spreadsheet-shaped GTM automation platform. You pull data **in** (Sources), process every row through a chain of **Actions** (enrich, score, format, route), and push results **out** to a CRM / sequencer / sheet. Think Clay, with a clean public API designed to be driven by an agent.
>
> **Floqer is optional.** Use it only if you have a Floqer account and key.
>
> **This skill** lets you build workflows, run enrichments, and operate the product end-to-end via the Floqer Public API. The authoritative spec lives in `reference/` (Floqer maintains those files; re-scrape periodically).

---

## 0. Credentials & Setup

- **Base URL:** `https://api.floqer.com`
- **Auth:** Bearer token on every request. Key starts with `floq_`. Generate it in the Floqer dashboard → **Settings**. Full org access.
  ```
  Authorization: Bearer floq_YOUR_API_KEY
  ```
- **Where the key lives:** `python3 gtm.py set-key FLOQER_API_KEY` (read back via `gtm.cred()`), or export it, or `skills/floqer/.env` as `FLOQER_API_KEY=floq_...` (gitignored). `floqer_client.py` checks env → `.env` → `gtm.cred()`.
- **Rate limits:** 200 req/min, 10,000 req/day per key. `429` returns `retryAfter` (seconds) — back off exactly that long.
- **Docs (authoritative, re-scrapeable):**
  - `https://floqer.com/docs/concepts.txt` — the mental model (READ FIRST; bundled in `reference/concepts.txt`)
  - `https://floqer.com/docs/action-catalog.txt` — every action + needs/produces/credits (`reference/action-catalog.txt`)
  - `https://floqer.com/docs/source-catalog.txt` — every source (`reference/source-catalog.txt`)
  - `https://floqer.com/docs/action-detail/{action_id}.txt` — per-action config guide (key ones bundled in `reference/action-detail/`)
  - `https://floqer.com/docs/source-detail/{source_id}.txt` — per-source body shape + filter catalogue
  - `https://floqer.com/docs/reference` — full interactive API reference
  - `https://floqer.com/docs/llms-full.txt` — everything in one file (~50KB)

---

## 1. The Mental Model (memorize this)

```
Workflow ─┬─ Main Sheet  (sheet_id === workflow_id)   ← created automatically
          ├─ Child Sheet (own UUID)                   ← create for one-to-many fan-out
          └─ ...
Each Sheet ─┬─ Inputs   (columns you feed in)
            ├─ Actions  (the chain — each runs on every row)
            ├─ Rows     (the records)
            └─ Settings (auto_run, cache_enabled, cache_since)

Sources  ── sit ALONGSIDE workflows. Pull external records in, then Sync into a workflow.
```

- **A workflow is a container for sheets.** Every operation (inputs, actions, rows, runs) happens **at the sheet level**.
- **Main sheet shortcut:** the main sheet's ID **equals the workflow ID**. To hit the main sheet, pass the workflow ID as *both* `{workflow_id}` and `{sheet_id}`.
- **Sheets are independent peers** — no parent/child hierarchy. Child sheets exist mainly to expand a `structured_array` (e.g. one company → many employees) into rows via `push_data_to_sheet`.

### Two identifiers for actions (don't confuse them)
| Term | What | Example |
|------|------|---------|
| `action_id` | Template ID, same across all workflows. From the catalog. | `enrich_company_linkedin_profile` |
| `action_instance_id` | The instance in *your* sheet, auto-generated, suffixed `_1`, `_2`. | `enrich_company_linkedin_profile_1` |

You reference outputs by **instance** ID: `{{enrich_company_linkedin_profile_1.company_name}}`.

### Data types
- **Scalars:** `string`, `url`, `email`, `number`, `boolean`. Used for inputs and outputs.
- **Code:** `js_expression` — a single JS expression run by the `format_data_using_js_expression` action (multi-line → wrap in an IIFE).
- **Nested (outputs only):**
  - `raw_array` — unstructured list (e.g. work experiences). Pass whole; can't expand to rows.
  - `json` — unstructured object (e.g. HQ block). Pass whole; can't expand to rows.
  - `structured_array` — typed list of records (e.g. `list_of_employees`). **Can** be referenced column-by-column **or** fanned out to a new sheet.

### Variable references — the wiring syntax
```
{{input.linkedin_url}}                              # an input column
{{enrich_company_linkedin_profile_1.company_name}}  # a scalar action output
{{get_employees..._1.list_of_employees.first_name}} # 3-segment: one column of a structured_array
"Research {{input.company_name}} at {{enrich_1.company_website}}"  # mix static + refs
```
**Rules:**
- You can only reference **upstream** actions (downstream refs fail).
- References resolve **per-row at runtime**.
- **`json`/`object` outputs are NOT dotted-addressable** — `{{lookup_1.record.full_name}}` resolves empty. The substitution layer only reaches *top-level* keys. To pluck a nested field, use the bracket form inside a `format_data_using_js_expression`: `{{lookup_1.record}}?.["full_name"]`.
- Every Add Inputs / Add Action response hands you the ready-to-paste `reference` string — copy it verbatim.

### ⚠️ The input `name` gotcha
The `name` you set at create time is the **literal JSON key** `Add Rows` expects — **case- and whitespace-sensitive**. The reference token may look snake_cased (`{{input.company_name}}`) even though the input was created as `"Company Name"`. **Always `List Inputs` and use the `name` value verbatim** as the row key. Mismatch → `unknown_field` rejection. Inputs **cannot be renamed** (delete + re-add, which breaks references).

---

## 2. The Build Loop (canonical flow)

```
Create Workflow ─► Add Inputs ─► Add Actions ─► Configure each Action (wire refs)
   ─► Add Rows (10) ─► Run first_10 ─► List Rows (poll) ─► inspect ─► tweak ─► repeat
   ─► expand 100 → 1,000 → run-all  (ONLY once output is verified)
```

**Discovering actions:** there is **no API endpoint** that lists action templates. The catalog files are authoritative. Load `reference/action-catalog.txt` into context, match your available data types against each action's **Needs**, pick the `action_id`, then read `reference/action-detail/{action_id}.txt` (or fetch live) for config guidance before wiring it.

### 💸 Cost safety — the single biggest risk
Every action call burns credits. **5 actions × 10,000 rows = 50,000 billable calls.** Never `run-all` on a fresh/edited workflow.
1. Run **10–50** rows first, verify output in `List Rows`.
2. Expand in batches: **100 → 1,000 → all**.
3. `run-all` is full-cost — treat it as the last step, not a test.

---

## 3. Endpoint Reference (38 endpoints)

All paths are under `https://api.floqer.com`. `{sheet_id}` = `{workflow_id}` for the main sheet.

### User / Identity / Org Knowledge
| Method | Path | Purpose |
|--------|------|---------|
| GET | `/api/v1/user/` | **Bootstrap call.** Who the key belongs to (email, name, role, org_id) + org member roster. No scope needed. |
| GET | `/api/v1/user/knowledge` | Read the org's free-form knowledge file (`{content, exists, updated_at}`; `exists:false` not 404). |
| PUT | `/api/v1/user/knowledge` | Write/replace the knowledge file (idempotent full replace, max 256 KB; empty string clears). |

### Workflows
| Method | Path | Purpose |
|--------|------|---------|
| POST | `/api/v1/workflows/` | Create workflow (+ auto-creates main sheet). Body: `{name, ...}`. |
| GET | `/api/v1/workflows/` | List all accessible workflows + metadata. |
| GET | `/api/v1/workflows/{workflow_id}` | **Workflow Overview** — metadata, sharing, every sheet w/ settings + webhook URLs. `sheets[0]` is main. |
| DELETE | `/api/v1/workflows/{workflow_id}` | Delete workflow (removes main sheet too). |

### Sheets
| Method | Path | Purpose |
|--------|------|---------|
| POST | `/api/v1/workflows/{workflow_id}/sheets` | Create child sheet. Body: `{name, auto_run?, cache_enabled?, cache_since?}`. |
| DELETE | `/api/v1/workflows/{workflow_id}/sheets/{sheet_id}` | Delete a **child** sheet (main sheet → 400; delete the workflow instead). |

### Inputs
| Method | Path | Purpose |
|--------|------|---------|
| GET | `.../sheets/{sheet_id}/inputs` | List input fields + reference strings. |
| POST | `.../sheets/{sheet_id}/inputs` | Add inputs. Body is a **bare JSON array** `[{name, type, description?}]`. Types: `string｜url｜email｜number`. |
| DELETE | `.../sheets/{sheet_id}/inputs/{field_name}` | Delete an input (breaks refs to it). |

### Actions
| Method | Path | Purpose |
|--------|------|---------|
| POST | `.../actions/add` | Add action. Body: `{action_id, after?, name?}`. Appends to end unless `after`. Returns `action_instance_id`, inputs to configure, outputs w/ refs. |
| PATCH | `.../actions/{aid}` | **Configure Action.** Body: `{inputs?, run_if?, continue_workflow_on_failure?, note?}`. Send only what you set. ⚠️ **invalidates cache** for this + all downstream cells. |
| GET | `.../actions/graph` | Full action chain as a graph (nodes w/ inputs, `run_if`, `note`, `next`). |
| GET | `.../actions/{aid}` | Get one action's config. |
| DELETE | `.../actions/{aid}` | Remove action (invalidates cache downstream). |
| POST | `.../actions/{aid}/options/{field_name}` | **Get Action Field Options** — resolve a dynamic dropdown. Body: `{context?: {...}}`. Returns `[{value,label}]`. |
| GET | `.../actions/{aid}/outputs` | Get an action's output schema. |
| PATCH | `.../actions/{aid}/name` | Rename (display only; **no** cache invalidation). Body: `{name}`. |
| PATCH | `.../actions/{aid}/move` | Reorder. Body: `{after}` (`"input"` = start, or an instance id). |
| PATCH | `.../actions/{aid}/waterfall/{field_name}` | Reorder waterfall providers. Body: `{providers: [...]}`. |
| POST | `.../actions/{aid}/notes` | Upsert a note (one per action). Body: `{note}`. |

### Rows / Running
| Method | Path | Purpose |
|--------|------|---------|
| POST | `.../rows` | **Add Rows.** Body: `{rows: [{...}], run_after_add?: "none"｜"first_10"｜"all"}`. Max 1,000/call. Partial success: returns `row_ids` + `rejected`. |
| POST | `.../run` | Run rows. Body: `{row_ids: [...]}` **or** `{first_10: true}`. Async. |
| POST | `.../run-all` | Run **every** row (no body). ⚠️ full credit cost. |
| POST | `.../actions/{aid}/run` | Re-run **one** action. Body: `{row_ids: [...], run_next_action?: bool}`. `row_ids:[]` = all rows. |
| POST | `.../rows/list` | **List Rows** (poll results). Body (all optional): `{row_ids?, page_no?, page_size?, filters?, status_filters?, created_at?}`. |
| POST | `.../rows/delete` | Delete specific rows. |
| POST | `.../rows/delete-all` | Delete all rows on a sheet. |

### Sources (data in)
| Method | Path | Purpose |
|--------|------|---------|
| GET | `/api/v1/sources/` | List created sources (newest first). Carries `source_instance_id`, `source_id`, `status`, `lead_count`. |
| POST | `/api/v1/sources/{source_id}/preview` | Preview up to 100 records that *would* import — no creation. (`{source_id}` = type slug.) |
| POST | `/api/v1/sources/{source_id}` | **Create** source (imports immediately if `pull_existing`). Returns `source_instance_id`. |
| POST | `/api/v1/sources/{source_id}/options/{field_name}` | Resolve source dynamic dropdowns (HubSpot lists/props, SF objects, sheet tabs, etc.). |
| GET | `/api/v1/sources/{source_instance_id}/data` | Paginated imported rows. `?page_no=&page_size=` (max 200). |
| POST | `/api/v1/sources/{source_instance_id}/sync` | **Connect source → workflow.** Body: `{workflow_id, field_mapping, push_existing?, run?}`. |
| PATCH | `/api/v1/sources/{source_instance_id}/status` | Pause/resume. Body: `{status: "active"｜"paused"}`. |

---

## 4. Per-cell Execution & Status

A **cell** = one action's run on one row. Each cell is independent: `queued → running → complete ｜ failed`. A row's run is a set of cells (one per action). Runs are **async** — submit, then poll `List Rows`.

In `List Rows` each cell has:
- `status` — `queued`/`running`/`complete`/`failed`.
- `outputs` — inline when small; or `outputs_ref` (a URL) when large (LinkedIn scrapes, enrichment blobs) — fetch that URL with your API key.
- `error` — on failed cells.
- Row-level `row_status` settles on `complete` or `has_failures` — **poll until then.**

`List Rows` browse-mode filters (mutually exclusive with `row_ids`):
- `filters` — input-column value filters.
- `status_filters` — per-action cell-status `is`/`is_not`.
- `created_at` — `{operator, values}` time filter.

---

## 5. Caching (what makes iteration affordable)

Cached **per cell**. `cache_enabled` default **on** per sheet. A cell re-runs **free** if its **resolved inputs exactly match** a prior run within the cache window.

- **Cache key = resolved inputs (after ref substitution + static params like prompt/model/provider) + entry newer than `cache_since`.** A single whitespace difference = cache miss.
- **Invalidated by:** any action config change (even whitespace), changed upstream output, advancing `cache_since`, brand-new cells.
- **Iteration cost:** "run 10 → tweak action 3's prompt → run 10" → actions 1-2 hit cache (free), action 3 re-bills all 10, downstream re-bills only where action 3's output changed. **Budget for worst case (every downstream re-bills); treat hits as a bonus.**
- **`cache_enabled: false`** (via Update Workflow) → every run bills in full. Use for high-temperature generative actions you want to re-sample.
- **`cache_since`** (YYYY-MM-DD UTC) → only entries after it are valid; advancing it bulk-invalidates.

---

## 6. Action Catalog (62 actions) — quick map

Match your data's types to an action's **Needs**. Full needs/produces/credits in `reference/action-catalog.txt`; per-action config in `reference/action-detail/{id}.txt`.

**AI / Research**
- `llm_models` — AI Generate Content (OpenAI/Anthropic/Google/Groq/DeepSeek/Perplexity). Needs `model`, `prompt`. → `generated_content`.
- `llm_web_agents` — Web Agent (prompt-driven live-web research w/ citations). Needs `select_a_model`, `mission`.
- `ai_web_navigator` — Web Pilot (step-by-step browser: clicks/forms/multi-page). 0 credits.
- `scrape_web_page_using_firecrawl` — Scrape Web Page Content (0.1).
- `get_fireflies_meeting_transcription` — Fireflies transcript lookup (PREREQ: Fireflies).

**Account (company) enrichment**
- `floqer_company_firmographics` (1cr) — cheapest firmographics + revenue range. ⚠️ US/UK-skewed; cross-check revenue for small/non-US-UK cos.
- `company_enrich_using_people_data_labs` (5cr) — firmographics + workforce dynamics + corporate structure.
- `store_leads_enrich_company` (0cr) — e-commerce store enrich by URL.
- `company_tech_stack_floqer` (1) / `..._using_their_stack` (0.3, precise + JD signal) / `..._from_builtwith` (2, broadest) — technographics.
- `enrich_company_linkedin_profile` (0.2) — scrape company LI profile.
- `get_employees_by_company_using_floqer_native` (0.005/emp) / `..._apollo` (1.4/100) / `..._sales_navigator` (25/page) — find employees → `structured_array`.
- `company_headcount_distribution_by_country` / `..._by_job_role` (1) — headcount breakdowns.
- `website_traffic_using_semrush` (1).

**Person enrichment**
- `enrich_person_linkedin_profile` (0.2) — scrape person LI.
- `person_enrich_by_floqer` (1) / `..._using_apollo` (1.4-8.4) / `..._using_people_data_labs` (5).
- `person_work_email_waterfall` (0.1-10) — **Find Work Email** (ordered provider waterfall; see §8).
- `personal_email_by_linkedin_url_waterfall` (1-5), `personal_phone_number_by_linkedin_url_waterfall` (0.1-23).
- `person_linkedin_url_by_email` (0.1-5).
- Email verification: `..._allegrow` (0.1), `..._million_verifier` (0.1), `..._neverbounce` (1), `..._zerobounce` (1).
- `person_phone_number_verification_using_real_phone` (2).

**CRM (PREREQ connections; 0 credits)**
- HubSpot: `hubspot_create_object`, `hubspot_lookup_object`, `hubspot_update_object`, `hubspot_upsert_object`.
- Salesforce: `salesforce_create_record`, `salesforce_lookup_record`, `salesforce_update_record`, `salesforce_upsert_record`.

**Integration / Outreach (PREREQ; 0 credits)**
- Sequencers: `instantly_add_to_campaign`, `smartleads_add_to_campaign`, `lemlist_add_lead_to_campaign`, `reply_add_and_push_to_campaign`, `heyreach_add_leads_to_campaign`, `la_growth_machine_add_to_audience`.
- Google Sheets: `google_sheet_add_data`, `google_sheet_upsert_row`, `google_sheets_lookup_rows`.

**Data ops / Format (0 credits)**
- `filter` — skip rows failing conditions (downstream cells never run for failed rows). See `reference/action-detail/filter.txt`.
- `auto_dedupe_rows`, `delay_step`.
- `lookup_another_floqer_workflow_row`, `push_data_to_another_floqer_workflow`, `push_data_to_sheet` (fan out a structured_array → rows).
- `format_data_using_js_expression` — **Workflow Data Formatter** (the JS escape hatch; see `reference/action-detail/`).
- `merge_employee_finder_structured_array`, `csv_to_structured_array_format`, `raw_to_structured_array`.

**LinkedIn signals**
- `get_company_or_person_linkedin_posts` (2/20 posts), `get_linkedin_post_reactors` (0.2).

**Developer**
- `http_api_call` (0) — call any external API and reference `{{http_api_call_1.response_body}}?.["data"]?.["id"]` via the JS formatter.

---

## 7. Source Catalog (26 sources) — quick map

Full body shapes + filter catalogues in `reference/source-catalog.txt` and `source-detail/{id}.txt`. Sources marked PREREQ need a one-time OAuth on the Floqer Connections page (missing → 424). List-building & LinkedIn sources need **no** connection.

- **CRM imports (PREREQ):** `import_from_hubspot`, `import_from_salesforce`, `import_from_pipedrive`, `import_from_google_sheets`, `import_from_snowflake`.
- **First-party (PREREQ):** `import_from_typeform`, `import_from_stripe`, `import_from_fireflies`, `track_website_visitors` / `track_personal_website_visitors` (return a tracking pixel to embed).
- **Ongoing signals:** `track_linkedin_posts`, `track_job_postings`, `track_x_posts`.
- **One-time signals:** `extract_from_website`, `find_linkedin_post_reactors`, `search_x_tweets`.
- **List building (one-time, no connection):** `find_companies`, `find_people`, `find_companies_by_buying_intent`, `find_companies_by_tech_stack`, `find_companies_hiring`, `find_job_postings`, `find_people_from_sales_navigator`, `find_companies_from_sales_navigator`, `search_local_businesses`.

**`pull_mode`:** `static` (one-time, `max_count` caps size) vs `active` (ongoing on `schedule` cron until `expiration_date`). **`pull_existing`** (default true) = backfill on create.

### Sync = connect source → workflow
```jsonc
POST /api/v1/sources/{source_instance_id}/sync
{
  "workflow_id": "...",
  "field_mapping": { "input.email": "email", "input.first_name": "firstname" },
  "push_existing": true,        // backfill workflow with current rows
  "run": "first_10"             // "all" | "first_10" | "none"
}
```
- `field_mapping` KEY = input reference **without braces** (`input.email`), **lowercase snake_case, case-sensitive**. VALUE = the source row's **top-level** key exactly as it appears in Preview (never a nested path; `{label,value}` cells unwrap automatically).
- Build it: `List Workflows` → `workflow_id`; `List Inputs` → input refs; map each to a Preview field.
- Re-syncing an already-connected source to the same workflow → **409** (don't retry to "fix" a mapping — it'd double the connection).

---

## 8. Dynamic Dropdowns (always resolve, never guess)

Many action/source fields are account-dependent (HubSpot props, Instantly campaigns, SF external-ID fields, Sheet tabs). **Resolve before configuring:**
```jsonc
POST .../actions/{aid}/options/{field_name}      // or /sources/{source_id}/options/{field_name}
{ "context": { "<other_field>": "<value>" } }    // optional, field-dependent
// → [{ value, label }]   →  pass chosen value into Configure Action / source body
```
Examples: HubSpot properties → `options/hubspot_object_properties` with `context:{hubspot_object:"contacts"}`; Instantly campaigns → `options/campaign_id` `{}`; Sheet tabs → `options/select_sheet` `{context:{spreadsheets:"<id>"}}`.

**Static-enum dropdowns** (e.g. HubSpot `hubspot_object`) return `"does not have a dynamic-options resolver"` — that's not an error; read valid values from the action-detail file.

**Waterfall fields** (e.g. `email_providers` on `person_work_email_waterfall`) take an **ordered string array** of provider IDs. Reorder via Configure Action or `PATCH .../waterfall/{field_name}` `{providers:[...]}`. Email verifiers available: `ZeroBounce`(1), `MillionVerifier`(0.1), `NeverBounce`(1), `Allegrow`(0.1). Note: passing `linkedin_url` enables LinkedIn-only providers (more coverage); domain-only disables them (cheaper, less coverage).

---

## 9. Conditional Execution (`run_if`) & Filtering

Gate any action so it runs for a row only when a condition holds. Set in Configure Action's body. `null` clears; omit = unchanged; `{}` = no-op (does **not** clear).

```jsonc
"run_if": {
  "conditions": [
    { "conditions": [
        { "variable": "{{person_work_email_waterfall_1.work_email}}",
          "operator": "is not empty" }
      ] }
  ]
}
```
- `conditions` = array of **groups**; each group = array of **leaf conditions**. Leaves joined by each leaf's `combinator` (AND/OR); groups joined the same way. First group/leaf `combinator` ignored; omitted = AND.
- A single condition = one group with one leaf.
- **Multi-value `is`/`is not` = set membership (SQL IN):** `values:["US","UK"]` with `operator:"is"` matches either.
- **Operators by stored type:** universal `is｜is not｜is empty｜is not empty`; string/email/url `contains｜starts with｜ends with` (+ negations, case-insensitive); number `greater/less than｜is between`; date `is after｜is before｜is between`; array/json `contains`.
- `values` are literals only (refs inside `values` are NOT resolved).
- The `filter` action uses the same `path_conditions` shape but **drops** failing rows from the chain (downstream cells never run). `run_if` only gates the one action.

**Common patterns:**
- Lookup-then-create: `salesforce_lookup_record` → `salesforce_create_record` with `run_if: {{lookup.record_id}} is empty`.
- Gate outreach on enrichment: `person_work_email_waterfall` → `instantly_add_to_campaign` with `run_if: work_email is not empty`.

---

## 10. Worked Example — enrich inbound + push to HubSpot

```bash
KEY="floq_..."; BASE="https://api.floqer.com/api/v1"

# 1. Bootstrap
curl -s "$BASE/user/" -H "Authorization: Bearer $KEY"

# 2. Create workflow (auto-creates main sheet; WF_ID === main sheet id)
WF=$(curl -s -X POST "$BASE/workflows/" -H "Authorization: Bearer $KEY" \
  -H "Content-Type: application/json" -d '{"name":"Inbound Enrich → HubSpot"}')
WF_ID=$(echo "$WF" | python3 -c "import sys,json;print(json.load(sys.stdin)['data']['workflow_id'])")

# 3. Add inputs (bare array)
curl -s -X POST "$BASE/workflows/$WF_ID/sheets/$WF_ID/inputs" -H "Authorization: Bearer $KEY" \
  -H "Content-Type: application/json" \
  -d '[{"name":"linkedin_url","type":"url"},{"name":"email","type":"email"}]'

# 4. Add action: scrape person LI profile
ADD=$(curl -s -X POST "$BASE/workflows/$WF_ID/sheets/$WF_ID/actions/add" \
  -H "Authorization: Bearer $KEY" -H "Content-Type: application/json" \
  -d '{"action_id":"enrich_person_linkedin_profile"}')
AID=$(echo "$ADD" | python3 -c "import sys,json;print(json.load(sys.stdin)['data']['action_instance_id'])")

# 5. Configure it — wire the input
curl -s -X PATCH "$BASE/workflows/$WF_ID/sheets/$WF_ID/actions/$AID" \
  -H "Authorization: Bearer $KEY" -H "Content-Type: application/json" \
  -d '{"inputs":{"linkedin_url":"{{input.linkedin_url}}"}}'

# 6. Add 1 test row + run first_10
curl -s -X POST "$BASE/workflows/$WF_ID/sheets/$WF_ID/rows" \
  -H "Authorization: Bearer $KEY" -H "Content-Type: application/json" \
  -d '{"rows":[{"linkedin_url":"https://linkedin.com/in/...","email":"x@acme.com"}],"run_after_add":"first_10"}'

# 7. Poll results
curl -s -X POST "$BASE/workflows/$WF_ID/sheets/$WF_ID/rows/list" \
  -H "Authorization: Bearer $KEY" -H "Content-Type: application/json" -d '{"page_size":20}'
```
Then add `hubspot_upsert_object` (resolve its dropdowns via `options/`), wire enriched fields, gate with `run_if`, and only `run-all` after the 10-row output looks right.

---

## 11. Gotchas Checklist

- [ ] **Main sheet id == workflow id.** Pass WF_ID for both path params on the main sheet.
- [ ] **Row keys = input `name` verbatim** (case/space-sensitive), NOT the snake_case reference token. Always `List Inputs` first.
- [ ] **`json`/object outputs aren't dotted** — bracket-access inside `format_data_using_js_expression`.
- [ ] **Configure Action invalidates cache** for that action + all downstream → re-bills. Rename/note don't.
- [ ] **Never `run-all` unverified.** 10 → 100 → 1,000 → all.
- [ ] **Add Inputs body is a bare array**, not `{inputs:[...]}`.
- [ ] **Resolve dynamic dropdowns** before configuring; don't guess values.
- [ ] **Re-sync to same workflow = 409.** Set the mapping right the first time.
- [ ] **`field_mapping` keys** = `input.<field>` (no braces, lowercase snake_case, case-sensitive).
- [ ] **Runs are async** — poll `List Rows` until `row_status` is `complete`/`has_failures`.
- [ ] **Large outputs** come as `outputs_ref` URL — fetch with the API key.
- [ ] **429** → wait `retryAfter` seconds exactly.

---

## 12. Outbound Write Paths Need Sign-off

Building workflows, running enrichments and syncing sources inside Floqer are fine. **But** Floqer can write **into** your other systems via CRM/integration actions (HubSpot, Salesforce, Instantly, Lemlist, SmartLead). When a workflow's actions push to those systems, that is a live write to your CRM or sequencer — flag it and get explicit sign-off from whoever owns that system before activating it. Building/previewing is safe; activating an outbound write path needs sign-off.

---

*Reference files bundled in `reference/` were scraped from floqer.com/docs on 2026-06-29. Floqer maintains them — re-scrape them from the URLs in §0 to refresh.*
