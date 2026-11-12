---
name: instantly
description: Instantly.ai API v2 — Email campaign creation, lead management, sending accounts, and analytics. Full API reference with default campaign settings, HTML formatting rules, and variable mapping.
---

# Instantly API Skill

## Overview

Instantly (`api.instantly.ai`) is the email sending platform for your outbound campaigns (one Instantly workspace, yours). This skill covers campaign creation, lead management, account management, and analytics via the v2 REST API.

**Base URL:** `https://api.instantly.ai/api/v2`
**Auth:** `Authorization: Bearer <API_KEY>` header
**Content-Type:** `application/json` (all requests)
**Pagination:** Cursor-based — use `next_starting_after` from response in subsequent requests

---

## Authentication

All requests require the Bearer token in the Authorization header. The key is `INSTANTLY_API_KEY`:

- **Python:** `gtm.cred("INSTANTLY_API_KEY")` from repo-root `gtm.py` (resolution: environment, then
  `~/.magna-gtm-config`, then the `api_keys` table).
- **Shell:** inline only, never echoed: `-H "Authorization: Bearer $(python3 gtm.py key INSTANTLY_API_KEY --raw)"`.
- **Missing?** Add it with `python3 gtm.py set-key INSTANTLY_API_KEY` (value on stdin).

**Send guard:** every campaign is created as a DRAFT (status `0`). Nothing is activated
(`/activate`) and no paused campaign is resumed until the user explicitly says go.

```bash
curl -H "Authorization: Bearer <API_KEY>" \
     -H "Content-Type: application/json" \
     https://api.instantly.ai/api/v2/campaigns
```

---

## Campaign Statuses

| Code | Status | Description |
|------|--------|-------------|
| `0` | Draft | Created but not sending |
| `1` | Active | Currently sending |
| `2` | Paused | Manually paused |
| `3` | Completed | All leads processed |

---

## Default Campaign Settings

These are the settings from the best performers in a few hundred B2B campaigns. Use these as the baseline for every new campaign:

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
    "schedules": [
      {
        "name": "Weekday schedule",
        "timing": {
          "from": "08:00",
          "to": "14:00"
        },
        "days": {
          "1": true,
          "2": true,
          "3": true,
          "4": true,
          "5": false
        },
        "timezone": "America/Detroit"
      }
    ]
  }
}
```

### Settings Reference

| Setting | Value | Why |
|---------|-------|-----|
| `email_gap` | `15` | 15-minute minimum between sends from same account |
| `random_wait_max` | `7` | Up to 7 extra random minutes added to gap |
| `text_only` | `true` | Plain-text rendering — no HTML styling, better deliverability |
| `first_email_text_only` | `true` | First email always plain text |
| `daily_limit` | `9999` | Per-campaign limit (individual account limits apply) |
| `stop_on_reply` | `true` | Stop sequence when prospect replies |
| `match_lead_esp` | `true` | Match sending domain to lead's ESP (Gmail→Gmail, Outlook→Outlook) |
| `link_tracking` | `false` | No link tracking — improves deliverability |
| `open_tracking` | `false` | No open pixel — improves deliverability |
| `pl_value` | `35000` | Pipeline value attribution ($350.00) |

### Timezone Quirk

Instantly does NOT accept `America/New_York`. Use `America/Detroit` instead (same timezone, ET).

### Schedule Days

Days are zero-indexed from Sunday:
- `0` = Sunday, `1` = Monday, `2` = Tuesday, `3` = Wednesday, `4` = Thursday, `5` = Friday, `6` = Saturday
- Default: Mon-Thu only (`"1": true, "2": true, "3": true, "4": true`)

---

## Email Body HTML Formatting

Instantly uses HTML `<div>` tags for email bodies, even when `text_only: true` (it renders as plain text).

### Rules

1. **Every line** goes in its own `<div>` tag
2. **Blank lines** use `<div><br /></div>`
3. **No `<p>` tags** — only `<div>`
4. **Special characters** must be HTML-encoded (`>` → `&gt;`, `<` → `&lt;`)
5. **Signature** goes in its own `<div>{{accountSignature}}</div>`

### Example — Converting Plain Text to Instantly HTML

**Plain text:**
```
{{firstName}},

Most teams book from 2-3% of cold replies.

Quality > volume.

Talk soon,
{{accountSignature}}
```

**Instantly HTML:**
```html
<div>{{firstName}},</div><div><br /></div><div>Most teams book from 2-3% of cold replies.</div><div><br /></div><div>Quality &gt; volume.</div><div><br /></div><div>Talk soon,</div><div>{{accountSignature}}</div>
```

### Conversion Function (Python)

```python
def to_instantly_html(plain_text: str) -> str:
    """Convert plain text email to Instantly HTML format."""
    import html
    lines = plain_text.strip().split('\n')
    result = []
    for line in lines:
        if line.strip() == '':
            result.append('<div><br /></div>')
        else:
            result.append(f'<div>{html.escape(line.strip())}</div>')
    return ''.join(result)
```

---

## Variables

### Core Variables (auto-populated from lead data)

| Variable | Source | Required in Lead |
|----------|--------|-----------------|
| `{{firstName}}` | `first_name` field | Yes |
| `{{lastName}}` | `last_name` field | Recommended |
| `{{companyName}}` | `company_name` field | Recommended |
| `{{email}}` | `email` field | Yes |
| `{{website}}` | `website` field | Optional |
| `{{personalization}}` | `personalization` field | Optional |
| `{{phone}}` | `phone` field | Optional |
| `{{accountSignature}}` | Sending account signature | Auto |

### Custom Variables (set in lead payload)

Custom variables are passed in the lead's `payload` object. Any key in the payload becomes a `{{variableName}}` in the email body.

Example custom variables:

| Variable | Description | Example |
|----------|-------------|---------|
| `{{Idea1}}` | AI-generated, prospect-specific idea #1 | "Route inbound demo requests by territory" |
| `{{Idea2}}` | AI-generated, prospect-specific idea #2 | "Flag accounts that just raised a round" |
| `{{Idea3}}` | AI-generated, prospect-specific idea #3 | "Re-engage closed-lost deals after a champion moves" |
| `{{SL}}` | Dynamic subject line override | "saw your post in {{community}}" |

### Spintax

Instantly supports spintax for deliverability:
```
{{RANDOM|Hey|Hi|Hello}} {{firstName}},
```

---

## Endpoints

### Campaigns

#### `GET /campaigns` — List Campaigns

```bash
curl -s -X GET "https://api.instantly.ai/api/v2/campaigns?limit=10&status=1" \
  -H "Authorization: Bearer <API_KEY>" \
  -H "Content-Type: application/json"
```

**Query params:**
| Param | Type | Description |
|-------|------|-------------|
| `limit` | int | Max results (default 10) |
| `status` | int | Filter by status (0/1/2/3) |
| `starting_after` | string | Cursor for pagination |

**Response:**
```json
{
  "items": [
    {
      "id": "uuid",
      "name": "Campaign Name",
      "status": 1,
      "campaign_schedule": { ... },
      "sequences": [ ... ],
      "email_gap": 15,
      "text_only": true,
      "daily_limit": 9999,
      "stop_on_reply": true,
      "match_lead_esp": true,
      "timestamp_created": "ISO8601",
      "timestamp_updated": "ISO8601"
    }
  ],
  "next_starting_after": "cursor_value"
}
```

---

#### `GET /campaigns/{id}` — Get Campaign

```bash
curl -s -X GET "https://api.instantly.ai/api/v2/campaigns/{campaign_id}" \
  -H "Authorization: Bearer <API_KEY>" \
  -H "Content-Type: application/json"
```

Returns full campaign object including sequences, schedule, and settings.

---

#### `POST /campaigns` — Create Campaign

This is the primary endpoint for campaign creation. Include all settings, schedule, and sequences in one call.

```bash
curl -s -X POST "https://api.instantly.ai/api/v2/campaigns" \
  -H "Authorization: Bearer <API_KEY>" \
  -H "Content-Type: application/json" \
  -d '<payload>'
```

**Full Campaign Creation Template:**

```json
{
  "name": "Campaign Name - Segment Description",
  "campaign_schedule": {
    "schedules": [
      {
        "name": "Weekday schedule",
        "timing": { "from": "08:00", "to": "14:00" },
        "days": { "1": true, "2": true, "3": true, "4": true, "5": false },
        "timezone": "America/Detroit"
      }
    ]
  },
  "sequences": [
    {
      "steps": [
        {
          "type": "email",
          "delay": 2,
          "variants": [
            {
              "subject": "Subject Line A",
              "body": "<div>Email body in HTML format</div>"
            },
            {
              "subject": "Subject Line B",
              "body": "<div>Variant B body</div>"
            }
          ],
          "delay_unit": "days",
          "pre_delay_unit": "days"
        },
        {
          "type": "email",
          "delay": 4,
          "variants": [
            {
              "subject": "Follow-up subject",
              "body": "<div>Follow-up body</div>"
            }
          ],
          "delay_unit": "days",
          "pre_delay_unit": "days"
        }
      ]
    }
  ],
  "email_gap": 15,
  "random_wait_max": 7,
  "text_only": true,
  "first_email_text_only": true,
  "daily_limit": 9999,
  "stop_on_reply": true,
  "match_lead_esp": true,
  "pl_value": 35000
}
```

**Step Structure:**

| Field | Type | Description |
|-------|------|-------------|
| `type` | string | Always `"email"` for email steps |
| `delay` | int | Days to wait before sending this step |
| `variants` | array | A/B/C variants — each with `subject` and `body` |
| `delay_unit` | string | `"days"` |
| `pre_delay_unit` | string | `"days"` |

**Variant Structure:**

| Field | Type | Description |
|-------|------|-------------|
| `subject` | string | Subject line (supports variables and spintax) |
| `body` | string | HTML email body (see formatting rules above) |

**Step Timing Guidelines:**
- Step 1 delay: `2` days (from lead addition)
- Step 2 delay: `3-5` days (from step 1)
- Step 3 delay: `4-7` days (from step 2)
- Max sequence length: 2-3 steps
- 2-3 variants per step for testing

---

#### `PATCH /campaigns/{id}` — Update Campaign

```bash
curl -s -X PATCH "https://api.instantly.ai/api/v2/campaigns/{campaign_id}" \
  -H "Authorization: Bearer <API_KEY>" \
  -H "Content-Type: application/json" \
  -d '{"name": "Updated Name", "daily_limit": 500}'
```

Partial updates — only include fields you want to change. Returns full updated campaign object.

---

#### `POST /campaigns/{id}/activate` — Activate Campaign

```bash
curl -s -X POST "https://api.instantly.ai/api/v2/campaigns/{campaign_id}/activate" \
  -H "Authorization: Bearer <API_KEY>" \
  -H "Content-Type: application/json" \
  -d '{}'
```

**Important:** Must send empty JSON body `{}`. Sets status to `1` (active). Returns full campaign object.

🚨 **This starts real sends to real prospects.** Never call it without the user's explicit go for
this specific campaign.

**Pre-activation checklist:**
1. Campaign has at least one sequence step with at least one variant
2. At least one sending account is connected
3. Leads have been added to the campaign
4. Double-check schedule, timezone, and daily limits

---

#### `POST /campaigns/{id}/pause` — Pause Campaign

```bash
curl -s -X POST "https://api.instantly.ai/api/v2/campaigns/{campaign_id}/pause" \
  -H "Authorization: Bearer <API_KEY>" \
  -H "Content-Type: application/json" \
  -d '{}'
```

Sets status to `2` (paused). Returns full campaign object.

---

### Leads

#### `POST /leads` — Add Single Lead

```bash
curl -s -X POST "https://api.instantly.ai/api/v2/leads" \
  -H "Authorization: Bearer <API_KEY>" \
  -H "Content-Type: application/json" \
  -d '{
    "campaign": "uuid",
    "email": "prospect@company.com",
    "first_name": "John",
    "last_name": "Doe",
    "company_name": "Acme Corp",
    "website": "acme.com",
    "personalization": "",
    "custom_variables": {
      "Idea1": "Flag accounts that just raised a round",
      "Idea2": "Route inbound demo requests by territory",
      "Idea3": "Re-engage closed-lost deals after a champion moves"
    }
  }'
```

**Required fields:**
| Field | Type | Description |
|-------|------|-------------|
| `campaign` | string | Campaign UUID to add lead to (**NOT `campaign_id`** — V2 API uses `campaign`) |
| `email` | string | Lead's email address |

**Dedup control:**
| Field | Type | Description |
|-------|------|-------------|
| `skip_if_in_campaign` | boolean | If `false` (default), adds lead even if they exist in other campaigns. If `true`, skips leads already active in another campaign. |

**Optional fields:**
| Field | Type | Description |
|-------|------|-------------|
| `first_name` | string | Maps to `{{firstName}}` |
| `last_name` | string | Maps to `{{lastName}}` |
| `company_name` | string | Maps to `{{companyName}}` |
| `website` | string | Maps to `{{website}}` |
| `personalization` | string | Maps to `{{personalization}}` |
| `phone` | string | Maps to `{{phone}}` |
| `custom_variables` | object | Custom variables — any key becomes `{{key}}` in templates (**NOT `payload`** — V2 API uses `custom_variables`). Values must be string, number, boolean, or null — no nested objects/arrays. |
| `list_id` | string | Lead list UUID to also add to |

**Response:** Full lead object with `id`, `status`, `payload`, `upload_method: "api"`.

---

#### `POST /leads/list` — List Leads (Search)

```bash
curl -s -X POST "https://api.instantly.ai/api/v2/leads/list" \
  -H "Authorization: Bearer <API_KEY>" \
  -H "Content-Type: application/json" \
  -d '{
    "campaign": "uuid",
    "limit": 100
  }'
```

**Body params:**
| Param | Type | Description |
|-------|------|-------------|
| `campaign` | string | Filter by campaign (**NOT `campaign_id`** — an unknown param is silently ignored and you page the ENTIRE workspace) |
| `list_id` | string | Filter by lead list |
| `limit` | int | Max results |
| `starting_after` | string | Pagination cursor |

**Lead object fields:**
```json
{
  "id": "uuid",
  "email": "string",
  "first_name": "string",
  "last_name": "string",
  "company_name": "string",
  "company_domain": "string",
  "status": 1,
  "email_open_count": 0,
  "email_reply_count": 0,
  "email_click_count": 0,
  "campaign": "campaign_uuid",
  "payload": { "custom_key": "value" },
  "upload_method": "api|csv|manual",
  "timestamp_created": "ISO8601",
  "timestamp_last_contact": "ISO8601",
  "status_summary": {
    "lastStep": {
      "from": "sender@domain.com",
      "stepID": "0_1_0",
      "timestamp_executed": "ISO8601"
    }
  }
}
```

**Lead statuses:**
| Code | Status |
|------|--------|
| `1` | Active / Not yet contacted |
| `2` | In sequence |
| `3` | Completed sequence |

---

#### `POST /leads/move` — Move Leads to a Campaign or List

Moves leads out of a campaign into a lead list (or another campaign) as a background job.
This is what the UI's "Move to list" does — the way to pull contacts out of an active sequence
without deleting them (e.g. compliance suppressions before a later step sends).

```bash
curl -s -X POST "https://api.instantly.ai/api/v2/leads/move" \
  -H "Authorization: Bearer <API_KEY>" \
  -H "Content-Type: application/json" \
  -d '{
    "ids": ["lead-uuid", "..."],
    "campaign": "source-campaign-uuid",
    "to_list_id": "destination-list-uuid",
    "check_duplicates_in_campaigns": false
  }'
```

- `ids` is a **filter within** the source, so `campaign` (or `list_id`) naming the source is
  required alongside it. Destination is `to_list_id` or `to_campaign_id`.
- Response is a background job (`{"id": "..."}`). Poll `GET /background-jobs/{id}` until
  `status` is `success`.
- **Only one move job may run per campaign at a time** — submitting another returns 409.
  Batch ~500 ids and submit → poll to success → next batch.
- Create a destination list with `POST /lead-lists` `{"name": "..."}`.
- Measured on a real workspace: 1,599 leads moved in 4 batches, a few seconds per job.

---

#### `DELETE /leads/{id}` — Delete Lead

```bash
curl -s -X DELETE "https://api.instantly.ai/api/v2/leads/{lead_id}" \
  -H "Authorization: Bearer <API_KEY>"
```

**Important:** Do NOT send a Content-Type header or body. The endpoint requires `body must be null`.

---

### Lead Lists

#### `GET /lead-lists` — List Lead Lists

```bash
curl -s -X GET "https://api.instantly.ai/api/v2/lead-lists?limit=10" \
  -H "Authorization: Bearer <API_KEY>" \
  -H "Content-Type: application/json"
```

**Response:**
```json
{
  "items": [
    {
      "id": "uuid",
      "organization_id": "uuid",
      "name": "List Name",
      "timestamp_created": "ISO8601",
      "has_enrichment_task": false,
      "owned_by": "user_uuid"
    }
  ],
  "next_starting_after": "cursor"
}
```

---

### Accounts (Sending Accounts)

#### `GET /accounts` — List Sending Accounts

```bash
curl -s -X GET "https://api.instantly.ai/api/v2/accounts?limit=10" \
  -H "Authorization: Bearer <API_KEY>" \
  -H "Content-Type: application/json"
```

**Account object fields:**
```json
{
  "email": "sender@domain.com",
  "first_name": "First",
  "last_name": "Last",
  "provider_code": 2,
  "warmup_status": 1,
  "daily_limit": 15,
  "sending_gap": 4,
  "status": -1,
  "setup_pending": false,
  "tracking_domain_name": "inst.domain.com",
  "tracking_domain_status": "CTD_ACTIVE",
  "stat_warmup_score": 100,
  "warmup": {
    "limit": 19,
    "reply_rate": 49,
    "advanced": {
      "warm_ctd": true,
      "open_rate": 100,
      "read_emulation": true,
      "spam_save_rate": 100,
      "weekday_only": true
    }
  }
}
```

**Provider codes** (per Instantly's API spec; a wrong code means the account won't work):
| Code | Provider |
|------|----------|
| `1` | Custom IMAP/SMTP |
| `2` | Google |
| `3` | Microsoft |
| `4` | AWS |
| `8` | AirMail |

**Account statuses:**
| Code | Status |
|------|--------|
| `1` | Active |
| `2` | Paused |
| `3` | Temporarily paused for maintenance |
| `-1` | Connection error |
| `-2` | Soft bounce error |
| `-3` | Sending error |

**Warmup status:** `0` paused · `1` active · `-1` banned · `-2` spam folder unknown · `-3` permanent suspension

---

### Analytics

#### `GET /campaigns/analytics` — Aggregate Analytics

```bash
curl -s -X GET "https://api.instantly.ai/api/v2/campaigns/analytics?campaign_id={id}" \
  -H "Authorization: Bearer <API_KEY>" \
  -H "Content-Type: application/json"
```

**Query params:**
| Param | Type | Description |
|-------|------|-------------|
| `campaign_id` | string | Filter by campaign (optional — omit for all) |
| `start_date` | string | ISO8601 date |
| `end_date` | string | ISO8601 date |

**Response:**
```json
[
  {
    "campaign": "uuid",
    "campaign_name": "string",
    "leads_count": 500,
    "contacted_count": 350,
    "emails_sent_count": 700,
    "reply_count": 25,
    "bounced_count": 12,
    "unsubscribed_count": 3,
    "opportunities_count": 8,
    "new_leads_contacted_count": 200
  }
]
```

**Key metrics to track:**
- **Reply rate:** `reply_count / contacted_count`
- **Bounce rate:** `bounced_count / emails_sent_count`
- **Opportunity rate:** `opportunities_count / contacted_count`

---

#### `GET /campaigns/analytics/daily` — Daily Analytics

```bash
curl -s -X GET "https://api.instantly.ai/api/v2/campaigns/analytics/daily?campaign_id={id}" \
  -H "Authorization: Bearer <API_KEY>" \
  -H "Content-Type: application/json"
```

**Response:**
```json
[
  {
    "campaign": "uuid",
    "campaign_name": "string",
    "date": "2026-02-13",
    "sent": 45,
    "contacted": 30,
    "replies": 3,
    "clicks": 0,
    "opportunities": 1
  }
]
```

---

### Emails

#### `GET /emails` — List Email Threads

```bash
curl -s -X GET "https://api.instantly.ai/api/v2/emails?campaign_id={id}&limit=10" \
  -H "Authorization: Bearer <API_KEY>" \
  -H "Content-Type: application/json"
```

Returns sent emails with message_id, subject, body, and address details.

---

## Workflows

### 1. Full Campaign Launch Workflow

```
Step 1: Create campaign (POST /campaigns)
  → Use the default settings template (lands as DRAFT, status 0)
  → Include all sequences and variants
  → Returns campaign_id

Step 2: Add leads (POST /leads — loop or bulk)
  → Include campaign_id
  → Include custom payload variables (Idea1, Idea2, Idea3)

Step 3: Verify setup
  → GET /campaigns/{id} to confirm sequences look correct
  → Check sending accounts are connected (may need to do in Instantly UI)

Step 4: Activate (POST /campaigns/{id}/activate)
  → Only after leads added and accounts connected
  → ONLY after the user explicitly says go. Never activate on your own.
```

### 2. Campaign Performance Check Workflow

```
Step 1: GET /campaigns/analytics?campaign_id={id}
  → Get aggregate stats (reply rate, bounce rate, opportunities)

Step 2: GET /campaigns/analytics/daily?campaign_id={id}
  → Get daily trends to spot patterns

Step 3: POST /leads/list with campaign_id
  → Check individual lead statuses and responses

Step 4: Report findings
  → Compare against the benchmarks:
    - Kill: <1% positive reply rate
    - Keep: 2-5% positive reply rate
    - Scale: >5% positive reply rate
```

### 3. A/B Test Analysis Workflow

```
Step 1: GET /campaigns/{id}
  → Review variant structure (step IDs: 0_0_0, 0_0_1, etc.)

Step 2: GET /campaigns/analytics?campaign_id={id}
  → Get overall campaign performance

Step 3: Decision matrix
  → After 200+ sends per variant:
    - Kill variants below 1% reply rate
    - Branch top 2-3 winners into sub-variants
    - Apply 70/20/10 split (winners/iterations/experiments)
```

---

## Python Helper Script

```python
"""
Instantly API helper.
Usage: from instantly_helper import InstantlyAPI
Key: gtm.cred("INSTANTLY_API_KEY") from repo-root gtm.py.
"""

import requests
import html
import json

class InstantlyAPI:
    BASE_URL = "https://api.instantly.ai/api/v2"

    def __init__(self, api_key: str):
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

    def _get(self, path: str, params: dict = None) -> dict:
        r = requests.get(f"{self.BASE_URL}{path}", headers=self.headers, params=params)
        r.raise_for_status()
        return r.json()

    def _post(self, path: str, data: dict = None) -> dict:
        r = requests.post(f"{self.BASE_URL}{path}", headers=self.headers, json=data or {})
        r.raise_for_status()
        return r.json()

    def _patch(self, path: str, data: dict) -> dict:
        r = requests.patch(f"{self.BASE_URL}{path}", headers=self.headers, json=data)
        r.raise_for_status()
        return r.json()

    def _delete(self, path: str) -> dict:
        r = requests.delete(f"{self.BASE_URL}{path}",
                          headers={"Authorization": self.headers["Authorization"]})
        r.raise_for_status()
        return r.json() if r.text else {}

    # --- Campaigns ---

    def list_campaigns(self, status: int = None, limit: int = 10) -> dict:
        params = {"limit": limit}
        if status is not None:
            params["status"] = status
        return self._get("/campaigns", params)

    def get_campaign(self, campaign_id: str) -> dict:
        return self._get(f"/campaigns/{campaign_id}")

    def create_campaign(self, name: str, sequences: list, **overrides) -> dict:
        payload = {
            "name": name,
            "sequences": sequences,
            **DEFAULTS,
            **overrides
        }
        return self._post("/campaigns", payload)

    def update_campaign(self, campaign_id: str, **updates) -> dict:
        return self._patch(f"/campaigns/{campaign_id}", updates)

    def activate_campaign(self, campaign_id: str, user_said_go: bool = False) -> dict:
        # Starts real sends. Pass user_said_go=True only after the user explicitly says go.
        if not user_said_go:
            raise RuntimeError("Refusing to activate: campaigns stay DRAFT until the user says go.")
        return self._post(f"/campaigns/{campaign_id}/activate", {})

    def pause_campaign(self, campaign_id: str) -> dict:
        return self._post(f"/campaigns/{campaign_id}/pause", {})

    # --- Leads ---

    def add_lead(self, campaign_id: str, email: str,
                 first_name: str = "", last_name: str = "",
                 company_name: str = "", payload: dict = None) -> dict:
        data = {
            "campaign": campaign_id,  # V2 field is `campaign`; `campaign_id` lands in the org pool
            "email": email,
            "first_name": first_name,
            "last_name": last_name,
            "company_name": company_name,
        }
        if payload:
            data["custom_variables"] = payload  # V2 field is `custom_variables`
        return self._post("/leads", data)

    def list_leads(self, campaign_id: str = None, limit: int = 100) -> dict:
        data = {"limit": limit}
        if campaign_id:
            data["campaign"] = campaign_id  # `campaign_id` is silently ignored here
        return self._post("/leads/list", data)

    def delete_lead(self, lead_id: str) -> dict:
        return self._delete(f"/leads/{lead_id}")

    # --- Analytics ---

    def campaign_analytics(self, campaign_id: str = None) -> dict:
        params = {}
        if campaign_id:
            params["campaign_id"] = campaign_id
        return self._get("/campaigns/analytics", params)

    def daily_analytics(self, campaign_id: str = None) -> dict:
        params = {}
        if campaign_id:
            params["campaign_id"] = campaign_id
        return self._get("/campaigns/analytics/daily", params)

    # --- Accounts ---

    def list_accounts(self, limit: int = 50) -> dict:
        return self._get("/accounts", {"limit": limit})

    # --- Lead Lists ---

    def list_lead_lists(self, limit: int = 20) -> dict:
        return self._get("/lead-lists", {"limit": limit})


# --- Defaults ---

DEFAULTS = {
    "email_gap": 15,
    "random_wait_max": 7,
    "text_only": True,
    "first_email_text_only": True,
    "daily_limit": 9999,
    "stop_on_reply": True,
    "match_lead_esp": True,
    "pl_value": 35000,
    "campaign_schedule": {
        "schedules": [
            {
                "name": "Weekday schedule",
                "timing": {"from": "08:00", "to": "14:00"},
                "days": {"1": True, "2": True, "3": True, "4": True, "5": False},
                "timezone": "America/Detroit"
            }
        ]
    }
}


# --- Email Formatting ---

def to_instantly_html(plain_text: str) -> str:
    """Convert plain text email body to Instantly HTML format.

    Each line becomes a <div>, blank lines become <div><br /></div>.
    Special characters are HTML-escaped.
    """
    lines = plain_text.strip().split('\n')
    result = []
    for line in lines:
        if line.strip() == '':
            result.append('<div><br /></div>')
        else:
            result.append(f'<div>{html.escape(line.strip())}</div>')
    return ''.join(result)


def build_sequence(steps: list[dict]) -> list:
    """Build an Instantly sequence from simplified step definitions.

    Args:
        steps: List of dicts, each with:
            - delay: int (days)
            - variants: list of {"subject": str, "body": str} where body is PLAIN TEXT

    Returns:
        Instantly-formatted sequence array.
    """
    formatted_steps = []
    for step in steps:
        formatted_variants = []
        for v in step["variants"]:
            formatted_variants.append({
                "subject": v["subject"],
                "body": to_instantly_html(v["body"])
            })
        formatted_steps.append({
            "type": "email",
            "delay": step["delay"],
            "variants": formatted_variants,
            "delay_unit": "days",
            "pre_delay_unit": "days"
        })
    return [{"steps": formatted_steps}]
```

### Quick-Start Example

```python
import sys
sys.path.insert(0, "<repo root>")
import gtm
from instantly_helper import InstantlyAPI, build_sequence

api = InstantlyAPI(gtm.cred("INSTANTLY_API_KEY"))

# Define steps with plain text (auto-converted to HTML)
steps = [
    {
        "delay": 2,
        "variants": [
            {
                "subject": "{{companyName}} pipeline",
                "body": """{{firstName}},

Most teams book from 2-3% of cold replies.

Quality > volume.

Talk soon,
{{accountSignature}}"""
            },
            {
                "subject": "quick question",
                "body": """{{firstName}}, from what I can see {{companyName}} still runs sales founder-led.

Is that by choice, or a hiring gap?

Talk soon,
{{accountSignature}}"""
            }
        ]
    },
    {
        "delay": 4,
        "variants": [
            {
                "subject": "3 ideas",
                "body": """Hey {{firstName}}, I looked at {{companyName}} and wrote down 3 ideas:

1. {{Idea1}}
2. {{Idea2}}
3. {{Idea3}}

Think any of these could be worth implementing?

Best regards,
{{accountSignature}}"""
            }
        ]
    }
]

# Create campaign (lands as DRAFT, status 0; nothing sends)
sequences = build_sequence(steps)
campaign = api.create_campaign("My New Campaign", sequences)
print(f"Created DRAFT: {campaign['id']}")

# Add a lead with custom variables
api.add_lead(
    campaign_id=campaign["id"],
    email="john@acme.com",
    first_name="John",
    last_name="Doe",
    company_name="Acme Corp",
    payload={
        "Idea1": "Flag accounts that just raised a round",
        "Idea2": "Route inbound demo requests by territory",
        "Idea3": "Re-engage closed-lost deals after a champion moves"
    }
)

# Activation is a separate, explicit step: only after the user says go.
# api.activate_campaign(campaign["id"], user_said_go=True)

# Check analytics
stats = api.campaign_analytics(campaign["id"])
print(f"Replies: {stats[0]['reply_count']} / {stats[0]['contacted_count']}")
```

---

## Benchmarks (from a few hundred B2B campaigns)

| Metric | Kill | Keep | Scale |
|--------|------|------|-------|
| Positive reply rate | <1% | 2-5% | >5% |
| Emails per positive reply | >5,000 | 1,000-3,000 | <1,000 |
| Meeting book rate | <0.5% | 1-2% | >2% |

**Top framework:** three AI-generated, prospect-specific ideas (`{{Idea1}}`, `{{Idea2}}`, `{{Idea3}}`) — outperformed all other templates across 43 campaigns analyzed.

---

## Common Gotchas

1. **Timezone:** Use `America/Detroit`, not `America/New_York`
2. **Activate/Pause:** Must send empty JSON body `{}`
3. **Delete lead:** Must NOT send body or Content-Type header
4. **Leads endpoint:** Use `POST /leads/list` to list/search (GET /leads returns 404)
5. **HTML escaping:** `>` in email body must be `&gt;` (e.g., "Quality &gt; volume")
6. **Schedule days:** Zero-indexed from Sunday (1=Monday, not 0=Monday)
7. **Daily limit 9999:** This is per-campaign; individual account limits still apply
8. **MCP tools:** The Instantly MCP integration may show Unauthorized — use direct API calls via curl as fallback
9. **Lead field name:** V2 API uses `campaign` NOT `campaign_id` when adding leads. Using `campaign_id` silently adds leads to the org pool without linking to the campaign.
10. **Lead dedup:** By default, Instantly deduplicates leads across campaigns. Set `skip_if_in_campaign: false` to force-add leads even if they exist in other campaigns.
11. **Unknown body params are silently ignored** — `/leads/list` with `campaign_id` doesn't error, it just returns the whole workspace unfiltered. If a "filtered" query is returning far more rows than expected, the param name is wrong (it's `campaign`).
12. **Python urllib gets 403** (Cloudflare blocks the UA) on some endpoints even with a valid key — campaigns may work while `/leads/list` is refused. Use curl (like `aiark.py` does). Never conclude the key is dead from a urllib 403.
13. **Move jobs serialize per campaign:** a second `POST /leads/move` while one is running returns 409 — wait and retry.
14. **`GET /emails` is rate-limited to 20 req/min** and a 429 comes back as a 200-shaped JSON body (`{"statusCode":429,...}`) with no `items` — naive pagination silently stops at ~1,900 rows looking complete. Throttle to ~3s/page, detect `statusCode` in the body, back off and resume (the `next_starting_after` cursor is just the last item's UUIDv7 `id`, so a chain can be resumed statelessly). Cross-check the final row count against `GET /campaigns/analytics` before trusting an export.
15. **`/emails` `ue_type` values:** `1` = campaign send, `2` = reply received, `3` = sent from unibox (manual reply/forward).
