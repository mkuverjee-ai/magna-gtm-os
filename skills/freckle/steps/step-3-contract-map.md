# Step 3: Contract Map Built

This step is contract inspection and design only; authoring and creating begin in step 5, after the plan freezes.

Nothing here needs the user: do the inspection legwork silently and continue into step 4 in the same turn, so the user's next message from you is the plan.

## Scout the nodes

Skip contract scouting entirely when reusing a saved Workflow as-is — its published shape and top-level `costEstimate` (from `workflow saved inspect`) are authoritative for shape and unit prices. Resolve fixed result caps from the exact revision export required by `credit-cost.md`; keep an explicit formula when a cap is input-dependent or unverifiable.

Inspect every node you plan to use with the [node catalog commands](../workflow/cli-reference.md#node-catalog):

- `workflow node inspect <definitionKey>` for each planned node; the full entry includes config and authoring guidance that `--contract` omits.
- Capture `creditCost` and `creditCostModel` from the full entry for every planned occurrence of the node.
- If a planned node is dynamic, note the config required to preview its surface; the preview happens in step 5, after the draft exists.

When the plan uses Apollo Find People, read [apollo-find-people.md](../workflow/apollo-find-people.md). When it uses Push to Dataset, read [push-to-dataset.md](../workflow/push-to-dataset.md). Apply their evidence/handoff decision and destination rules rather than treating every object array as an ordinary Workflow output.

### Enrichment

Waterfall-first is the default: design enrichment as a provider waterfall even when one provider appears sufficient. Inspect every relevant structured provider node and Research Agent before choosing the plan. Read [waterfall.md](../workflow/waterfall.md) for construction, and [research-agent.md](../workflow/research-agent.md) to decide whether Research Agent is the backstop or the primary node.

### Glue logic

Use JavaScript transform nodes for glue: merging upstream data, normalizing or renaming fields, choosing fallback values, reshaping objects, creating fallback outputs, or preparing combined inputs for downstream nodes. Their ports are dynamic.

Whenever the design branches — parallel enrichments over different data, or fallback branches — plan one collector to converge them before downstream nodes; unconverged branches become node bloat. Read [collector.md](../workflow/collector.md).

### Credit cost

Read [credit-cost.md](../workflow/credit-cost.md), calculate its per-row maximum and any fixed-size Workbook maximum, and carry those facts into step 4. Keep catalog billing labels internal and allocate no credits across result fields.

### Outputs

Plan one typed object Workflow Output for user-facing results, such as `data` or `profile`, with explicit top-level fields — these become the output Dataset's columns. Omit pass-through input columns unless the user explicitly asks to echo inputs; the row already carries them. No opaque `unknown`/raw provider JSON unless the user explicitly asks for raw JSON.

## Map the data

Skip this section only for a Workflow-artifact request with no Workbook destination.

Read [WORKBOOKS.md#input-mappings](../WORKBOOKS.md#input-mappings) and [WORKBOOKS.md#field-catalogs](../WORKBOOKS.md#field-catalogs), then design:

- **The input Dataset's fields** — from the CSV header, a sample record, or the webhook payload shape. If the destination is an existing Dataset, its field catalog (from `workbook inspect`) is authoritative; new fields the mapping needs mean a catalog edit in the plan.
- **The input mapping** — for every workflow input (from the saved Workflow's shape, or the draft's planned inputs), a dataset field or a constant. Field types must be assignable to the input types; a mismatch here becomes a trigger rejection later.
- **Unfold** — if the user wants one output row per item of an array-of-objects workflow output, elect that output for unfold and note that sibling outputs will not be collected.
- **Dataset handoffs** — for every Push to Dataset node, identify the same-Workbook destination: user-specified, pinned by an inspected Workflow as the shared handoff for the same design, or new — the Dataset-wide `workflow_node` source names no writers, so provenance comes from inspected Workflow configs. Inspect every connection that reads the destination, derive its field catalog from the complete object item and downstream mappings, and use the Push receipt as the producing Workflow's result. For an existing Dataset, freeze a complete merged catalog that preserves every current field unchanged and adds only missing handoff fields.

**Completion** — every box checked:

- [ ] Every planned node has a pinned `definitionKey@version` with known config needs, input ports, output ports, branch cases, waterfall/fallback role, `creditCost`, and `creditCostModel` — or the reused Workflow's shape and `costEstimate` are captured from inspect/list.
- [ ] The supported per-row maximum and fixed-size Workbook maximum or uncapped formula are calculated per `credit-cost.md`.
- [ ] When Apollo Find People is planned: it is classified as evidence or handoff, and its result count and per-billable-person maximum are resolved.
- [ ] When Push is planned: every destination, catalog, reader, and complete-object source is known.
- [ ] The final column-shaped outputs are decided.
- [ ] Every workflow input has a mapped dataset field or constant.
- [ ] Any dynamic-preview follow-up for step 5 is noted.

Completion met → read [step-4-plan.md](step-4-plan.md).
