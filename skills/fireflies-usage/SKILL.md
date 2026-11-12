---
name: fireflies-usage
description: Search meeting transcripts, extract action items, and pull call context from Fireflies.
---

# Fireflies Meeting Transcripts

How to use Fireflies.ai to search, retrieve, and extract insights from your team's recorded calls
(prospect, customer and internal). Optional: only relevant if your team records calls in Fireflies.

Check the repo first: `python3 gtm.py meetings [--limit N]` and `python3 gtm.py transcript --date YYYY-MM-DD`
read the calls already stored in your own database. Use Fireflies directly for anything missing there.

---

## When to Use

- Preparing for an upcoming prospect or customer call (review what was discussed last time)
- Finding what was said about a specific topic across meetings
- Extracting action items and commitments from past calls
- Building context on an account or a play you're picking up
- Mining buyer language and buying moments for `/pqs-builder` and `/pvp-builder`

---

## MCP Setup

Add Fireflies to your Claude Code instance so you can query meetings directly.

### Option 1: CLI Command (Recommended)

Run this in your terminal (not inside Claude Code):

```bash
claude mcp add fireflies -s user -- npx mcp-remote "https://api.fireflies.ai/mcp" --header "Authorization: Bearer YOUR_API_KEY_HERE"
```

Replace `YOUR_API_KEY_HERE` with your Fireflies API key (get it from Fireflies Settings > Developer Settings).

Scope options:
- `-s user` — available in all projects (recommended)
- `-s project` — only in the current project directory

Restart Claude Code after adding.

### Option 2: Edit .claude.json

Add to your `~/.claude.json` under `mcpServers`:

```json
{
  "fireflies": {
    "command": "npx",
    "args": [
      "mcp-remote",
      "https://api.fireflies.ai/mcp",
      "--header",
      "Authorization: Bearer YOUR_API_KEY_HERE"
    ]
  }
}
```

Restart Claude Code after saving.

### Prerequisites

- Fireflies.ai account with API access (Business plan or higher)
- Node.js installed (for `npx mcp-remote`)
- API key from Fireflies Settings > Developer Settings

---

## Available MCP Tools

| Tool | What It Does |
|------|-------------|
| `fireflies_get_transcripts` | List transcripts with filters (limit, date range) |
| `fireflies_get_transcript` | Get full transcript by ID (sentences, speakers, timestamps) |
| `fireflies_get_summary` | Get AI summary, action items, and key points for a meeting |
| `fireflies_search` | Search across all transcripts by keyword |
| `fireflies_get_user_contacts` | Get user profile and contact info |

---

## How to Search for Meetings

### By Company Name (Title Search)

Most meetings are titled like "CompanyA <> CompanyB" or "Company | Topic". Search by the company name in the title:

```
fireflies_search(query: "acme")
```

Or use `fireflies_get_transcripts` and filter by title locally.

### By Participant Email

If you know who was on the call, search by their email domain:

```
fireflies_get_transcripts(limit: 50)
```

Then filter the `participants` array for emails matching `@prospectdomain.com`.

### By Date Range

Pull recent transcripts and filter by date:

```
fireflies_get_transcripts(limit: 20)
```

Dates come back as Unix timestamps in milliseconds. Convert: `datetime.fromtimestamp(date_ms / 1000)`.

### By Keyword

Search for specific topics discussed across all meetings:

```
fireflies_search(query: "campaign performance")
```

Note: keyword search only hits transcript text and titles, NOT participant emails. To find meetings by participant, fetch broadly and filter locally.

---

## Getting Full Transcripts and Summaries

Once you find the meeting ID:

```
# Get the AI-generated summary (faster, usually enough)
fireflies_get_summary(transcriptId: "MEETING_ID")

# Get the full word-by-word transcript
fireflies_get_transcript(transcriptId: "MEETING_ID")
```

The summary includes:
- **Overview** — bullet-point summary of the meeting
- **Action items** — tasks assigned by person with timestamps
- **Shorthand bullet** — emoji-tagged key points with timestamps

The full transcript includes:
- **Sentences** — each utterance with speaker name, text, start/end timestamps

---

## Extracting Action Items

Use `fireflies_get_summary` to get the action items section. This returns tasks grouped by speaker with timestamps.

Focus on:
1. Items assigned to your own team (not the prospect or customer)
2. Items with specific deadlines mentioned
3. Deliverables that were promised ("we'll send the list by Friday")

---

## Direct GraphQL API (No MCP)

If MCP is not set up or you need data without restarting, use curl:

### List Recent Transcripts

```bash
curl -s -X POST "https://api.fireflies.ai/graphql" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -d '{"query": "{ transcripts(limit: 10) { id title date organizer_email duration participants } }"}'
```

### Get Full Transcript

```bash
curl -s -X POST "https://api.fireflies.ai/graphql" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -d '{"query": "{ transcript(id: \"TRANSCRIPT_ID\") { id title date duration participants summary { action_items overview shorthand_bullet } sentences { text speaker_name start_time end_time } } }"}'
```

---

## Use Cases

### Pre-Call Prep
Before a follow-up call, pull the summary from the last meeting. Review action items to see what was committed and whether it was delivered.

### Finding What Was Discussed
Search for a keyword ("scoring model", "campaign copy", "ICP") across transcripts to find when and where it was discussed.

### Extracting Prospect Commitments
Pull action items from the last 3-4 meetings with an account to build a running list of what they agreed to (intros, data, a trial, a decision date).

### Account Handoff
When picking up an account from a teammate, pull the last 5 meeting summaries to understand the relationship, open threads, and next steps.

### Confidentiality
Recordings can be confidential. Pull only the calls the task needs, and never copy one customer's words into material another prospect will see.

---

## Gotchas

| Issue | What Happens | Fix |
|-------|-------------|-----|
| Comma-joined participants | `participants` field can be `"user1@a.com,user2@b.com"` (one string, not an array) | Split on comma before filtering |
| Keyword search scope | `fireflies_search` only hits transcript text and titles, not participant emails | Fetch 50-100 recent transcripts and filter by participant locally |
| Transcript not ready | Fireflies needs ~60 seconds after a meeting ends to finalize the transcript | Wait before fetching; if empty, try again in a minute |
| Unix timestamps | `date` field is Unix milliseconds, not seconds | Divide by 1000 before converting to datetime |
| MCP tools not appearing | Config was added but Claude Code was not restarted | Restart Claude Code |
| 401 errors | API key is wrong or lacks API access | Verify key in Fireflies Settings > Developer Settings |
| Cloudflare blocking | Python `urllib` gets blocked by Fireflies' Cloudflare | Use `subprocess` with `curl` instead of urllib directly |

---

## Formatting Transcripts

When printing transcript excerpts for readability, use this format:

```
[MM:SS] Speaker Name: What they said
[01:23] Rep: Let's review what changed since our last call.
[01:45] Prospect: We hired two more SDRs, and they still have no account list.
```

Calculate MM:SS from the `start_time` field (which is in seconds from meeting start).
