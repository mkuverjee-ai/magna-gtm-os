---
name: lemlist-reporting
description: Lemlist campaign analytics and reporting endpoints. Use when pulling Lemlist performance data.
---

# Lemlist Reporting Skill

> **Purpose:** Pull campaign performance data from your Lemlist team via the REST API. Covers campaigns, sequences, leads, activities, and how to derive all reporting metrics. Save reports under `plays/<play-slug>/reports/`.

---

## Authentication

```
Base URL: https://api.lemlist.com/api
Auth: Basic authentication
  - Username: (empty)
  - Password: your API key
  - Header: Authorization: Basic <base64(":YOUR_API_KEY")>
```

The key is `LEMLIST_API_KEY`, resolved in Python with `gtm.cred("LEMLIST_API_KEY")` (environment, then
`~/.magna-gtm-config`, then the `api_keys` table). Missing? `python3 gtm.py set-key LEMLIST_API_KEY` (value on stdin).

**Python example:**
```python
import base64, sys, requests
sys.path.insert(0, "<repo root>")
import gtm

API_KEY = gtm.cred("LEMLIST_API_KEY")
AUTH = base64.b64encode(f":{API_KEY}".encode()).decode()
HEADERS = {"Authorization": f"Basic {AUTH}"}
BASE = "https://api.lemlist.com/api"

r = requests.get(f"{BASE}/campaigns", headers=HEADERS)
campaigns = r.json()
```

**cURL example:**
```bash
# key resolved inline, never echoed
AUTH=$(echo -n ":$(python3 gtm.py key LEMLIST_API_KEY --raw)" | base64)
curl -s "https://api.lemlist.com/api/campaigns" -H "Authorization: Basic $AUTH"
```

**Rate limit:** 20 requests per 2-second window per API key. Use 100ms delays between requests.

---

## Endpoint Reference

### 1. List All Campaigns

```
GET /campaigns
```

Returns an array of all campaigns in the account (no pagination — returns all at once).

**Response:**
```json
[
  {
    "_id": "cam_xxx",
    "name": "Campaign Name",
    "sequenceId": "seq_xxx",
    "labels": ["Event Plays", "Q1 2026"],
    "createdAt": "2024-12-19T23:01:08.225Z",
    "createdBy": "usr_xxx",
    "status": "paused"
  }
]
```

**Status values:**
| Status | Meaning |
|--------|---------|
| `draft` | Not yet launched |
| `running` | Currently sending |
| `paused` | Temporarily stopped |
| `ended` | Finished sending to all leads |
| `archived` | Hidden from default view |

---

### 2. Get Campaign Detail

```
GET /campaigns/{campaignId}
```

**Response:**
```json
{
  "_id": "cam_xxx",
  "name": "Campaign Name",
  "labels": ["Label1"],
  "createdAt": "2025-02-13T19:50:21.804Z",
  "status": "ended",
  "creator": {
    "userId": "usr_xxx",
    "userEmail": "user@company.com"
  },
  "senders": [
    {
      "id": "usr_xxx",
      "type": "linkedinVisit"
    },
    {
      "id": "usr_xxx",
      "email": "sender@company.com",
      "sendUserMailboxId": "usm_xxx"
    }
  ],
  "sendUsers": [
    {
      "id": "usr_xxx",
      "mailboxes": [
        {
          "email": "sender@company.com",
          "sendUserMailboxId": "usm_xxx"
        }
      ]
    }
  ],
  "senderStrategy": "random",
  "hasError": false,
  "errors": []
}
```

---

### 3. Campaign Export (THE KEY REPORTING ENDPOINT)

```
GET /campaigns/{campaignId}/export
```

**This is the primary reporting endpoint.** Returns a CSV with one row per lead and all engagement timestamps. There is NO dedicated analytics/stats JSON endpoint — you derive all metrics from this CSV.

**Response:** CSV text (not JSON)

**Lead info columns (first ~38):**
| Column | Description |
|--------|-------------|
| `email` | Lead email address |
| `firstName` | Lead first name |
| `lastName` | Lead last name |
| `companyName` | Company name |
| `companyDomain` | Company domain |
| `jobTitle` | Job title |
| `phone` | Phone number |
| `linkedinUrl` | LinkedIn profile URL |
| `companySize` | Company employee count |
| `companyIndustry` | Industry |
| `companyLinkedinUrl` | Company LinkedIn URL |
| `industry` | Lead industry |
| `location` | Lead location |
| `picture` | Profile picture URL |
| `icebreaker` | Custom icebreaker variable |
| `_id` | Internal lead ID (lea_xxx) |
| `notes` | Notes on the lead |
| `sentStep` | Number of steps sent |
| `sendUser` | Sender name:email |

**Aggregate engagement columns (across ALL steps):**
| Column | Description | Non-empty = |
|--------|-------------|-------------|
| `sentAt` | Timestamp of first email sent | Lead was contacted |
| `openedAt` | Timestamp of first open | Lead opened an email |
| `repliedAt` | Timestamp of first reply | Lead replied |
| `interestedAt` | Timestamp marked interested | Lead manually tagged as interested |
| `notInterestedAt` | Timestamp marked not interested | Lead manually tagged as not interested |
| `bouncedAt` | Timestamp of bounce | Email bounced |
| `unsubscribedAt` | Timestamp of unsubscribe | Lead unsubscribed |
| `clickedAt` | Timestamp of first click | Lead clicked a link |
| `clickedLink` | The URL that was clicked | — |
| `failedAt` | Timestamp of failure | Delivery failed |
| `failedMessage` | Failure reason | — |

**LinkedIn engagement columns (aggregate):**
| Column | Description |
|--------|-------------|
| `linkedinVisitAt` | Profile visit completed |
| `linkedinVisitFailedAt` | Profile visit failed |
| `linkedinInviteDoneAt` | Connection invite sent |
| `linkedinInviteFailedAt` | Invite failed |
| `linkedinInviteAcceptedAt` | Invite accepted |
| `linkedinSentAt` | LinkedIn message sent |
| `linkedinOpenedAt` | LinkedIn message opened |
| `linkedinRepliedAt` | LinkedIn reply received |
| `linkedinInterestedAt` | Marked interested via LinkedIn |
| `linkedinNotInterestedAt` | Marked not interested via LinkedIn |
| `linkedinFollowAt` | Profile followed |
| `linkedinLikeLastPostAt` | Last post liked |
| `linkedinCommentLastPostAt` | Last post commented |
| `linkedinEndorseAt` | Skills endorsed |

**Other channel columns (aggregate):**
| Column | Description |
|--------|-------------|
| `callDoneAt` | Call completed |
| `callInterestedAt` | Interested after call |
| `callNotInterestedAt` | Not interested after call |
| `apiDoneAt` | API step completed |
| `manualDoneAt` | Manual step completed |
| `meetingBooked` | Meeting booked timestamp |

**Per-step columns:**
Every engagement column repeats with a step number suffix: `sentAt1`, `repliedAt1`, `openedAt1`, `sentAt2`, `repliedAt2`, `openedAt2`, etc. up to the number of steps in the sequence (typically 3-8 steps).

This lets you calculate per-step performance (e.g., "Step 2 got more replies than Step 1").

---

### 4. Campaign Sequences

```
GET /campaigns/{campaignId}/sequences
```

Returns the email sequences (steps) for a campaign.

**Response:** Object keyed by sequence ID (NOT an array):
```json
{
  "seq_xxx": {
    "_id": "seq_xxx",
    "steps": [
      {
        "_id": "stp_xxx",
        "delay": 0,
        "emailTemplateId": "etp_xxx",
        "index": 1,
        "sequenceId": "seq_xxx",
        "sequenceStep": 0,
        "subject": "Subject line here",
        "message": "<div>HTML email body here</div>",
        "type": "email"
      },
      {
        "_id": "stp_yyy",
        "delay": 2,
        "sequenceStep": 1,
        "subject": "Follow-up subject",
        "message": "<p>Follow-up body</p>",
        "type": "email"
      }
    ],
    "level": 0
  }
}
```

**Step fields:**
| Field | Description |
|-------|-------------|
| `_id` | Step ID (stp_xxx) |
| `delay` | Days delay from previous step |
| `index` | 1-based display order |
| `sequenceStep` | 0-based step number |
| `subject` | Email subject line (email steps only) |
| `message` | HTML email body (email steps only) |
| `type` | Step type (see below) |

**Step types:**
- `email` — Email step (has subject + message)
- `linkedinVisit` — Visit LinkedIn profile
- `linkedinInvite` — Send connection request
- `linkedinMessage` — Send LinkedIn message
- `linkedinCommentLastPost` — Comment on last post
- `linkedinLikeLastPost` — Like last post
- `linkedinFollow` — Follow profile
- `linkedinEndorse` — Endorse skills
- `call` — Phone call task
- `manual` — Manual task
- `api` — API webhook step

**Important:** Only `email` and `linkedinMessage` type steps have `subject` and `message` fields. Filter by `type === "email"` when extracting email copy.

---

### 5. Campaign Leads

```
GET /campaigns/{campaignId}/leads?limit=100&offset=0
```

Returns leads in the campaign. Paginated.

**Response:**
```json
[
  {
    "_id": "lea_xxx",
    "state": "emailsSent",
    "contactId": "ctc_xxx"
  }
]
```

**Lead states:** `emailsSent`, `emailsReplied`, `emailsBounced`, `emailsNotSent`

**Note:** The leads endpoint returns minimal data. For full lead details, use the `/export` endpoint instead.

---

### 6. Activities (Live Event Stream)

```
GET /activities?limit=100&offset=0
```

Returns recent activities across all campaigns. Useful for real-time monitoring.

**Response:**
```json
[
  {
    "_id": "act_xxx",
    "type": "linkedinVisitDone",
    "isFirst": true,
    "createdAt": "2026-04-29T11:43:25.212Z",
    "teamId": "tea_xxx",
    "leadId": "lea_xxx",
    "campaignId": "cam_xxx",
    "sequenceStep": 0,
    "name": "Campaign Name",
    "sendUserName": "Sender Name",
    "leadFirstName": "Lead",
    "leadLastName": "Name",
    "leadEmail": "lead@company.com",
    "leadCompanyName": "Company Inc",
    "jobTitle": "VP Marketing",
    "campaignName": "Campaign Name"
  }
]
```

**Activity types:**
- `emailsSent` — Email sent
- `emailsOpened` — Email opened
- `emailsClicked` — Link clicked
- `emailsReplied` — Email reply received
- `emailsBounced` — Email bounced
- `emailsUnsubscribed` — Lead unsubscribed
- `emailsFailed` — Delivery failed
- `emailsInterested` — Marked interested
- `emailsNotInterested` — Marked not interested
- `linkedinVisitDone` — LinkedIn profile visited
- `linkedinInviteDone` — Connection invite sent
- `linkedinInviteAccepted` — Invite accepted
- `linkedinSent` — LinkedIn message sent
- `linkedinReplied` — LinkedIn reply
- `callDone` — Call completed
- `manualDone` — Manual task done
- `apiDone` — API step done

---

### 7. Team Info

```
GET /team
```

Returns team/account info including user count and creation date.

```json
{
  "_id": "tea_xxx",
  "name": "Team Name",
  "userIds": ["usr_xxx", ...],
  "createdAt": "2024-12-19T22:55:50.219Z",
  "hooks": [...]
}
```

---

### 8. Webhooks

```
GET /hooks
```

Returns configured webhooks.

```json
[
  {
    "_id": "hoo_xxx",
    "targetUrl": "https://example.com/webhook",
    "type": "emailsReplied",
    "createdAt": "2025-11-05T10:16:38.503Z"
  }
]
```

**Webhook event types:** `emailsReplied`, `emailsClicked`, `emailsBounced`, `emailsUnsubscribed`, `connectionIssue`, `linkedinInviteAccepted`

---

## How to Build a Campaign Report

### Step 1: Get all campaigns

```python
campaigns = requests.get(f"{BASE}/campaigns", headers=HEADERS).json()
```

### Step 2: For each campaign, get the export CSV

```python
import csv, io

def get_campaign_stats(campaign_id):
    r = requests.get(f"{BASE}/campaigns/{campaign_id}/export", headers=HEADERS)
    reader = csv.DictReader(io.StringIO(r.text))
    rows = list(reader)

    return {
        "total_leads": len(rows),
        "sent": sum(1 for r in rows if r.get("sentAt")),
        "opened": sum(1 for r in rows if r.get("openedAt")),
        "clicked": sum(1 for r in rows if r.get("clickedAt")),
        "replied": sum(1 for r in rows if r.get("repliedAt")),
        "interested": sum(1 for r in rows if r.get("interestedAt")),
        "not_interested": sum(1 for r in rows if r.get("notInterestedAt")),
        "bounced": sum(1 for r in rows if r.get("bouncedAt")),
        "unsubscribed": sum(1 for r in rows if r.get("unsubscribedAt")),
        "failed": sum(1 for r in rows if r.get("failedAt")),
        # LinkedIn
        "linkedin_visits": sum(1 for r in rows if r.get("linkedinVisitAt")),
        "linkedin_invites_sent": sum(1 for r in rows if r.get("linkedinInviteDoneAt")),
        "linkedin_invites_accepted": sum(1 for r in rows if r.get("linkedinInviteAcceptedAt")),
        "linkedin_messages_sent": sum(1 for r in rows if r.get("linkedinSentAt")),
        "linkedin_replies": sum(1 for r in rows if r.get("linkedinRepliedAt")),
        # Calls
        "calls_done": sum(1 for r in rows if r.get("callDoneAt")),
        "meetings_booked": sum(1 for r in rows if r.get("meetingBooked")),
    }
```

### Step 3: Calculate rates

```python
stats = get_campaign_stats("cam_xxx")
sent = stats["sent"]

report = {
    "open_rate": (stats["opened"] / sent * 100) if sent else 0,
    "click_rate": (stats["clicked"] / sent * 100) if sent else 0,
    "reply_rate": (stats["replied"] / sent * 100) if sent else 0,
    "bounce_rate": (stats["bounced"] / sent * 100) if sent else 0,
    "positive_rate": (stats["interested"] / sent * 100) if sent else 0,
    "unsubscribe_rate": (stats["unsubscribed"] / sent * 100) if sent else 0,
}
```

### Step 4: Per-step analysis

```python
def get_per_step_stats(campaign_id, num_steps=5):
    r = requests.get(f"{BASE}/campaigns/{campaign_id}/export", headers=HEADERS)
    reader = csv.DictReader(io.StringIO(r.text))
    rows = list(reader)

    step_stats = []
    for step in range(1, num_steps + 1):
        s = str(step)
        sent = sum(1 for r in rows if r.get(f"sentAt{s}"))
        if sent == 0:
            break
        step_stats.append({
            "step": step,
            "sent": sent,
            "opened": sum(1 for r in rows if r.get(f"openedAt{s}")),
            "replied": sum(1 for r in rows if r.get(f"repliedAt{s}")),
            "bounced": sum(1 for r in rows if r.get(f"bouncedAt{s}")),
            "clicked": sum(1 for r in rows if r.get(f"clickedAt{s}")),
            "linkedin_sent": sum(1 for r in rows if r.get(f"linkedinSentAt{s}")),
            "linkedin_replied": sum(1 for r in rows if r.get(f"linkedinRepliedAt{s}")),
        })
    return step_stats
```

### Step 5: Get email copy for each step

```python
def get_sequences(campaign_id):
    r = requests.get(f"{BASE}/campaigns/{campaign_id}/sequences", headers=HEADERS)
    data = r.json()
    # Response is { "seq_xxx": { steps: [...] } }
    steps = []
    for seq_id, seq in data.items():
        for step in seq.get("steps", []):
            if step.get("type") == "email":
                steps.append({
                    "step": step["sequenceStep"] + 1,
                    "delay_days": step.get("delay", 0),
                    "subject": step.get("subject", ""),
                    "body_html": step.get("message", ""),
                })
    return sorted(steps, key=lambda s: s["step"])
```

### Full Report Script

```python
import base64, requests, csv, io, json, time, re, sys
sys.path.insert(0, "<repo root>")
import gtm

API_KEY = gtm.cred("LEMLIST_API_KEY")
AUTH = base64.b64encode(f":{API_KEY}".encode()).decode()
HEADERS = {"Authorization": f"Basic {AUTH}"}
BASE = "https://api.lemlist.com/api"

def strip_html(html):
    text = re.sub(r'<br\s*/?>', '\n', html)
    text = re.sub(r'<[^>]+>', '', text)
    text = re.sub(r'&nbsp;', ' ', text)
    text = re.sub(r'&amp;', '&', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()

# 1. Get all campaigns
campaigns = requests.get(f"{BASE}/campaigns", headers=HEADERS).json()
print(f"Total campaigns: {len(campaigns)}")

report = []

for camp in campaigns:
    if camp["status"] == "archived":
        continue

    time.sleep(0.1)  # Rate limit

    # 2. Get export stats
    try:
        r = requests.get(f"{BASE}/campaigns/{camp['_id']}/export", headers=HEADERS)
        rows = list(csv.DictReader(io.StringIO(r.text)))
    except:
        rows = []

    sent = sum(1 for r in rows if r.get("sentAt"))
    replied = sum(1 for r in rows if r.get("repliedAt"))
    opened = sum(1 for r in rows if r.get("openedAt"))
    interested = sum(1 for r in rows if r.get("interestedAt"))
    bounced = sum(1 for r in rows if r.get("bouncedAt"))

    # 3. Get sequences
    time.sleep(0.1)
    try:
        seqs = requests.get(f"{BASE}/campaigns/{camp['_id']}/sequences", headers=HEADERS).json()
        email_steps = []
        for seq_id, seq in seqs.items():
            for step in seq.get("steps", []):
                if step.get("type") == "email":
                    email_steps.append({
                        "step": step["sequenceStep"] + 1,
                        "subject": step.get("subject", ""),
                        "body": strip_html(step.get("message", "")),
                    })
    except:
        email_steps = []

    report.append({
        "name": camp["name"],
        "status": camp["status"],
        "labels": camp.get("labels", []),
        "created": camp.get("createdAt", ""),
        "sent": sent,
        "opened": opened,
        "replied": replied,
        "interested": interested,
        "bounced": bounced,
        "open_rate": round(opened / sent * 100, 2) if sent else 0,
        "reply_rate": round(replied / sent * 100, 2) if sent else 0,
        "bounce_rate": round(bounced / sent * 100, 2) if sent else 0,
        "sequences": email_steps,
    })
    print(f"  [{camp['status']}] {camp['name']}: {sent} sent, {replied} replied ({round(replied/sent*100,1) if sent else 0}%)")

# 4. Save report
with open("lemlist_report.json", "w") as f:
    json.dump(report, f, indent=2)
print(f"\nSaved {len(report)} campaigns to lemlist_report.json")
```

---

## Key Gotchas

1. **The export CSV is the lead-level source of truth** — derive per-lead and per-step metrics from `/export`. For campaign-level totals there is also `GET /v2/campaigns/{id}/stats` (needs `startDate`/`endDate`; see the `lemlist` skill).

2. **Export returns CSV, not JSON** — Parse with `csv.DictReader`, not `json.loads()`.

3. **`interestedAt` is manual** — The "interested" field only gets set when someone manually tags a lead in the Lemlist UI. Many teams don't use it, so `interested` count may be 0 even with lots of replies. Use `replied` as the primary engagement metric.

4. **Sequences response is an object, not an array** — Response is `{ "seq_xxx": { steps: [...] } }`. Iterate with `.items()` or `Object.entries()`.

5. **Multi-channel steps** — Sequences can include LinkedIn, call, and API steps alongside email. Filter by `type === "email"` for email copy.

6. **Per-step columns use 1-based numbering** — `sentAt1`, `sentAt2`, etc. (not 0-based).

7. **Rate limit: 20 req / 2 sec** — Use 100ms delays between requests. With 100 campaigns, full export takes ~20 seconds.

8. **No pagination on campaign list** — `/campaigns` returns ALL campaigns in one response (no limit/offset needed).

9. **Labels are your categories** — Lemlist uses `labels` arrays on campaigns (e.g., `["Event Plays"]`). Use these for grouping/filtering.

10. **Draft campaigns have no export data** — Skip `/export` calls for campaigns with `status === "draft"`.

---

## Metric Definitions (for reporting)

| Metric | How to calculate |
|--------|-----------------|
| **Sent** | Count of rows where `sentAt` is not empty |
| **Opened** | Count of rows where `openedAt` is not empty |
| **Open Rate** | opened / sent × 100 |
| **Clicked** | Count of rows where `clickedAt` is not empty |
| **Click Rate** | clicked / sent × 100 |
| **Replied** | Count of rows where `repliedAt` is not empty |
| **Reply Rate** | replied / sent × 100 |
| **Interested (Positive)** | Count of rows where `interestedAt` is not empty |
| **Positive Rate** | interested / sent × 100 |
| **Not Interested** | Count of rows where `notInterestedAt` is not empty |
| **Bounced** | Count of rows where `bouncedAt` is not empty |
| **Bounce Rate** | bounced / sent × 100 |
| **Unsubscribed** | Count of rows where `unsubscribedAt` is not empty |
| **Failed** | Count of rows where `failedAt` is not empty |
| **Meetings Booked** | Count of rows where `meetingBooked` is not empty |
| **LinkedIn Acceptance Rate** | linkedin_invites_accepted / linkedin_invites_sent × 100 |
