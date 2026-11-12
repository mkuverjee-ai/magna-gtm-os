---
name: instantly-api
description: Instantly campaign creation, lead loading, analytics, and HTML formatting. Use when working with the Instantly API.
---

# Instantly API — Operations Playbook

## Quick Reference

- **Base URL:** `https://api.instantly.ai/api/v2`
- **Auth:** `Authorization: Bearer <API_KEY>`
- **Content-Type:** `application/json` (all requests)
- **Pagination:** Cursor-based — use `next_starting_after` from response
- **Key:** `INSTANTLY_API_KEY`. Python resolves it with `gtm.cred("INSTANTLY_API_KEY")` (environment,
  then `~/.magna-gtm-config`, then the `api_keys` table). In a shell command use
  `$(python3 gtm.py key INSTANTLY_API_KEY --raw)` inline, never echoed. Missing? Add it with
  `python3 gtm.py set-key INSTANTLY_API_KEY` (value on stdin).
- **Send guard:** every campaign is created as a DRAFT (status 0). Nothing is activated until the
  user explicitly says go.

---

## Default Campaign Settings

Always use these as baseline for every new campaign:

```json
{
  "email_gap": 15,
  "random_wait_max": 7,
  "text_only": true,
  "first_email_text_only": true,
  "daily_limit": 9999,
  "stop_on_reply": true,
  "match_lead_esp": true,
  "link_tracking": false,
  "open_tracking": false,
  "pl_value": 35000,
  "campaign_schedule": {
    "schedules": [{
      "name": "Weekday schedule",
      "timing": { "from": "08:00", "to": "14:00" },
      "days": { "1": true, "2": true, "3": true, "4": true, "5": false },
      "timezone": "America/Detroit"
    }]
  }
}
```

| Setting | Value | Why |
|---------|-------|-----|
| `email_gap` | `15` | 15-min minimum between sends from same account |
| `text_only` | `true` | Plain-text rendering, better deliverability |
| `stop_on_reply` | `true` | Stop sequence on prospect reply |
| `match_lead_esp` | `true` | Gmail-to-Gmail, Outlook-to-Outlook matching |
| `link_tracking` | `false` | No tracking = better deliverability |
| `open_tracking` | `false` | No pixel = better deliverability |
| `daily_limit` | `9999` | Per-campaign limit; individual account limits still apply |

---

## Gotchas (Read Before Doing Anything)

1. **Timezone:** Use `America/Detroit`, NOT `America/New_York` (same timezone, but Instantly rejects New_York)
2. **Schedule days:** Zero-indexed from Sunday: `0`=Sun, `1`=Mon, `2`=Tue, `3`=Wed, `4`=Thu, `5`=Fri, `6`=Sat
3. **Activate/Pause:** Must send empty JSON body `{}`
4. **Delete lead:** Must NOT send body or Content-Type header
5. **List leads:** Use `POST /leads/list` (GET /leads returns 404)
6. **Lead field name:** V2 API uses `campaign` NOT `campaign_id` when adding leads. Using `campaign_id` silently adds leads to org pool without linking to campaign.
7. **HTML escaping:** `>` in email body must be `&gt;` (e.g., "Quality &gt; volume")
8. **Lead dedup:** By default, leads are deduped across campaigns. Set `skip_if_in_campaign: false` to force-add.

---

## HTML Email Formatting

Even with `text_only: true`, Instantly uses HTML `<div>` tags internally.

**Rules:**
- Every line in its own `<div>` tag
- Blank lines use `<div><br /></div>`
- No `<p>` tags, only `<div>`
- Special chars HTML-encoded (`>` = `&gt;`, `<` = `&lt;`)
- Signature: `<div>{{accountSignature}}</div>`

**Example conversion:**
```
Plain:  {{firstName}},\n\nMost teams book from 2-3% of replies.\n\nQuality > volume.
HTML:   <div>{{firstName}},</div><div><br /></div><div>Most teams book from 2-3% of replies.</div><div><br /></div><div>Quality &gt; volume.</div>
```

**Python converter:**
```python
import html

def to_instantly_html(plain_text: str) -> str:
    lines = plain_text.strip().split('\n')
    return ''.join(
        '<div><br /></div>' if line.strip() == ''
        else f'<div>{html.escape(line.strip())}</div>'
        for line in lines
    )
```

---

## Variables

### Core (auto-populated from lead data)

| Variable | Source Field | Required |
|----------|-------------|----------|
| `{{firstName}}` | `first_name` | Yes |
| `{{lastName}}` | `last_name` | Recommended |
| `{{companyName}}` | `company_name` | Recommended |
| `{{email}}` | `email` | Yes |
| `{{website}}` | `website` | Optional |
| `{{personalization}}` | `personalization` | Optional |
| `{{accountSignature}}` | Sending account signature | Auto |

### Custom (via lead `payload` object)

Any key in `payload` becomes `{{key}}` in templates:

| Variable | Description |
|----------|-------------|
| `{{Idea1}}` | AI-generated, prospect-specific idea #1 |
| `{{Idea2}}` | AI-generated, prospect-specific idea #2 |
| `{{Idea3}}` | AI-generated, prospect-specific idea #3 |
| `{{SL}}` | Dynamic subject line override |

### Spintax

```
{{RANDOM|Hey|Hi|Hello}} {{firstName}},
```

---

## Key Endpoints

### Create Campaign — `POST /campaigns`

```json
{
  "name": "Campaign Name - Segment",
  "campaign_schedule": { ... },
  "sequences": [{
    "steps": [
      {
        "type": "email",
        "delay": 2,
        "variants": [
          { "subject": "Subject A", "body": "<div>HTML body</div>" },
          { "subject": "Subject B", "body": "<div>Variant B</div>" }
        ],
        "delay_unit": "days",
        "pre_delay_unit": "days"
      }
    ]
  }],
  "email_gap": 15,
  "text_only": true,
  ... // other defaults from above
}
```

**Step timing guidelines:**
- Step 1 delay: `2` days
- Step 2 delay: `3-5` days
- Step 3 delay: `4-7` days
- Max sequence: 2-3 steps, 2-3 variants per step

### Add Lead — `POST /leads`

```json
{
  "campaign": "campaign-uuid",
  "email": "prospect@company.com",
  "first_name": "John",
  "last_name": "Doe",
  "company_name": "Acme Corp",
  "website": "acme.com",
  "payload": {
    "Idea1": "Flag accounts that just raised a round",
    "Idea2": "Route inbound demo requests by territory",
    "Idea3": "Re-engage closed-lost deals after a champion moves"
  }
}
```

**Required:** `campaign` (UUID) + `email`. Use `campaign`, NOT `campaign_id`.

### List Leads — `POST /leads/list`

```json
{ "campaign": "uuid", "limit": 100 }
```

Lead statuses: `1` = Not yet contacted, `2` = In sequence, `3` = Completed.

### Campaign Analytics — `GET /campaigns/analytics`

```
GET /campaigns/analytics?campaign_id={id}
GET /campaigns/analytics?campaign_id={id}&start_date=2026-01-01&end_date=2026-03-01
```

Returns: `leads_count`, `contacted_count`, `emails_sent_count`, `reply_count`, `bounced_count`, `opportunities_count`.

### Daily Analytics — `GET /campaigns/analytics/daily`

Same params, returns per-day breakdown with `sent`, `contacted`, `replies`, `opportunities`.

### Other Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `GET /campaigns` | GET | List campaigns (filter by `status`: 0=draft, 1=active, 2=paused, 3=completed) |
| `GET /campaigns/{id}` | GET | Get full campaign details |
| `PATCH /campaigns/{id}` | PATCH | Update campaign (partial) |
| `POST /campaigns/{id}/activate` | POST | Activate (send `{}`) |
| `POST /campaigns/{id}/pause` | POST | Pause (send `{}`) |
| `DELETE /leads/{id}` | DELETE | Delete lead (NO body, NO Content-Type) |
| `GET /accounts` | GET | List sending accounts |
| `GET /lead-lists` | GET | List lead lists |

---

## Block List (exclusion / suppression)

**The path is `block-lists-entries`** — plural on both words. Every intuitive spelling
(`blocklist`, `blocklist-entries`, `block-list-entries`, `blocked-domains`, `suppression`) returns
`404 Route not found`. Verified 2026-09-09.

```bash
# List entries (cursor-paginated like everything else)
GET /block-lists-entries?limit=100

# Add a domain or a single email
POST /block-lists-entries   {"bl_value": "example.com"}
```

Response: `{"id", "timestamp_created", "organization_id", "bl_value", "is_domain"}`.
`is_domain` is inferred by Instantly — pass a bare domain (`example.edu`, no `@`) and it comes back
`true`; pass `someone@example.edu` and it comes back `false`.

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `GET /block-lists-entries` | GET | List blocked domains/emails |
| `POST /block-lists-entries` | POST | Add one (`bl_value`) |
| `DELETE /block-lists-entries/{id}` | DELETE | Remove one |

Scopes required: `block_list_entries:create` / `block_list_entries:all` / `all:create` / `all:all`.

**Blocking is not removing.** Adding a domain stops *future* sends and blocks re-import, but it does
not delete leads already sitting in campaigns. To purge existing ones, search and delete first, then
block:

```
1. POST /leads/list  {"search": "<domain>"}   → find them (searches email, company_domain, website)
2. DELETE /leads/{id}  (loop)                  → remove from campaigns
3. POST /block-lists-entries {"bl_value": "<domain>"}  → stop them coming back
```

Filter step 1's results yourself — `search` is a loose substring match across several fields, so
confirm `company_domain == <domain>` or `email` ends with `@<domain>` before deleting anything.

---

## Cloudflare blocks default user-agents

Python `urllib` gets `403` with body `error code: 1010` on every endpoint — that is Cloudflare
rejecting the default `Python-urllib/3.x` user-agent, not an auth failure. Use `curl` (via
`subprocess` if you need to script it), or set a browser-like `User-Agent` header.

---

## Workflows

### Full Campaign Launch

```
1. POST /campaigns          → Create (lands as DRAFT) with the defaults + sequences
2. POST /leads (loop)       → Add leads with payload variables
3. GET /campaigns/{id}      → Verify sequences look correct
4. Connect sending accounts → (Instantly UI)
5. POST /campaigns/{id}/activate → ONLY after the user explicitly says go. Never on your own.
```

### Performance Check

```
1. GET /campaigns/analytics?campaign_id={id}     → Aggregate stats
2. GET /campaigns/analytics/daily?campaign_id={id} → Daily trends
3. Compare against the benchmarks (see below)
4. POST /leads/list with campaign_id              → Check individual lead statuses
```

---

## Benchmarks (from a few hundred B2B campaigns)

| Metric | Kill | Keep | Scale |
|--------|------|------|-------|
| Positive reply rate | <1% | 2-5% | >5% |
| Emails per positive reply | >5,000 | 1,000-3,000 | <1,000 |
| Meeting book rate | <0.5% | 1-2% | >2% |

**Top performer:** a template carrying three AI-generated, prospect-specific ideas (`{{Idea1}}`, `{{Idea2}}`, `{{Idea3}}`) outperformed all other templates across 43 campaigns.

### A/B Test Decision Matrix

After 200+ sends per variant:
- Kill variants below 1% reply rate
- Branch top 2-3 winners into sub-variants
- Apply 70/20/10 split (winners / iterations / experiments)
