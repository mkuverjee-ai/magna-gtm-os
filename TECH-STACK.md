# Tech stack

What the OS needs, what is worth having, and the alternatives. Prices change; check each vendor
before you buy.

## Must have

| Tool | What it does here | Notes |
|---|---|---|
| **Claude Code** | Runs everything | A Claude subscription (Pro, Max or Team) |
| **GitHub** | Holds the repo; how work is shared between teammates | Private repo, free tier is enough |
| **Instantly** | Email campaigns, inboxes, warm-up, analytics | You own the workspace. Keep only the mailboxes you use; rename warmed mailboxes rather than buying new ones when someone leaves |
| **Lemlist** | Email + LinkedIn sequences in one campaign, LinkedIn inbox | Needed for LinkedIn steps |
| **AI Ark** | Companies, people and emails: the list-building source | Refreshes its data roughly every 30 days; has an API, MCP and CLI. Count queries are free, pulls are billed |

## Strongly recommended

| Tool | Why | Alternative |
|---|---|---|
| **Supabase** (free tier) | Team database: keys set once for everyone, logs you can query | Without it the OS still works (per-laptop keys, logs as files). A Google Sheet can hold the what-worked log but not keys |
| **An always-on call recorder** (Fireflies or Granola) | Calls are how you learn why a buyer came in, which feeds `pqs-builder` and copy | Ask "what made you reach out?" on every first call and write it down |
| **A CRM** (Salesforce, HubSpot) | Where meetings and opportunities land; checked before anyone is added to a campaign | `CRM_PROVIDER`, `CRM_API_KEY` (+ `CRM_INSTANCE_URL` for Salesforce) |

## Optional, add when a play needs it

| Tool | Use | Key |
|---|---|---|
| **Apify** | Google Maps scraping, LinkedIn post engagers (for daily engagement plays), Meta ad counts | `APIFY_TOKEN`. Pay-per-use; every run is capped with `--max-usd` |
| **Exa** | Web research and signal search (news, hiring, expansion) | `EXA_API_KEY` |
| **Ocean.io** | Lookalike companies from a customer you already have | `OCEAN_API_KEY` |
| **Clay** | Tables and workflows from the CLI | The CLI may move to enterprise plans; AI Ark covers list building without it |
| **Freckle** / **Floqer** | Enrich, score and route a known list | Their own keys |
| **Railway** | Host a daily job (signal sweep, engagement pull), a webhook or a dashboard | `RAILWAY_WORKSPACE_TOKEN` |
| **Miro** | Boards and flowcharts from Claude | Sign in via `/mcp` |
| **Anthropic API** | Only for scripts that call Claude headless (e.g. bulk ICP generation) | `ANTHROPIC_API_KEY` |

## Data you don't need a separate tool for

- **Emails:** come from AI Ark. No separate email-finder or waterfall is needed.
- **Tech stack and hiring signals:** AI Ark firmographics plus Exa / job-posting search.
- **Event lists:** exhibitor and speaker pages, extracted with Claude and qualified against the ICP.
