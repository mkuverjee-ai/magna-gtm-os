---
name: lemlist-inbox
description: Lemlist inbox API — reading conversations, writing reply drafts, labels, webhooks, and (only on the user's explicit go) sending. Use when handling Lemlist replies programmatically.
---

# Lemlist Inbox API — SKILL.md

> **The write half of Lemlist.** The `lemlist` skill covers reading campaigns, stats, leads and activities. This file covers the **unified inbox**: reading conversations and **sending / replying** on email, LinkedIn and WhatsApp.
>
> Verified against the live OpenAPI spec at `developer.lemlist.com` on **2026-08-03**.

---

## ⚠️ READ THIS FIRST — sending reaches real prospects

Every endpoint in the "Sending" section below is a **write that puts a message in a real prospect's inbox** — the highest-consequence call in this OS. Replies are worked in the Lemlist inbox; the API's job is to read threads and prepare drafts there.

| Endpoint group | Safe to run freely? |
|---|---|
| `GET /inbox`, `GET /inbox/{contactId}`, `GET /inbox/labels` | ✅ Read-only |
| `POST /inbox/{contactId}/drafts` (+ PATCH/DELETE) | ⚠️ Writes, but only into the Lemlist UI. A human still hits Send. **This is the safe middle step.** |
| `POST /inbox/email`, `/inbox/linkedin`, `/inbox/whatsapp` | 🚨 **Sends to the prospect immediately. Only after the user explicitly says go for that exact message.** |

**Rule:** never wire a `POST /inbox/email` behind an automatic trigger. Default to the drafts endpoints: the draft appears in the Lemlist inbox and a human reviews and sends it there.

---

## Auth

Identical to the rest of the Lemlist API: **HTTP Basic, empty username, API key as password.** Not Bearer.

The key is `LEMLIST_API_KEY`, resolved by `gtm.cred("LEMLIST_API_KEY")` (environment, then
`~/.magna-gtm-config`, then the `api_keys` table). Missing? `python3 gtm.py set-key LEMLIST_API_KEY` (value on stdin).

```bash
# key resolved inline, never echoed
curl -u ":$(python3 gtm.py key LEMLIST_API_KEY --raw)" "https://api.lemlist.com/api/inbox"
```

```python
import sys, requests
sys.path.insert(0, "<repo root>"); import gtm
requests.get("https://api.lemlist.com/api/inbox", auth=("", gtm.cred("LEMLIST_API_KEY")))
```

In the curl examples below, `$KEY` stands for that inline `$(python3 gtm.py key LEMLIST_API_KEY --raw)`.

All routes live at `https://api.lemlist.com/api`. Rate limit **20 requests / 2 seconds** per API key (same bucket as the rest of the API — add ~0.12s between calls).

---

## The object model

Lemlist splits a person into two records. Getting this wrong is the #1 source of 400s.

| Object | Prefix | What it is |
|---|---|---|
| **Lead** | `lea_` | A person **inside a specific campaign**. One human in 3 campaigns = 3 leads. |
| **Contact** | `ctc_` | The person in the CRM. **One per human**, across all campaigns. The inbox is keyed on this. |
| **Activity** | `act_` | A single event (email sent, email replied, LinkedIn message). **This is what you reply to.** |
| **Mailbox** | `usm_` | A connected sending mailbox belonging to a user. |
| **User** | `usr_` | A Lemlist seat. Sends via one or more mailboxes. |

The inbox is **contact-scoped**, not lead-scoped: `GET /inbox/{contactId}` returns every message with that human regardless of which campaign it came from.

`POST /inbox/email` accepts **either** `contactId` **or** `leadId`. If you pass only `leadId`, Lemlist resolves the contact and returns `contactId` in the response.

---

## Endpoints

### Reading

#### `GET /inbox` — all team conversations
Returns Inbox Conversation objects for the whole team.

#### `GET /inbox/{contactId}` — full message history with one contact

```bash
curl -u ":$KEY" "https://api.lemlist.com/api/inbox/ctc_xxx?limit=10"
```

| Param | Notes |
|---|---|
| `userId` | ID of the user viewing (optional) |
| `limit` / `skip` | Pagination |
| `markAsRead` | **Default `false`.** Setting `true` is a write — it clears the unread badge in the Lemlist inbox UI. Leave it off unless asked. |

Response: `{ data: [InboxMessage], pagination: {...} }`

**The InboxMessage object is the most useful payload in the whole API** — one object hands you everything needed to reply:

```jsonc
{
  "_id": "act_xxx",   // ← pass as replyToActivityId
  "type": "emailsReplied",           // or emailsSent, linkedinSent, ...
  "messageId": "<CAKs+3EY...@mail.gmail.com>",
  "createdAt": "2024-12-03T10:10:45.000Z",
  "fromEmail": "alex@example.com",
  "teamId": "tea_...",
  "leadId": "lea_...",
  "campaignId": "cam_...",
  "sequenceId": "seq_...",
  "sequenceStep": 0,                 // 0-based; SHIFTS if steps are reordered
  "stepId": "stp_...",               // stable — prefer this when storing a reference
  "sendUserId": "usr_xxx",        // ┐
  "sendUserName": "Jordan DOE",                  // │ the sender triple —
  "sendUserEmail": "jordan.doe@example.com",     // │ reuse verbatim to reply
  "sendUserMailboxId": "usm_xxx",  // ┘ from the same mailbox
  "leadEmail": "alex@example.com",
  "contactId": "ctc_xxx",
  "subject": "Meet me !",
  "message": "<html>...</html>",     // HTML body
  "attachments": []
}
```

> **Don't guess the sender.** Read `sendUserId` / `sendUserEmail` / `sendUserMailboxId` off the thread and echo them back. If you reply from a different mailbox than the one that sent the sequence, the thread breaks and deliverability suffers.

---

### Sending 🚨

#### `POST /inbox/email` — send or reply

```bash
curl -u ":$KEY" -X POST "https://api.lemlist.com/api/inbox/email" \
  -H "Content-Type: application/json" \
  -d '{
    "sendUserId": "usr_xxx",
    "sendUserEmail": "john@example.com",
    "sendUserMailboxId": "usm_xxx",
    "contactId": "ctc_xxx",
    "message": "<p>Hello,</p><p>Following up...</p>",
    "replyToActivityId": "latest"
  }'
```

| Field | Required | Notes |
|---|---|---|
| `sendUserId` | ✅ | `usr_...` |
| `sendUserEmail` | ✅ | Must belong to that user |
| `sendUserMailboxId` | ✅ | `usm_...` |
| `message` | ✅ | **HTML.** Plain `\n` will not render — wrap in `<p>` / use `<br>`. |
| `contactId` *or* `leadId` | ✅ (one of) | Not both required |
| `subject` | Conditional | **Required for a standalone email. OMIT on a reply** — the thread's subject is reused. Passing one anyway breaks threading in some clients. |
| `cc` | ❌ | On a reply: omit to inherit the thread's CC, `[]` to strip it, or a list to override |
| `replyToActivityId` | ❌ | `act_...` for a specific message, or the literal string `"latest"` for the contact's most recent email. Sets `In-Reply-To` so it threads. **Omit entirely to send a brand new standalone email.** |

Response: `{ "ok": true, "contactId": "ctc_..." }`

**`"latest"` is the pragmatic choice** for automated replies — no need to track activity IDs. If the contact has no prior email, it degrades gracefully to a standalone send (so still pass a `subject` as a fallback if that's reachable in your flow).

400 errors are returned as **`text/plain`, not JSON**: `Bad team`, `Invalid sendUserId`, `Invalid sendUserEmail`, `Invalid sendUserMailboxId`, `contactId or leadId is required`, `Invalid leadId`, `Lead not found`, `Failed to send email`.

#### `POST /inbox/linkedin` — send a LinkedIn message
#### `POST /inbox/whatsapp` — send a WhatsApp message

Same shape/sender pattern. Requires the channel to be connected on that user (`GET /users/channels` reports availability).

---

### Drafts — the safe alternative to sending

Writes a draft into the Lemlist inbox UI for a human to review and send. **This is the default way to prepare a reply.** **`source` is automatically tagged `"api"`** so whoever works the inbox can see it came from automation.

| Method | Path |
|---|---|
| `POST` | `/inbox/{contactId}/drafts` |
| `GET` | `/inbox/{contactId}/drafts` (list) |
| `GET` | `/inbox/{contactId}/drafts/{draftId}` |
| `PATCH` | `/inbox/{contactId}/drafts/{draftId}` |
| `DELETE` | `/inbox/{contactId}/drafts/{draftId}` (soft delete — sets `deletedAt`) |

**`draftOwner` is a required query param** on create. Accepts either a `usr_...` ID or a login email (resolved via lookup). Team membership is verified either way.

Validations that will bite you:
- `content` must be non-empty, **max 30KB**
- `channel` ∈ `email` | `linkedin` | `whatsapp` | `sms`
- **Max 10 drafts per conversation**
- `content` and `subject` are sanitized server-side

---

### Labels

| Method | Path | Purpose |
|---|---|---|
| `POST` | `/inbox/labels` | Create a team label |
| `GET` | `/inbox/labels` | List labels |
| `GET` | `/inbox/labels/{id}` | Get one |
| `POST` | `/inbox/conversations/labels/{contactId}` | Attach label(s) to conversation(s) |
| `DELETE` | `/inbox/conversations/labels/{contactId}` | Remove label(s) |

Useful for marking a conversation `auto-replied` / `needs-human` from automation without sending anything.

---

## Webhooks — getting notified of replies

`POST /hooks` registers a callback. `GET /hooks` lists, `DELETE /hooks/{id}` removes.

```bash
curl -u ":$KEY" -X POST "https://api.lemlist.com/api/hooks" \
  -H "Content-Type: application/json" \
  -d '{"targetUrl":"https://your-endpoint.example.com/webhook/reply-<long-random-token>","type":"emailsReplied","isFirst":false}'
```

| Field | Notes |
|---|---|
| `campaignId` | Scope the hook to one campaign. Omit for team-wide (all campaigns). |
| `isFirst` | **Send it as a JSON body boolean** — the documented query param is silently stored as `null`. `true` = fire only on a lead's FIRST activity of that type, so a second reply from the same person is never delivered. For replies, use `false` and dedupe per message yourself (key on the activity `_id`). Read the hook back with `GET /hooks` to confirm what was stored. |
| `zapId` | Zapier only |

**One hook per `targetUrl`.** A second hook on the same URL (e.g. one for `emailsReplied`, one for `linkedinReplied`) returns `409` with an empty body. Use distinct paths or a query suffix (`?e=linkedinReplied`), and make sure your receiver matches on the path, not the full path-plus-query string.

`type` is optional — **omit it and you receive every event**, which is a firehose (`emailsSent`, `emailsOpened`, …) and includes the lead-state groups (`contacted`/`hooked`/`attracted`/`warmed`) that duplicate activity events. Set it unless you filter server-side.

### Event types that matter for replies

| Event | Fires when |
|---|---|
| `emailsReplied` | **Any** email reply — positive or negative. Sentiment is *not* judged. |
| `emailsInterested` | A human/AI marked the lead interested in the Lemlist UI |
| `emailsNotInterested` | Marked not interested |
| `interested` / `notInterested` | Lead-state groups (aggregate several activity types) |
| `linkedinReplied` / `linkedinInterested` / `linkedinNotInterested` | LinkedIn equivalents |
| `whatsappReplied`, `smsReplied` | Other channels |
| `emailsUnsubscribed`, `emailsBounced`, `emailsFailed` | Suppression / delivery |

> **To handle positive AND negative replies: subscribe to `emailsReplied` (and `linkedinReplied` for LinkedIn) alone** and classify sentiment yourself. `emailsInterested`/`emailsNotInterested` only fire when someone has *already* labelled the lead, so they'd miss raw replies and double-fire on ones that get labelled later.

Full event enum (69 values) is in the [Add Webhook](https://developer.lemlist.com/api-reference/endpoints/webhooks/add-webhook) docs — includes the whole `linkedin*`, `whatsapp*`, `sms*`, `aircall*`, `api*`, `manual*` families plus `paused`, `stopped`, `campaignComplete`, `enrichmentDone`, `callTranscriptDone`, `inboxLabelUpdated`, `signalRegistered`.

### The `emailsReplied` payload

Unlike Instantly's reply events, **the payload already contains everything needed to reply.** No lookup call required. (LinkedIn reply bodies arrive in `text`; email bodies in `message`/`html` when read back from `GET /inbox/{contactId}`.)

```jsonc
{
  "_id": "act_xxx",        // ← replyToActivityId
  "type": "emailsReplied",
  "emailId": "eml_xxx",
  "messageId": "<CADhdMOY2ov...@mail.gmail.com>",
  "createdAt": "2025-11-18T23:11:26.000Z",
  "fromEmail": "prospect@gmail.com",
  "isFirst": true,                        // first reply of this type from this lead?
  "stopped": true,                        // sequence auto-stopped on reply
  "bot": false,                           // ← Lemlist's own auto-reply/bounce detector
  "subject": "Re: quick question",
  "messagePreview": "Hey Sam, sounds interesting...",
  "teamId": "tea_...",
  "leadId": "lea_...",
  "campaignId": "cam_...",
  "campaignName": "Q3 outbound test",
  "sequenceId": "seq_...",
  "sequenceStep": 0,
  "emailTemplateId": "etp_...",
  "sendUserId": "usr_xxx",           // ┐
  "sendUserName": "Sam Doe",                        // │ sender triple,
  "sendUserEmail": "sam.doe@example.com",           // │ ready to echo back
  "sendUserMailboxId": "usm_xxx",     // ┘
  "leadEmail": "prospect@gmail.com",
  "email": "prospect@gmail.com",
  "contactId": "ctc_xxx",
  "html": "<div dir=\"ltr\">...full reply + quoted thread...</div>",
  "text": "Hey Sam...\n\nOn Mon, Nov 17 ... wrote:\n> ...",   // ← plain text, use this
  "metaData": { "taskId": "tsk_...", ... }
}
```

**Gotchas on the payload:**
- `text` includes the **quoted thread below the reply**. Strip everything from the first `On <date> ... wrote:` / leading `>` block before feeding it to an LLM, or the model will answer the wrong message.
- `bot: true` means Lemlist flagged it as an auto-responder. **Always skip these** — replying to a bounce daemon is how you burn a domain.
- Direct Lemlist webhooks POST a **single JSON object**. Routed through Zapier or another relay it often arrives **wrapped in an array**. Handle both.
- There is **no signature header** to verify. Use an unguessable webhook path and/or a shared-secret query param.

---

## Minimal reply flow

```
emailsReplied webhook  (isFirst=false, dedupe on activity _id)
  → skip if bot == true
  → strip quoted thread from `text`
  → classify + draft  (your LLM)
  → POST /inbox/{contactId}/drafts   ← default: a human reviews + sends it in the Lemlist inbox
  → only if the user explicitly says go for this message:
    POST /inbox/email {
       sendUserId, sendUserEmail, sendUserMailboxId  ← copied from the webhook
       contactId                                     ← copied from the webhook
       replyToActivityId: "latest"   (or the webhook's `_id`)
       message: "<p>...</p>"
       // no subject — inherits the thread
    }
```

Zero extra API calls between trigger and draft.

---

## Client

`lemlist_inbox.py` in this folder — dependency-free (stdlib `urllib` only), mirrors every endpoint above.

```python
from lemlist_inbox import LemlistInbox

lem = LemlistInbox()                               # LEMLIST_API_KEY via gtm.cred

msgs = lem.get_contact_messages("ctc_...")         # read
lem.create_draft("ctc_...", draft_owner="john@acme.com",
                 content="<p>hi</p>", channel="email")   # safe write

lem.send_email(                                    # 🚨 real send, only on the user's go
    send_user_id="usr_...", send_user_email="john@acme.com",
    send_user_mailbox_id="usm_...", contact_id="ctc_...",
    message="<p>Sounds good, how's Thursday?</p>",
    reply_to_activity_id="latest",
)
```

`send_email()` (and `send_linkedin` / `send_whatsapp`) refuse to run unless `allow_send=True` is passed to the constructor **or** `LEMLIST_ALLOW_SEND=1` is set — a deliberate guardrail so an accidental import can't message a prospect. Set it only for a send the user explicitly approved.

Helpers included: `strip_quoted_reply(text)`, `text_to_html(text)`, `parse_webhook(payload)` (handles the array-wrapping and normalizes field names).

---

## Gotchas summary

1. **Basic auth, empty username** — not Bearer.
2. **Contact (`ctc_`) ≠ Lead (`lea_`).** Inbox is contact-keyed.
3. **`message` is HTML.** Newlines don't survive.
4. **Omit `subject` on replies.** Include it only on standalone sends.
5. **`replyToActivityId: "latest"`** saves you an entire lookup call.
6. **Echo the sender triple from the thread** — never pick a mailbox yourself.
7. **`isFirst` is a body boolean**, and `true` drops every later reply from the same lead. Use `false` + per-message dedupe.
8. **Skip `bot: true`** payloads.
9. **Strip the quoted thread** out of `text` before prompting an LLM.
10. **400s come back as plain text**, so `resp.json()` will throw — read `resp.text`.
11. **Max 10 drafts per conversation**, `content` max 30KB.
12. **Rate limit 20/2s** shared with all other Lemlist calls.
13. **No webhook signature** — protect the endpoint with an unguessable path.
14. **One hook per `targetUrl`** — a second registration 409s with an empty body.
15. **Drafts by default** — sending is the exception and needs the user's explicit go.

---

## Related

- `lemlist` skill — campaigns, stats, leads, activities (read)
- `lemlist-campaign-builder` skill — building sequences via API
- `lemlist-reporting` skill — campaign exports and metrics
