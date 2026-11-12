# Workflow CLI Reference

If the current request authors or changes a Workflow and you have not entered the six-step path in [../BUILD.md](../BUILD.md) or the refine path in [../REFINE.md](../REFINE.md), go back — these commands do not replace those paths; they tell you when to use them.

Org-scoped Workflow commands accept `--org-id <org-id>` and `--token <frk_token>`. An explicit `--org-id` has highest precedence over `FRECKLE_ORG_ID` and shared global config. `workflow node list` and `workflow node inspect` use only the CLI Token because the catalog is global; `workflow node preview` remains org-scoped.

## Node Catalog

List and inspect node definitions:

```bash
freckle workflow node list
freckle workflow node inspect <definition-key>
freckle workflow node inspect <definition-key> --contract
```

Node command output is YAML. The following shapes are abbreviated; nested schemas, types, metadata, and repeated entries are omitted.

`workflow node list` returns:

```yaml
nodes:
  - definitionKey: <definition-key>
    definitionVersion: <definition-version>
    label: <label>
    description: <optional-description>
    category: <category>
    purpose: <optional-purpose>
    creditCost: <credits>
    creditCostModel: <static-or-dynamic>
```

`description` and `purpose` are omitted when unavailable.
`creditCost` and `creditCostModel` are always present, including when the price is zero. `creditCost` is the customer-facing unit price. A `static` price is charged at most once per execution and only when the node produces a billable result; an enrichment node that finds no result costs 0 credits. A `dynamic` price is charged once per billable result.

Use the full `workflow node inspect <definition-key>` before authoring. It returns:

```yaml
definitionKey: <definition-key>
definitionVersion: <definition-version>
configSchema: <schema-representation>
contract:
  kind: static
  inputPorts: <input-port-details>
  outputs: <output-port-details>
  caseIds: <branch-case-ids>
editor: <editor-metadata>
authoring: <optional-authoring-guidance>
creditCost: <credits>
creditCostModel: <static-or-dynamic>
```

`authoring` is omitted when unavailable. A dynamic definition's full inspect has `contract: { kind: dynamic }`. Pricing fields use the same semantics as the list response.

`workflow node inspect <definition-key> --contract` prints only the contract. Static contracts have lowered ports and branch cases:

```yaml
kind: static
inputPorts:
  - portId: <port-id>
    label: <label>
    type: <workflow-type>
    isOptional: false
outputs:
  - outputId: <output-id>
    label: <label>
    type: <workflow-type>
    isOptional: false
caseIds: <branch-case-ids>
```

A dynamic contract cannot be resolved without node config and may contain only:

```yaml
kind: dynamic
```

Preview dynamic nodes after their config is present in the draft:

```bash
freckle workflow node preview <node-id> --file workflow.yaml
freckle workflow node preview <node-id> --json '<draft-json>'
```

`workflow node preview` returns the resolved contract for the requested node. Unlike inspect output, the resolved `contract` has no `kind` field:

```yaml
nodeId: <node-id>
definitionKey: <definition-key>
definitionVersion: <definition-version>
contract:
  inputPorts: <input-port-details>
  outputs: <output-port-details>
  caseIds: <branch-case-ids>
```

When a node config needs a provider `credentialId`, inspect connected credentials first — see [../CONNECTIONS.md](../CONNECTIONS.md).

## Saved Workflows

List and inspect saved Workflows:

```bash
freckle workflow saved list
freckle workflow saved list --org-id <org-id>
freckle workflow saved list --all
freckle workflow saved inspect <workflowId>
freckle workflow saved inspect <workflowId> --org-id <org-id>
freckle workflow saved revisions list <workflowId>
freckle workflow saved revisions inspect <workflowId> <revisionId>
```

Each list row includes the Workflow's input/output `shape` when it has a published revision, and `saved inspect` embeds the full input/output `schema` — use these for reuse checks and input mappings instead of exporting drafts.

`workflow saved list` adds `costEstimate` to every Workflow row, and `workflow saved inspect <workflowId>` adds it to the top-level response:

```yaml
costEstimate:
  estimatedStaticCreditCost: <credits>
  dynamicNodeCosts:
    - nodeId: <node-id>
      definitionKey: <definition-key>
      definitionVersion: <version>
      creditCost: <per-result-credits>
      creditCostModel: dynamic
  description: <plain-language-estimate>
# or null when the Workflow has no saved latest revision
```

`costEstimate` is the same structured estimate returned when creating or saving a Workflow revision: static node prices are summed into `estimatedStaticCreditCost`, and dynamic node unit prices are listed separately in `dynamicNodeCosts` because billable result counts are unknown until runtime. A Workflow without a saved latest revision returns `costEstimate: null`. This is a conservative maximum for static charges plus per-result dynamic unit prices — not a guaranteed bill (a run can cost 0 credits when no node produces a billable result).

Use the default saved Workflow list for reuse discovery — it is scoped to the Active Organization, which is the only organization reuse looks at; archived Workflows are not reuse candidates unless the user explicitly asks about archived Workflows. Use `--all` only when the user explicitly asks to list saved Workflows across every organization available to the CLI token, or when step 1 is locating a named Workflow to derive the destination organization; it returns groups keyed by organization and is not part of normal reuse discovery.

Export an editable draft from a saved Workflow:

```bash
freckle workflow saved get-draft <workflowId> --out workflow.yaml
freckle workflow saved get-draft <workflowId> --revision-id <revisionId> --out workflow.yaml
```

Create a new saved Workflow and first revision:

```bash
freckle workflow saved create --file workflow.yaml --label "<label>" --description "<description>"
```

Keep the returned `workflow.id`; saved Workflow IDs are UUIDv7.

Publish a new revision of an existing saved Workflow:

```bash
freckle workflow saved lifecycle publish <workflowId> --file workflow.yaml
```

Update saved Workflow metadata or lifecycle state:

```bash
freckle workflow saved lifecycle update <workflowId> --label "<label>" --description "<description>"
freckle workflow saved archive <workflowId>
freckle workflow saved unarchive <workflowId>
```

## Run Saved Workflows

Invoke a saved Workflow with a JSON object input:

```bash
freckle workflow saved invoke <workflowId> --json '{"email":"person@example.com"}'
freckle workflow saved invoke <workflowId> --json '{"email":"person@example.com"}' --external-invocation-id <id>
freckle workflow saved invoke <workflowId> --file inputs.json
```

Capture the returned `runId`. Runs are async, so watch until terminal or inspect a single run on demand:

```bash
freckle workflow saved runs watch <workflowId> <runId...> --watch-timeout 10m
freckle workflow saved runs inspect <workflowId> <runId>
freckle workflow saved runs list <workflowId> --status completed --limit 25
```

`--watch-timeout` accepts positive integer durations ending in `s` or `m`, for example `30s`, `5m`, or `10m`,
up to `10m`. Watch up to 100 Workflow Run IDs per command.
Optional outputs from unselected branches may be omitted from run outputs.

## Run Errors

A failed run or node carries a product-safe error:

```yaml
error:
  kind: <error-code>
  category: <failure-category>
  message: <human-readable-explanation>
  details: <optional-safe-facts>
```

Choose how to react from `category` alone:

- `invalid_config` — the node's config is wrong. Fix the workflow draft and republish.
- `invalid_input` — a bound input value is wrong or missing. Fix the upstream data or bindings.
- `connection` — the Integration Connection has a problem (revoked credentials, missing scopes, or a rate limit tied to that connection). Reconnect the Integration Connection or resolve the limit in the Integration; see [../CONNECTIONS.md](../CONNECTIONS.md).
- `provider_unavailable` — a transient upstream outage. Retry the run; no workflow change is needed. Any `kind` ending in `.runtime.provider_unavailable` means this.
- `internal` — Freckle hit an internal error. The `kind` is always `freckle.node.internal`. Retry the run; if it persists, tell the user to contact Freckle support with the run id from `details`.

Node-specific `kind` values and their fixes are documented per node in `workflow node inspect <definition-key>` under `authoring.commonDiagnostics`. Errors persisted before categories existed may omit `category`; treat those as unknown and read the `message`.

**Sample gate:** before running a saved Workflow across user rows, check the row count. Read [credit-cost.md](credit-cost.md) and return its Credit Forecast Summary after the first 10 input rows’ runs reach terminal states.

- 20 or fewer rows: run all rows and inspect each run until terminal.
- More than 20 rows: run the first 10 representative rows, inspect results until terminal, show those preview inputs and results plus the Credit Forecast Summary to the user, and ask whether to continue before running the rest.

After processing rows, report final results as a Markdown table: every row when there are 20 or fewer; 10 representative rows, clearly labeled as a sample, when there are more.
