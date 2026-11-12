---
name: fireflies-mcp
description: Fireflies MCP setup and usage for pulling meeting transcripts. Use when you need call context from Fireflies directly.
---

# Fireflies.ai MCP for Claude Code — SKILL.md

> Setup guide for connecting Fireflies.ai meeting transcripts to Claude Code. Any Claude Code instance can follow this to get full access to meeting data.

---

## What It Does

Connects Fireflies.ai to Claude Code so you can:
- List and search all meeting transcripts
- Pull full transcripts with speaker attribution and timestamps
- Get AI-generated summaries, action items, and key points
- Search across meetings by keyword, participant, or date

---

## Prerequisites

- **Fireflies.ai account** with API access (Business plan or higher)
- **API key** from Fireflies Settings > Developer Settings
- **Node.js** installed (for `npx mcp-remote`)
- **Claude Code** CLI installed

---

## Setup — Method 1: claude mcp add (Recommended)

Run this in your terminal (**not** inside a Claude Code session):

```bash
claude mcp add fireflies -s user -- npx mcp-remote "https://api.fireflies.ai/mcp" --header "Authorization: Bearer YOUR_API_KEY_HERE"
```

Replace `YOUR_API_KEY_HERE` with your actual Fireflies API key.

**Scope options:**
- `-s user` — available in all projects (recommended)
- `-s project` — only available in the current project directory

Then restart Claude Code. The Fireflies tools will appear automatically.

---

## Setup — Method 2: Edit .claude.json Directly

If you're inside a Claude Code session and can't run `claude mcp add`, edit the config file directly.

### User-level (all projects)

Edit `~/.claude.json` and add `fireflies` to the project's `mcpServers`:

```json
{
  "projects": {
    "/Users/YOUR_USERNAME": {
      "mcpServers": {
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
    }
  }
}
```

You can also do this atomically with Python (useful when .claude.json is being actively written to by a running session):

```python
python3 -c "
import json
with open('$HOME/.claude.json', 'r') as f:
    data = json.load(f)

project_path = '/Users/YOUR_USERNAME'  # your home directory
data['projects'][project_path]['mcpServers']['fireflies'] = {
    'command': 'npx',
    'args': [
        'mcp-remote',
        'https://api.fireflies.ai/mcp',
        '--header',
        'Authorization: Bearer YOUR_API_KEY_HERE'
    ]
}

with open('$HOME/.claude.json', 'w') as f:
    json.dump(data, f, indent=2)
print('Fireflies MCP added')
"
```

Then restart Claude Code.

---

## Setup — Method 3: Direct GraphQL API (No MCP Restart Needed)

If you need transcripts immediately without restarting, hit the Fireflies GraphQL API directly with curl:

### List Recent Transcripts

```bash
curl -s -X POST "https://api.fireflies.ai/graphql" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_API_KEY_HERE" \
  -d '{"query": "{ transcripts(limit: 10) { id title date organizer_email duration participants } }"}'
```

### Get Full Transcript by ID

```bash
curl -s -X POST "https://api.fireflies.ai/graphql" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_API_KEY_HERE" \
  -d '{"query": "{ transcript(id: \"TRANSCRIPT_ID\") { id title date duration participants summary { action_items overview shorthand_bullet } sentences { text speaker_name start_time end_time } } }"}'
```

### Search Transcripts

```bash
curl -s -X POST "https://api.fireflies.ai/graphql" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_API_KEY_HERE" \
  -d '{"query": "{ transcripts(limit: 20) { id title date duration participants } }"}'
```

Then filter by title/date/participants in code.

### Convert Timestamps to Readable Dates

Fireflies returns `date` as Unix milliseconds. Convert with:

```python
from datetime import datetime, timezone
dt = datetime.fromtimestamp(date_ms / 1000, tz=timezone.utc)
print(dt.strftime("%Y-%m-%d %H:%M UTC"))
```

---

## Available MCP Tools (Once Connected)

| Tool | Description |
|------|-------------|
| `fireflies_get_transcripts` | List transcripts with filters (limit, date range) |
| `fireflies_get_transcript` | Get full transcript by ID (sentences, speakers, timestamps) |
| `fireflies_get_summary` | Get AI summary (overview, action items, key points) |
| `fireflies_search` | Search across all transcripts by keyword |
| `fireflies_get_user_contacts` | Get user profile and contact info |

---

## GraphQL API Reference

**Endpoint:** `https://api.fireflies.ai/graphql`
**Auth:** `Authorization: Bearer <API_KEY>` header
**Method:** POST with JSON body `{"query": "..."}`

### Key Query Fields

**Transcript object:**
- `id` — unique transcript ID
- `title` — meeting title
- `date` — Unix timestamp in milliseconds
- `duration` — meeting length in minutes (float)
- `organizer_email` — who scheduled the meeting
- `participants` — array of email addresses

**Summary object (nested under transcript):**
- `overview` — bullet-point summary of the meeting
- `action_items` — assigned tasks by person with timestamps
- `shorthand_bullet` — emoji-tagged key points with timestamps

**Sentences array (nested under transcript):**
- `text` — what was said
- `speaker_name` — who said it
- `start_time` — seconds from start (float)
- `end_time` — seconds from start (float)

---

## Notes for this GTM OS

- **Optional.** Only relevant if your team records calls in Fireflies. Everything else in the OS
  works without call transcripts.
- **Check the repo first:** `python3 gtm.py meetings [--limit N]` and
  `python3 gtm.py transcript --date YYYY-MM-DD` read the calls already stored in your own database.
  Reach for the MCP or the GraphQL API only for calls that are missing there.
- **API key:** keep it in the MCP config, or store it with `python3 gtm.py set-key FIREFLIES_API_KEY`
  (value on stdin) and read it in scripts with `gtm.cred("FIREFLIES_API_KEY")`. Never paste it into a
  file in the repo.
- **Finding the right call:** filter by the prospect's or customer's email domain in `participants`,
  then by date. Titles are free text and often inconsistent.
- **Recordings can be confidential.** Pull only the calls the task needs, quote sparingly, and never
  copy one customer's words into material another prospect will see.
- **Transcript format tip:** use `[MM:SS] Speaker: Text` when printing transcripts for readability.

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| MCP tools not appearing | Restart Claude Code after config change |
| `mcp-remote` not found | Run `npm install -g mcp-remote` or ensure npx works |
| 401 Unauthorized | Check API key is correct and has API access enabled |
| Empty transcripts | Verify meetings are being recorded in Fireflies settings |
| `.claude.json` write conflict | Use the Python atomic write method (Method 2) |
| Need data NOW without restart | Use Method 3 (direct GraphQL via curl) |

---

## Security

- API key grants read access to all meeting transcripts and user data in the Fireflies workspace
- Store the key in the MCP config (not in env vars or plain text files)
- The MCP connection uses HTTPS with Bearer token authentication
- Fireflies Zero-Day Retention policy does not apply to external platform processing
