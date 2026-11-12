---
name: lemlist-campaign-builder
description: Build a complete lemlist campaign end-to-end via the API — create the campaign, configure senders/tracking/schedule, craft all sequence steps (email + multichannel LinkedIn invite/message/conditional branches), load leads with custom variables, and (only on the user's explicit go) launch. Use when you need to PROGRAMMATICALLY create or load a lemlist campaign (not just report on one). Complements the read-only `lemlist` skill (analytics/exports).
---

# Lemlist Campaign Builder

Build a campaign from scratch through the lemlist API: create → configure → craft steps → load leads → launch. Scraped and verified from `developer.lemlist.com` (June 2026).

> **IMPORTANT — supersedes an old gotcha.** Older notes (and some forum answers) say "lemlist API creates campaign shells only; sequence steps are UI-only (405)." **That is no longer true.** The current API has `POST /sequences/{sequenceId}/steps` (add step), `PATCH` (update), `DELETE`, plus conditional branches. You can build the entire sequence — email AND LinkedIn — via API.

**Base URL:** `https://api.lemlist.com/api`
**Auth:** HTTP **Basic** (NOT Bearer). Username empty, password = API key. Build `:YOUR_API_KEY` (leading colon), Base64-encode it, send `Authorization: Basic <base64>`.
**Rate limit:** 20 requests / 2 seconds per key. Add ~0.12s between calls; honor `Retry-After` on 429.
**API version:** use v2. Some GET endpoints default to v1 and need `?version=v2`; the write endpoints below do not.
**Key:** `LEMLIST_API_KEY`, resolved in Python with `gtm.cred("LEMLIST_API_KEY")` (environment, then
`~/.magna-gtm-config`, then the `api_keys` table). Missing? `python3 gtm.py set-key LEMLIST_API_KEY` (value on stdin).

> 🚨 **Send guard.** Every campaign is built as a DRAFT: `autoReview: false`, and `POST /campaigns/{id}/start`
> is never called until the user explicitly says go for that campaign. Building, configuring, adding steps
> and loading leads are all safe while the campaign is not started; starting it sends to real prospects.

```python
import sys, requests
from requests.auth import HTTPBasicAuth
sys.path.insert(0, "<repo root>"); import gtm
API = "https://api.lemlist.com/api"
auth = HTTPBasicAuth("", gtm.cred("LEMLIST_API_KEY"))   # empty user, key as password
```

---

## The build flow (order matters)

1. **Create campaign** → returns `campaignId` (`cam_`), `sequenceId` (`seq_`), `scheduleIds`. An empty sequence + default schedule are auto-created.
2. **Configure** the campaign (senders, tracking, stop conditions) — PATCH.
3. **(Optional) Schedule** — a default schedule exists; create/associate a custom one only if needed.
4. **Craft sequence steps** — POST each step to the sequence (email / LinkedIn / conditional branches).
5. **Load leads** — POST each lead into the campaign (+ custom variables if any).
6. **Launch** — ONLY after the user explicitly says go: POST start. Never rely on auto-launch (`autoReview`) by default.

---

## 1. Create campaign

```
POST /campaigns
{
  "name": "Customer | V1 CIO | EU/UK | LinkedIn",
  "timezone": "Europe/London",           // IANA; defaults to Europe/Paris
  "autoReview": false,                    // KEEP false. true = auto-launch leads on add (sends with no review)
  "autoReviewConditions": ["deliverable","risky"]   // only auto-launch leads matching these email statuses
}
```
Response includes `_id` (campaignId), `sequenceId`, `scheduleIds`. **Save the `sequenceId`** — you add steps to it.

- `autoReview: true` = "auto launch mode": leads start sending the moment they're added, no manual review. It bypasses the draft guard, so never set it unless the user explicitly asks for it (and you risk spamming → account suspension on an untrusted list).
- `autoReviewConditions`: `deliverable` | `risky` | `undeliverable` | `unverified`.

## 2. Configure campaign (senders + tracking + stop rules)

```
PATCH /campaigns/{campaignId}
{
  "sendUserIds": ["usr_xxx"],        // assign the sending mailbox(es)/LinkedIn sender. Each sender must cover the campaign's channels.
  "disableTrackOpen": true,          // default stance: open-tracking OFF for email (deliverability)
  "disableTrackClick": false,
  "stopOnEmailReplied": true,
  "stopOnMeetingBooked": true
}
```
`sendUserIds` are user IDs (`usr_xxx`) — get them from `GET /team/senders`. A sender is validated against the campaign's channels (email, LinkedIn, SMS, WhatsApp); all channels must be covered.

## 3. Schedule (optional — a default one is auto-created)

```
POST /schedules
{ "name":"EU business hours","timezone":"Europe/London","start":"09:00","end":"17:00","weekdays":[1,2,3,4,5],"secondsToWait":1200,"public":false }
→ returns skd_xxx

POST /campaigns/{campaignId}/schedules/{scheduleId}   // associate it
```
`weekdays`: 1=Mon … 7=Sun. `start`/`end`: `HH:mm`. `secondsToWait`: gap between sends.

## 4. Craft sequence steps  ← the part that used to be "UI-only"

```
POST /sequences/{sequenceId}/steps
```
Common fields: `type` (required), `index` (position, omit to append), `delay` (days before step, 0–1500; default 0 for first step, 1 after).

### Step types + required fields
| type | required | notes |
|---|---|---|
| `email` | `subject`, `message` | `message` is **HTML** |
| `linkedinInvite` | — | connection request; `message` optional (omit/empty = **blank invite**) |
| `linkedinSend` | `message` | LinkedIn DM; `message` is **plain text** (`\n` for breaks); `altMessage` optional fallback |
| `linkedinVisit` | — | profile visit |
| `conditional` | `conditionKey`, `delayType` | branches the sequence (see below) |
| `linkedinFollow` / `linkedinLikeLastPost` / `linkedinCommentLastPost` / `linkedinEndorse` / `linkedinWithdrawInvitation` / `linkedinVoiceNote` | — | various LinkedIn actions |
| `sendToAnotherCampaign` | `campaignId` | hand the lead to another campaign |
| `whatsappMessage` / `sms` | `message` | |
| `manual` | `title` | manual task |
| `phone` | — | call reminder |
| `api` | `method`, `url` | webhook step |

> **Naming gotcha:** the Step *object definition* calls the LinkedIn-message type `linkedinMessage`, but the **create/update step endpoint uses `linkedinSend`**. When building, use **`linkedinSend`**.

### Email step example
```
{ "type":"email", "index":0, "delay":0,
  "subject":"{{firstName}}, quick one on {{companyName}}",
  "message":"<p>Hi {{firstName}},</p><p>...</p>" }
```

### Conditional branch — the LinkedIn "invite → on accept → messages" flow
A standard 4-touch LinkedIn arc: TOUCH 1 blank invite → TOUCH 2 on accept → TOUCH 3 +3d → TOUCH 4 +4d.

```
# 1) blank connection request
POST /sequences/{mainSeqId}/steps  { "type":"linkedinInvite", "delay":0 }

# 2) branch on acceptance
POST /sequences/{mainSeqId}/steps  { "type":"conditional", "conditionKey":"linkedinInviteAccepted", "delayType":"waitUntil" }
# → returns conditions: [ {sequenceId: seqAccepted, key:"linkedinInviteAccepted"}, {sequenceId: seqFallback, fallback:true} ]

# 3) messages in the ACCEPTED branch
POST /sequences/{seqAccepted}/steps  { "type":"linkedinSend", "delay":0, "message":"TOUCH 2 ..." }
POST /sequences/{seqAccepted}/steps  { "type":"linkedinSend", "delay":3, "message":"TOUCH 3 ..." }
POST /sequences/{seqAccepted}/steps  { "type":"linkedinSend", "delay":4, "message":"TOUCH 4 ..." }
```
`conditionKey` options: `linkedinInviteAccepted`, `linkedinOpened`, `emailsOpened`, `emailsClicked`, `meetingBooked`, `hasEmailAddress`, `hasLinkedinUrl`, `hasPhoneNumber`, `hasScore`, `linkedinNetworkCheck`, etc. `delayType`: `waitUntil` (wait for the condition) or `within` (needs a `delay`).

Update a step: `PATCH /sequences/{sequenceId}/steps/{stepId}` (must include `type`; type cannot be changed). Delete: `DELETE /sequences/{sequenceId}/steps/{stepId}`. Inspect: `GET /campaigns/{campaignId}/sequences`.

### Merge tags
Use `{{firstName}}`, `{{lastName}}`, `{{companyName}}`, `{{companyDomain}}`, `{{linkedinUrl}}`, `{{senderName}}`, `{{icebreaker}}`, etc. Liquid syntax supported. (These default vars exist automatically once a lead has them — no setup needed.)

## 5. Load leads

```
POST /campaigns/{campaignId}/leads/
{ "email":"j@acme.com","firstName":"John","lastName":"Doe","companyName":"Acme","jobTitle":"CIO",
  "linkedinUrl":"https://www.linkedin.com/in/johndoe","companyDomain":"acme.com","timezone":"Europe/London" }
```
Query params: `deduplicate=true` (skip if email already in another campaign), `findEmail`, `verifyEmail`, `findPhone`, `linkedinEnrichment`. Returns `_id` (`lea_`).

- **Default lead fields** (usable as merge tags immediately): `email`, `firstName`, `lastName`, `companyName`, `companyDomain`, `phone`, `linkedinUrl`, `picture`, `icebreaker`, `jobTitle`, `timezone`.
- **For LinkedIn-only campaigns**, `linkedinUrl` is the key field; email may be unused but lemlist generally expects one on the lead.

### Custom variables (only if you need fields beyond the defaults)
```
POST  /leads/{leadId}/variables   { "persona":"CIO", "trigger":"hiring a data engineer" }   # CREATE new vars
PATCH /leads/{leadId}/variables   { "persona":"CDO" }                                        # UPDATE values
```
You **cannot** create a custom var with the same name as a default/existing one. Copy that only uses `{{firstName}}` + `{{companyName}}` (both default) needs **no custom variables.**

## 6. Launch

```
POST /campaigns/{campaignId}/start     # → { "_id":"cam_...", "state":"running" }
```
🚨 This sends to real prospects. Call it only after the user explicitly says go for this campaign;
until then the campaign stays a draft. (`autoReview:true` at creation would launch leads automatically
as they're added, which skips that go, so don't use it unless asked.) Pause: `POST /campaigns/{campaignId}/pause`.

---

## Reference build script (skeleton)

```python
import requests, time
from requests.auth import HTTPBasicAuth
import sys; sys.path.insert(0, "<repo root>"); import gtm
API="https://api.lemlist.com/api"; auth=HTTPBasicAuth("", gtm.cred("LEMLIST_API_KEY"))
def post(path, body=None, params=None):
    r=requests.post(f"{API}{path}", json=body, params=params, auth=auth); r.raise_for_status(); time.sleep(0.12); return r.json()
def patch(path, body): r=requests.patch(f"{API}{path}", json=body, auth=auth); r.raise_for_status(); time.sleep(0.12); return r.json()

# 1. create
c = post("/campaigns", {"name":name, "timezone":tz, "autoReview":False})
cam, seq = c["_id"], c["sequenceId"]
# 2. configure (open-tracking off, stop on reply)
patch(f"/campaigns/{cam}", {"sendUserIds":[sender_id], "disableTrackOpen":True, "stopOnEmailReplied":True})
# 4. steps — LinkedIn arc
post(f"/sequences/{seq}/steps", {"type":"linkedinInvite","delay":0})
cond = post(f"/sequences/{seq}/steps", {"type":"conditional","conditionKey":"linkedinInviteAccepted","delayType":"waitUntil"})
accepted = next(b["sequenceId"] for b in cond["conditions"] if b.get("key")=="linkedinInviteAccepted")
post(f"/sequences/{accepted}/steps", {"type":"linkedinSend","delay":0,"message":touch2})
post(f"/sequences/{accepted}/steps", {"type":"linkedinSend","delay":3,"message":touch3})
post(f"/sequences/{accepted}/steps", {"type":"linkedinSend","delay":4,"message":touch4})
# 5. leads
for L in leads:
    post(f"/campaigns/{cam}/leads/", {"email":L["email"],"firstName":L["firstName"],"companyName":L["companyName"],"linkedinUrl":L["linkedinUrl"]}, params={"deduplicate":"true"})
# 6. launch: ONLY after the user explicitly says go. Leave commented until then.
# post(f"/campaigns/{cam}/start")
```

---

## Build notes
- **Where things live:** copy for a play goes in `plays/<play-slug>/campaigns/`; the lead CSV in `plays/<play-slug>/leads/contacts/`.
- **Persona x region:** one campaign per persona and region (e.g. 4 personas × EU/UK + USA = 8). Each = blank `linkedinInvite` → `conditional linkedinInviteAccepted (waitUntil)` → 3× `linkedinSend` (TOUCH 2 delay 0, TOUCH 3 delay 3, TOUCH 4 delay 4).
- **Sender:** assign the LinkedIn sending profile via `sendUserIds`; confirm that person's LinkedIn is connected as a sender in your Lemlist team first (`GET /team/senders`).
- **No em-dashes** in any message (they read as machine-written).

## Gotchas
- Auth is **Basic**, not Bearer. Empty username, leading colon before the key, Base64.
- Rate limit 20/2s — throttle ~0.12s, retry on 429.
- LinkedIn message type for creation is **`linkedinSend`** (object def says `linkedinMessage` — don't use that to create).
- `linkedinInvite` `message` is optional → omit for a **blank** connection request.
- Email `message` is HTML; LinkedIn `message` is plain text.
- Conditional steps return sub-sequence IDs — add follow-up steps to the **accepted** branch's `sequenceId`, not the main one.
- `autoReview:true` sends immediately on lead-add and bypasses the draft guard — keep it `false` unless the user explicitly asks.
- Lead custom vars: `POST` to create, `PATCH` to update; cannot reuse a default var name.
