---
name: clay-cli
description: Build and run Clay workflows, tables, searches and enrichments from the terminal with the Clay CLI (clay@clay-plugins). Use when someone asks to build a Clay workflow or table, wire an HTTP/API column, add enrichment steps in Clay, test or debug a Clay node, or check which Clay workspace they are in.
---

# Clay CLI

## In the GTM OS

- **Clay is optional.** Use this only if you have a Clay workspace.
- **Install the plugin** (see Install below). It also brings ~34 of Clay's own skills (`workflows`,
  `tables`, `searches`, `signals`, `campaigns`, `public-api`, ...), which Claude loads on its own.
- **Log in once, as yourself:** type `! clay login` in Claude Code (browser OAuth). Check with
  `clay whoami`. Switch workspace with `clay workspaces switch <id>` (`clay workspaces list` shows ids).
- **Right after the first install** `clay` is not on PATH until Claude Code restarts. Use the
  launcher path shown under "The PATH gotcha" below, or restart Claude Code.
- **Credits are real money.** Test ONE node (`clay workflows nodes test`) before a full run, and
  state the row count and credit cost before `runs` on a live table.
- **Emails:** default to AI Ark (`skills/ai-ark`). Use Clay's email waterfall only when you
  deliberately want a second source for the rows AI Ark missed.
- **Shared or partner Clay workspaces** belong to their owner. Read and build only what the task
  needs, and never delete a table, column or workflow you didn't create.

---

Building Clay **workflows** from the terminal with the `clay` CLI, which ships in the
`clay@clay-plugins` Claude Code plugin. Written from building a 6-node enrichment workflow
(domain -> LinkedIn ads -> Meta ads -> headcount -> HTTP scoring call) end to end on 2026-09-20;
every trap below cost a failed run to find.

- **Install:** `claude plugin marketplace add clay-run/agent-plugins` then
  `claude plugin install clay@clay-plugins`. Non-interactive, no need to type the `/plugin` slash
  commands. Requires Claude Code v2.1.91+.
- **Repo:** `github.com/clay-run/agent-plugins` · **Docs:** `developers.clay.com`
- ~34 bundled skills (`workflows`, `routines`, `tables`, `searches`, `signals`, `campaigns`,
  `audiences`, `public-api`, `cli`), plus recipe skills like `workflows-audience-enrichment` and
  `workflows-vs-tables`.

## The PATH gotcha on a fresh install

Claude Code only adds a newly installed plugin's `bin/` to PATH **starting with the next session**.
Do not install a forwarder for this. Resolve the bundled launcher and call it directly:

```bash
shim="$(sh -c 'ls -1dt "${CLAUDE_CONFIG_DIR:-$HOME/.claude}"/plugins/cache/*/clay/*/bin/clay 2>/dev/null | head -n1')"
"$shim" whoami
```

Re-run that `ls -1dt` **fresh before every command** — each Bash call is a new shell, so a variable
set in one call is gone in the next. Bare `clay` works after a restart.

`clay login` is browser OAuth and stores a session per workspace on disk. `clay whoami` exiting 0 is
the whole proof. `clay workspaces switch <id>` moves between them.

## Mental model

```
workflow -> trigger + nodes + edges
node types: trigger | tool | agent | conditional | code
```

- `clay workflows create --name X` makes an **empty** workflow. No trigger, no nodes.
- `clay workflows nodes create <wf> --input spec.json` adds a node.
- Edges live **on the node**, as `incomingEdges`, set via `nodes update`.
- `clay workflows graph validate <wf>` is the gate. Run it after every structural change.
- `clay workflows diagram <wf>` renders Mermaid, which is the fastest way to eyeball the shape.
- `clay workflows runs test <wf> --inputs '{"domain":"x.com"}'` runs the **draft**; `--live` runs the
  published version.
- `clay workflows nodes test <wf> <node> --inputs {...}` tests ONE node. Use this instead of
  re-running the whole chain while debugging; it only bills that node.

## Node spec shape

```json
{
  "name": "LinkedIn Ads",
  "description": "...",
  "nodeType": "tool",
  "tools": [{
    "toolType": "clay_action",
    "actionKey": "adyntel-get-linkedin-ads",
    "actionPackageId": "550e8400-e29b-41d4-a716-446655440000",
    "inputMappingConfig": {
      "company_domain": { "type": "reference", "expression": "{{domain}}" },
      "role_filter":    { "type": "static",    "value": "sales" }
    }
  }]
}
```

Mapping `type` is one of `static` | `reference` | `coalesce` | `item` | `skip` | `map`.
**There is no `literal`** — that spelling fails validation naming the six valid ones.

## The traps

### 1. Every node nests its output under `result`

`stepOutputs` is `{ result, success, textPreview }`. A flat `{{total_ads}}` resolves to nothing, and
`{{result.total_ads}}` is ambiguous the moment two upstream nodes both emit `result`. Always go
through `inputSchema` (trap 2), never a bare `{{field}}` for upstream data.

### 2. A tool node must DECLARE what it references, and failing to is SILENT

`inputMappingConfig` can only use variables the node already has. Declare each one on the node's
`inputSchema`, inline, with `sourceNodeId` + a JSONPath `sourcePath`:

```json
"inputSchema": { "type": "object", "properties": {
  "linkedin_ads_count": { "type": "number",
                          "sourceNodeId": "wfn_abc",
                          "sourcePath": "$.result.total_ads" }
}}
```

Use `sourcePath`, not `path`. **This is the dangerous one**: without the declaration the run still
reports success. 6/6 nodes completed, green status, and a body of `{"domain":"x.com","sdr_headcount":""}`.
`graph validate` returns `valid: true`. Nothing surfaces it except reading the downstream
`stepInputs`, or the receiving service reporting that it got nothing. **After wiring any reference,
read back the run's `stepInputs` and confirm real values.**

### 2b. An AGENT node's output is `$.structuredOutputs`, not `$.result`

Trap 1 says every node nests under `result`. **Agent nodes do not.** A `nodeType: agent` node
returns its declared `outputSchema` fields under `structuredOutputs`, alongside `reasoning` and
`stepsTaken`:

```json
"inputSchema": { "type": "object", "properties": {
  "competitor1_domain": { "type": "string",
                          "sourceNodeId": "wfn_agent",
                          "sourcePath": "$.structuredOutputs.competitor1_domain" }
}}
```

Wiring an agent field as `$.result.<field>` fails the same silent way as trap 2, but worse: the
downstream node does not receive empty, it receives the agent's **raw reasoning log**. Measured on
a real agent-into-tool chain 2026-09-20: `graph validate` returned `valid: true`,
the agent node itself completed green with perfect output, and the next node was handed
`{"stepsTaken": ["Searched Google with query ..."]}` as its company domain and failed.

Tool nodes stay on `$.result.*`. In one chain you will use both spellings, so check the producing
node's type before writing any `sourcePath`.

### 3. `headers` on `http-api-v2` is silently DROPPED

`headers` is declared `type: object`, and object params do not survive `inputMappingConfig`:

| attempt | result |
|---|---|
| raw object as `static.value` | `[...headers.value] Invalid input` |
| JSON **string** as `static.value` | validates, then sent as a literal string |
| `reference` with a JSON expression | dropped entirely |

The failed step's `stepInputs` had `url`, `body`, `method` and **no `headers` key**, so the call went
out unauthenticated. Fixes, in order of preference:

1. **An HTTP API auth account** in Clay, referenced by the node's `authAccountId`. Clay's own schema
   tip says to do this for `X-API-KEY` / `Authorization`. No CLI command found for creating one; may
   be UI-only.
2. **Put the key in the URL query string** if the service accepts it (`?key=...`). This is what worked.
3. The docs say object-valued params want the **`map`** type, one entry per key. Untested here.

### 4. `responseTimeout` is capped at 100,000 ms

`Response timeout must be less than 100000ms`. Anything slower than ~100 s cannot use a synchronous
HTTP node, so it needs the async + webhook pattern (202 now, result POSTed to a Clay
"Pull in data from a webhook" source, with `passthrough` echoed to rejoin the row).

### 5. Edges use `sourceNode`, the validator reports `sourceNodeId`

Setting an edge:

```bash
clay workflows nodes update <wf> <childNode> --input '{"incomingEdges":[{"sourceNode":"<parentNode>"}]}'
```

`sourceNodeId` is rejected here (`Unrecognized key`) even though `graph get` and the validator both
*report* edges as `{sourceNodeId, targetNodeId}`. Inside `inputSchema` it is `sourceNodeId`. The two
spellings are not interchangeable.

**References only resolve from strictly upstream nodes**, so a fan-out of independent enrichments
that all feed one final node must be wired as a sequential chain, not parallel branches.

## Actions catalog

```bash
clay workflows actions list > actions.json          # 690 actions, greppable
clay workflows actions schema <packageId> <actionKey> [--include-options]
clay workflows actions dynamic-fields <pkg> <key> <paramPath>
clay workflows actions test <pkg> <key>             # COSTS CREDITS
```

The catalog is heterogeneous: integration actions carry `packageId` + `actionKey`, workspace
functions carry `type: "function"` + `functionId`. A `.get('packageId')` over the whole list returns
`None` for half the rows.

⚠️ **The catalog's declared output schema is not always the live field name.** PDL's
`get-employee-count-by-criteria` advertises `employeeCountByCriteria` and actually returns
**`roleCount`**. Run the node once and read the real `stepOutputs` before wiring anything to it.

Useful ones found so far:

| Need | Action | Package | Credits |
|---|---|---|---|
| LinkedIn ads + creatives | `adyntel-get-linkedin-ads` | `550e8400-...440000` | 1 |
| Meta ads + creatives | `adyntel-get-meta-ads` | `550e8400-...440000` | 1 |
| Headcount by criteria | `get-employee-count-by-criteria` | `78593846-...` (PDL) | 5 |
| Any HTTP call | `http-api-v2` | `4299091f-...` | - |

Adyntel is `requiresApiKey: false` and bills as **Clay credits**, so no vendor key to manage.
`clay credits balance` for the workspace total.

## Debugging recipe

```bash
clay workflows runs list <wf>
clay workflows runs get <wf> <runId>      # status, duration, credits, progress
clay workflows runs steps <wf> <runId>    # per-step stepInputs, stepOutputs, errors
```

`runs steps` is the one that matters. **`stepInputs` tells you what a node actually received**,
which is how you catch empty references that a green run hides. `statusDetail:
tool_execution_pending` on an async tool means it is still waiting on the vendor.

## Read-only note

Reads (`list`, `get`, `graph`, `actions list/schema`, `credits balance`) are free and safe.
`create`, `update`, `publish`, `runs test` and `actions test` all WRITE or SPEND. A workflow whose
nodes write into your CRM or sequencer (HubSpot, Attio, Instantly, Lemlist, SmartLead, Airtable) is a
live write to that system: get sign-off from whoever owns it before publishing or running it.
