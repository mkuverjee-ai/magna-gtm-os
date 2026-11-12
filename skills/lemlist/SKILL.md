---
name: lemlist
description: Lemlist API — Campaign analytics, lead management, sequences, activities, and reporting. Full API reference with authentication, rate limits, and all reporting endpoints.
---

# Lemlist API Skill

## Overview

Lemlist (`api.lemlist.com`) is the multichannel (email + LinkedIn) outreach platform you run alongside Instantly, in your own Lemlist team. This skill covers campaign analytics, lead management, sequence data, and activity tracking via the REST API.

**Base URL:** `https://api.lemlist.com/api`
**Auth:** HTTP Basic Authentication (empty username, API key as password)
**Rate Limit:** 20 requests per 2 seconds per API key
**Content-Type:** `application/json`

---

## Authentication

Lemlist uses **HTTP Basic Auth** — NOT Bearer tokens.

- **Username:** empty (blank)
- **Password:** your API key
- Format the credentials string as `:YourApiKey`, then Base64 encode it
- Header: `Authorization: Basic {base64-encoded-credentials}`
- **Key name:** `LEMLIST_API_KEY`. Python resolves it with `gtm.cred("LEMLIST_API_KEY")` from repo-root
  `gtm.py` (environment, then `~/.magna-gtm-config`, then the `api_keys` table). In a shell command use
  `-u ":$(python3 gtm.py key LEMLIST_API_KEY --raw)"` inline, never echoed. Missing? Add it with
  `python3 gtm.py set-key LEMLIST_API_KEY` (value on stdin).

### Python Example

```python
import sys, requests
from requests.auth import HTTPBasicAuth
sys.path.insert(0, "<repo root>")
import gtm

API_KEY = gtm.cred("LEMLIST_API_KEY")
BASE_URL = "https://api.lemlist.com/api"

# requests library handles Basic Auth encoding automatically
response = requests.get(
    f"{BASE_URL}/campaigns",
    auth=HTTPBasicAuth("", API_KEY)
)
```

### curl Example

```bash
# Let curl handle Basic Auth
curl -u ":YOUR_API_KEY" https://api.lemlist.com/api/campaigns

# Or manually with Base64
curl -H "Authorization: Basic $(echo -n ':YOUR_API_KEY' | base64)" \
     https://api.lemlist.com/api/campaigns
```

---

## Rate Limits

- **20 requests per 2 seconds** (per API key, all endpoints)
- Response headers on every request:
  - `Retry-After` — seconds before you can retry
  - `X-RateLimit-Limit` — max allowed requests in window
  - `X-RateLimit-Remaining` — requests still available
  - `X-RateLimit-Reset` — timestamp when limit resets
- **Recommended delay:** 0.12s between requests (~8-9 req/s, safe margin)

---

## Campaign Statuses

| Status | Description |
|--------|-------------|
| `running` | Currently sending |
| `paused` | Manually paused |
| `draft` | Created but not active |
| `ended` | Completed |
| `archived` | Archived |
| `errors` | Has sending errors |

---

## Endpoints

### Campaigns

#### `GET /campaigns` — List All Campaigns

```bash
curl -u ":API_KEY" "https://api.lemlist.com/api/campaigns?version=v2&limit=100"
```

**Query params:**

| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `offset` | int | 0 | Pagination offset |
| `limit` | int | 100 | Max results (max 100) |
| `version` | string | — | Set to `v2` for latest |
| `page` | int | — | Page number |
| `sortBy` | string | — | Sort field (only `createdAt` supported) |
| `sortOrder` | string | asc | `desc` for newest first |
| `status` | string | — | Filter: running, draft, archived, ended, paused, errors |

**Response:** Array of campaign objects:
```json
[
  {
    "_id": "cam_xxx",
    "name": "Product Launch Campaign",
    "labels": [],
    "createdAt": "2025-02-20T14:45:54.230Z",
    "createdBy": "usr_xxx",
    "status": "running",
    "sequenceId": "seq_abc123",
    "scheduleIds": [],
    "teamId": "tea_xxx",
    "hasError": false,
    "errors": [],
    "creator": { "userId": "usr_xxx", "userEmail": "user@example.com" },
    "senders": [{ "id": "snd_xxx", "email": "sender@domain.com", "sendUserMailboxId": "mbx_xxx" }]
  }
]
```

---

#### `GET /campaigns/{campaignId}` — Get Single Campaign

```bash
curl -u ":API_KEY" "https://api.lemlist.com/api/campaigns/{campaignId}"
```

Returns full campaign object (same schema as list).

---

#### `GET /v2/campaigns/{campaignId}/stats` — Campaign Stats (V2)

**This is the primary reporting endpoint.** Returns comprehensive lead and message metrics.

```bash
curl -u ":API_KEY" \
  "https://api.lemlist.com/api/v2/campaigns/{campaignId}/stats?startDate=2024-01-01T00:00:00.000Z&endDate=2026-12-31T23:59:59.999Z"
```

**Query params:**

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `startDate` | ISO 8601 | **Yes** | Start date |
| `endDate` | ISO 8601 | **Yes** | End date |
| `sendUser` | string | No | Filter by sender: `userId\|email` |
| `ABSelected` | string | No | A/B filter: `A` or `B` |
| `channels` | string | No | JSON array: `["email","linkedin","others"]` |

**Response:**
```json
{
  "nbLeads": 32,
  "nbLeadsLaunched": 32,
  "nbLeadsReached": 32,
  "nbLeadsOpened": 31,
  "nbLeadsInteracted": 4,
  "nbLeadsAnswered": 16,
  "nbLeadsInterested": 1,
  "nbLeadsNotInterested": 0,
  "nbLeadsUnsubscribed": 1,
  "nbLeadsInterrupted": 1,
  "messagesSent": 72,
  "messagesNotSent": 0,
  "messagesBounced": 0,
  "delivered": 72,
  "opened": 47,
  "clicked": 4,
  "replied": 16,
  "invitationAccepted": 0,
  "meetingBooked": 0,
  "steps": [
    {
      "index": 0,
      "sequenceId": "seq_xxx",
      "sequenceStep": 0,
      "taskType": "email",
      "abTest": "A",
      "conditionLabel": "",
      "invited": 0,
      "sent": 32,
      "delivered": 32,
      "opened": 28,
      "clicked": 2,
      "replied": 10,
      "notDelivered": 0,
      "bounced": 0,
      "unsubscribed": 0
    }
  ]
}
```

**Key metrics to calculate:**
- **Reply rate:** `replied / delivered`
- **Open rate:** `opened / delivered`
- **Click rate:** `clicked / delivered`
- **Bounce rate:** `messagesBounced / messagesSent`
- **Interest rate:** `nbLeadsInterested / nbLeadsReached`

---

#### `GET /campaigns/reports` — Multi-Campaign Reports

Get reports for multiple campaigns in one call.

```bash
curl -u ":API_KEY" \
  "https://api.lemlist.com/api/campaigns/reports?campaignIds={campaignId1},{campaignId2},{campaignId3}"
```

**Query params:**

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `campaignIds` | string | **Yes** | Comma-separated campaign IDs |

**Response:** Array of report objects:
```json
[
  {
    "_id": "cam_xxx",
    "name": "Campaign Name",
    "creator": "usr_xxx|user@example.com",
    "createdAt": "2025-02-20T14:45:54.230Z",
    "createdBy": "User Name",
    "labels": "",
    "totalCount": 500,
    "reviewedCount": 450,
    "inSequenceLeadCount": 200,
    "state": "running",
    "status": "running",
    "senderNames": "sender1@domain.com,sender2@domain.com",
    "sendersUsers": "User1,User2",
    "emailsSent": 1200,
    "emailsOpened": 800,
    "emailsClicked": 45,
    "emailsReplied": 60,
    "emailsUnsubscribed": 5,
    "emailsInterested": 15,
    "linkedinSent": 100,
    "linkedinOpened": 80,
    "linkedinReplied": 12,
    "interested": 15,
    "notInterested": 3
  }
]
```

---

### Leads

#### `GET /campaigns/{campaignId}/export/leads` — Export Campaign Leads

Export all leads from a campaign as CSV or JSON, with optional state filtering.

```bash
# Export all leads as JSON
curl -u ":API_KEY" \
  "https://api.lemlist.com/api/campaigns/{campaignId}/export/leads?state=all&format=json"

# Export only interested leads
curl -u ":API_KEY" \
  "https://api.lemlist.com/api/campaigns/{campaignId}/export/leads?state=interested&format=json"

# Export multiple states
curl -u ":API_KEY" \
  "https://api.lemlist.com/api/campaigns/{campaignId}/export/leads?state=emailsReplied,interested&format=json"
```

**Query params:**

| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `state` | string | `all` | Filter by lead state (comma-separated) |
| `format` | string | `csv` | Output format: `json` or `csv` |

**Valid states:**
- **Global:** imported, scanned, skipped, reviewed, contacted, hooked, attracted, warmed, interested, notInterested, emailsBounced, emailsUnsubscribed, failed, meetingBooked, paused
- **Detailed:** emailsSent, emailsOpened, emailsClicked, emailsReplied, emailsInterested, emailsNotInterested, emailsFailed, linkedinVisitDone, linkedinInviteDone, linkedinInviteAccepted, linkedinSent, linkedinOpened, linkedinReplied, linkedinInterested, linkedinNotInterested

**Response fields:**

| Field | Type | Description |
|-------|------|-------------|
| `email` | string | Lead email |
| `firstName` | string | First name |
| `lastName` | string | Last name |
| `companyName` | string | Company |
| `companyDomain` | string | Domain |
| `jobTitle` | string | Title |
| `phone` | string | Phone |
| `linkedinUrl` | string | LinkedIn URL |
| `emailStatus` | string | deliverable, risky, undeliverable |
| `lastState` | string | Final lead state |
| `status` | string | Current status |
| `_id` | string | Lead ID |

---

#### Deleting a lead from a campaign — use `?action=remove`

```bash
# Remove the lead from the campaign (what you almost always want)
curl -X DELETE -u ":API_KEY" \
  "https://api.lemlist.com/api/campaigns/{campaignId}/leads/{leadId}?action=remove"
```

Without `?action=remove` the same path is treated as an **unsubscribe**, not a removal, and fails on
any lead that has no email address:

```json
{"error": "An email is required to unsub a lead"}   // HTTP 404
```

LinkedIn-only leads (`state: linkedinInviteDone`, no `email` field) are common in multichannel
campaigns and can *only* be deleted with `?action=remove`. The `{leadId}` form (`lea_…`) works;
you do not need the email. Verified 2026-09-09.

---

#### `POST /unsubscribes/{value}` — Block an email or a whole domain

The value goes **in the path**, not a body. Prefix with `@` to block an entire domain:

```bash
# Block one address
curl -X POST -u ":API_KEY" "https://api.lemlist.com/api/unsubscribes/john@acme.com"

# Block every address at a domain
curl -X POST -u ":API_KEY" "https://api.lemlist.com/api/unsubscribes/@acme.com"

# List / remove
curl -u ":API_KEY" "https://api.lemlist.com/api/unsubscribes?page=1&limit=100"
curl -X DELETE -u ":API_KEY" "https://api.lemlist.com/api/unsubscribes/@acme.com"
```

Returns `{"_id": "uns_…", "value": "@acme.com", "email": "@acme.com"}`; the listing shows
`source: "api"`.

**This is Lemlist's only exclusion mechanism, and it is semantically an *unsubscribe*.** Entries
count toward `nbLeadsUnsubscribed` in campaign stats, so a large bulk import of exclusion domains
will inflate the unsubscribe metric and distort reporting. Note it in the report when you do it.

Lemlist's unsubscribe list is **per-workspace and entirely separate from Instantly's block list**.
Running both platforms means the exclusion list must be applied twice — check both before assuming
a domain is suppressed.

---

#### `GET /leads` — Get Lead by Email or ID

```bash
# By email
curl -u ":API_KEY" "https://api.lemlist.com/api/leads?email=john@company.com&version=v2"

# By ID
curl -u ":API_KEY" "https://api.lemlist.com/api/leads?id=lea_123&version=v2"
```

**Query params:**

| Param | Type | Description |
|-------|------|-------------|
| `email` | string | Lead email (takes precedence if both provided) |
| `id` | string | Lead ID |
| `version` | string | Set to `v2` |

**Response:**
```json
{
  "firstName": "John",
  "lastName": "Doe",
  "companyName": "Acme Corp",
  "jobTitle": "CFO",
  "companyDomain": "acme.com",
  "email": "john@acme.com",
  "_id": "lea_xxx",
  "isPaused": false,
  "campaignId": "cam_xxx",
  "contactId": "ctc_xxx",
  "emailStatus": "deliverable"
}
```

---

### Activities

#### `GET /activities` — Get Activities

```bash
curl -u ":API_KEY" \
  "https://api.lemlist.com/api/activities?version=v2&campaignId={campaignId}&limit=100"
```

**Query params:**

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `version` | string | **Yes** | Must be `v2` |
| `type` | string | No | Filter: emailOpened, emailClicked, emailReplied, paused, etc. |
| `campaignId` | string | No | Filter by campaign |
| `isFirst` | boolean | No | First activity only |
| `offset` | int | No | Pagination offset |
| `limit` | int | No | Max 100 (default 100) |
| `leadId` | string | No | Filter by lead |

**Response:** Array of activity objects:
```json
[
  {
    "_id": "act_xxx",
    "type": "emailReplied",
    "leadId": "lea_xxx",
    "campaignId": "cam_xxx",
    "sequenceId": "seq_xxx",
    "stepId": "stp_xxx",
    "createdAt": "2025-02-20T14:45:54.230Z"
  }
]
```

---

### Sequences

#### `GET /campaigns/{campaignId}/sequences` — Get Campaign Sequences

```bash
curl -u ":API_KEY" "https://api.lemlist.com/api/campaigns/{campaignId}/sequences"
```

**Response:** Object keyed by sequence IDs:
```json
{
  "seq_xxx": {
    "_id": "seq_xxx",
    "steps": [
      {
        "_id": "stp_xxx",
        "delay": 2,
        "type": "email",
        "index": 0,
        "sequenceId": "seq_xxx",
        "sequenceStep": 0,
        "subject": "Subject line",
        "message": "<p>Email body HTML</p>"
      }
    ],
    "level": 0
  }
}
```

**Step fields:**

| Field | Type | Description |
|-------|------|-------------|
| `_id` | string | Step ID |
| `delay` | int | Days before execution |
| `type` | string | email, linkedinSend, linkedinInvite, conditional, manual |
| `index` | int | Position in sequence |
| `sequenceStep` | int | Step number |
| `subject` | string | Email subject (email type only) |
| `message` | string | Body (HTML for email, plain text for LinkedIn) |

---

### Team

#### `GET /team/senders` — Get Team Senders

```bash
curl -u ":API_KEY" "https://api.lemlist.com/api/team/senders?state=running"
```

**Query params:**

| Param | Type | Description |
|-------|------|-------------|
| `state` | string | Filter by campaign state: running, paused, draft, ended, archived, errors |

**Response:**
```json
[
  {
    "userId": "usr_xxx",
    "campaigns": [
      {
        "_id": "cam_xxx",
        "name": "Campaign Name",
        "status": "running",
        "sendingChannels": ["email", "linkedinVisit", "linkedinSend"]
      }
    ]
  }
]
```

---

### Exports

#### `GET /campaigns/{campaignId}/export/start` — Start Stats Export

Triggers an async export of campaign stats.

```bash
curl -u ":API_KEY" "https://api.lemlist.com/api/campaigns/{campaignId}/export/start"
```

**Response:**
```json
{
  "_id": "axp_xxx",
  "campaignId": "cam_xxx",
  "campaignName": "Campaign Name",
  "status": "pending",
  "startedAt": "2024-07-09T13:43:52.124Z",
  "progress": 0,
  "total": 0
}
```

Export status values: `pending`, `done`, `error`

---

## Reporting Workflows

### 1. Full Campaign Performance Report

```
Step 1: GET /campaigns?version=v2&limit=100&sortBy=createdAt&sortOrder=desc
  → Get all campaigns with IDs and statuses

Step 2: For each campaign:
  GET /v2/campaigns/{id}/stats?startDate=...&endDate=...
  → Get lead metrics + message metrics + per-step breakdown

Step 3: Calculate key metrics:
  - Reply rate = replied / delivered
  - Open rate = opened / delivered
  - Bounce rate = messagesBounced / messagesSent
  - Interest rate = nbLeadsInterested / nbLeadsReached

Step 4: GET /campaigns/{id}/sequences
  → Get email copy (subjects + bodies) per step

Step 5: Cross-reference step stats with copy to identify winning variants
```

### 2. Quick Multi-Campaign Overview

```
Step 1: GET /campaigns?version=v2&limit=100
  → Get all campaign IDs

Step 2: GET /campaigns/reports?campaignIds={id1},{id2},...
  → Get aggregate metrics for all campaigns in one call
```

### 3. Lead-Level Analysis

```
Step 1: GET /campaigns/{id}/export/leads?state=all&format=json
  → Get all leads with their final states

Step 2: Segment by:
  - emailStatus (deliverable vs risky vs undeliverable)
  - lastState (interested, replied, bounced, etc.)
  - jobTitle, companyName for persona/account analysis
```

---

## Benchmarks (from a few hundred B2B campaigns)

| Metric | Kill | Keep | Scale |
|--------|------|------|-------|
| Positive reply rate | <1% | 2-5% | >5% |
| Open rate | <30% | 30-50% | >50% |
| Bounce rate | >5% | 2-5% | <2% |
| Interest rate | <0.5% | 0.5-2% | >2% |

---

## Common Gotchas

1. **Auth is Basic, not Bearer** — `requests.auth.HTTPBasicAuth("", api_key)`, NOT `Authorization: Bearer`
2. **Stats endpoint is v2** — use `/api/v2/campaigns/{id}/stats` (note the `/v2/` in path)
3. **startDate/endDate required** for stats — will 400 without them
4. **Rate limit 20/2s** — add 0.12s delay between requests
5. **Pagination max 100** — loop with offset for large datasets
6. **Campaign IDs** — always prefixed with `cam_`
7. **Lead states** — `interested` is the positive outcome; `emailsReplied` includes all replies (positive + negative)
8. **Export formats** — default is CSV; explicitly pass `format=json` for JSON
