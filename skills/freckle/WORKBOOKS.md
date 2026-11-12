# Freckle Workbooks Reference

Commands and semantics for Workbooks, Datasets, and Workflow Dataset Connections. If the current request builds or changes what a Workbook runs and you have not entered the gated path in [BUILD.md](BUILD.md) or the refine path in [REFINE.md](REFINE.md), go back — these commands do not replace those paths.

A **Workbook** contains Datasets and connections. A **connection** reads entries from one input Dataset, maps them into a saved Workflow's inputs, runs them, and collects results into one output Dataset it creates in the same Workbook. The output Dataset holds only the newest result per input row — re-running a row replaces its outputs, never appends.

Most commands print YAML by default and accept `--json` for pretty JSON output. Entry create/update and connection create use `--json` for inline *input*, so read their output as YAML. Org-scoped commands accept `--org-id` and `--token` overrides.

## Workbooks

```bash
freckle workbook create --label "Leads" --description "Lead enrichment"
freckle workbook list
freckle workbook list --archived
freckle workbook inspect <workbook-id>
freckle workbook update <workbook-id> --label "Qualified Leads"
freckle workbook archive <workbook-id>
freckle workbook unarchive <workbook-id>
```

`workbook list` rows include each Workbook's Datasets (`id`, `label`, `fieldPaths`, `archivedAt`) and connections (`workflowId`, input/output dataset ids, `triggerPolicy`) — enough to see what every Workbook does without inspecting each one. `workbook inspect` returns the full graph: Datasets with complete field catalogs, and connections with input mappings and unfold config. Archived Datasets stay visible in both (connections may still reference them) with `archivedAt` set; they refuse ingestion and triggers.

## Datasets

```bash
freckle workbook dataset list <workbook-id>
freckle workbook dataset create <workbook-id> --label "<label>" --description "<description>"
freckle workbook dataset inspect <workbook-id> <dataset-id>
freckle workbook dataset archive <workbook-id> <dataset-id>
freckle workbook dataset delete <workbook-id> <dataset-id>
```

Entries and ingestion:

```bash
freckle workbook dataset entry list <workbook-id> <dataset-id> --limit 100
freckle workbook dataset entry create <workbook-id> <dataset-id> --json '{"email":"person@example.com"}'
freckle workbook dataset entry create <workbook-id> <dataset-id> --file entry.json
freckle workbook dataset entry update <workbook-id> <dataset-id> <entry-id> --file entry.json
freckle workbook dataset entry delete <workbook-id> <dataset-id> <entry-id...>
freckle workbook dataset csv import <workbook-id> <dataset-id> --file rows.csv --key-column email
freckle workbook dataset build new csv <workbook-id> rows.csv --label "Imported Leads" --key-column email
```

`build new csv` creates the Dataset and imports in one shot, deleting the Dataset again if the import fails. `entry list` paginates with `--cursor`/`--limit`; entry deletion is asynchronous and also deletes downstream entries derived through workflow lineage.

## Sources and keys

```bash
freckle workbook dataset source list <workbook-id> <dataset-id>
freckle workbook dataset webhook create <workbook-id> <dataset-id> --key-path /email
freckle workbook dataset webhook rotate <workbook-id> <source-id>
freckle workbook dataset hubspot create <workbook-id> --label "HubSpot List Contacts" --credential-id <credential-id> --object-type contacts --property email --property firstname --list-id <stable-list-id> --request-id <stable-request-id>
freckle workbook dataset hubspot inspect <workbook-id> <source-id>
freckle workbook dataset hubspot run-again <workbook-id> <source-id> --request-id <stable-request-id>
```

Every entry enters through a source — `manual`, `csv_upload`, `webhook`, `hubspot`, `workflow_output`, or `workflow_node` — and carries a **source key** that identifies its logical record within the Dataset. A Dataset is the entry container and may have multiple configured sources; each entry belongs to exactly one. Repeat-key behavior depends on the source:

- CSV with `--key-column`: key is that column's value; re-imports update matching rows. Rows with an empty key are skipped and reported. Without `--key-column`, keys are positional per import — a re-import creates duplicates, so prefer a key column.
- Webhook: key is the value at `--key-path` (JSON Pointer) in each posted record; must be a non-empty scalar.
- HubSpot: key identifies the portal, object type, and HubSpot object id; later manual imports update the same logical records instead of duplicating them. Records no longer returned by HubSpot remain in the Dataset.
- Manual entries: keyed by their own id; `entry update` replaces the value and bumps the version.
- Workflow node entries: written by Push to Dataset through one reused `workflow_node` source per Dataset; their keys identify the producing Workflow Run, node, and array index. Repeating the same run/node/index reuses the entry; a separate run has distinct keys. See [workflow/push-to-dataset.md](workflow/push-to-dataset.md).

`webhook create` returns an `endpointUrl` containing a secret; external systems POST one JSON object or an array of them (limits: 1000 records and 5 MB per request, 100 requests/min). `webhook rotate` invalidates the old URL.

### Manual HubSpot imports

`hubspot create` creates a new Dataset, configures its source, and starts the first import; it does not attach HubSpot to an existing Dataset. Get an authorized public credential ID with `connections show hubspot`, select `contacts`, `companies`, or `deals` with `--object-type`, and repeat `--property` in the order fields should be retained. `--description` is optional.

Record selection is always explicit. Pass exactly one of:

- `--list-id <stable-list-id>` to import members of one HubSpot list. List selection is independent and never combines with filter groups.
- `--all-records` to import every record of the selected object type.
- `--criteria-json '<json>'` for inline filter-group criteria.
- `--criteria-file <path>` for filter-group criteria stored in a JSON file. Prefer this for non-trivial filters.

List creation sends criteria exactly as `{ "kind": "list", "listId": "<stable-list-id>" }`. Filter criteria use the complete `HubspotDatasetImportCriteria` shape and preserve nested groups:

```json
{
  "kind": "filter_groups",
  "filterGroups": [
    {
      "filters": [
        { "propertyName": "lifecyclestage", "operator": "EQ", "value": "customer" },
        { "propertyName": "country", "operator": "IN", "values": ["India", "Singapore"] }
      ]
    },
    { "filters": [{ "propertyName": "annualrevenue", "operator": "GTE", "value": "1000000" }] }
  ]
}
```

Filters within one group are ANDed; groups are ORed — pass the complete nested JSON as one value so that structure survives. Criteria allow 1–5 groups, 1–6 filters per group, and 18 filters total. Select 1–200 unique properties. Supported operators are `EQ`, `NEQ`, `GT`, `GTE`, `LT`, `LTE`, `CONTAINS_TOKEN`, `NOT_CONTAINS_TOKEN`, `IN`, `NOT_IN`, `BETWEEN`, `HAS_PROPERTY`, and `NOT_HAS_PROPERTY`. Single-value operators use `value`; `IN`/`NOT_IN` use a non-empty `values` array; `BETWEEN` uses `value` and `highValue`; property-existence operators take none of those fields.

Always give create and run-again operations an operation-specific stable `--request-id`. Retrying create with the same request ID in the same Workbook returns the original source/run; retrying run-again with the same request ID for one source returns the original run. A genuinely new import gets a fresh ID.

`hubspot inspect` returns the pinned config and `latestRun`. Read `latestRun.status` (`pending`, `running`, `completed`, or `failed`), `pagesProcessed`, `recordsRead`, `insertedCount`, `updatedCount`, `unchangedCount`, and `error`; poll inspect when a terminal result is required. `hubspot run-again` accepts no criteria and starts another manual import with exactly the pinned source config. In its immediate response, read the top-level `run` as authoritative: the nested `source.latestRun` can still show the prior run until the next inspect. Imports are full scans with merge-only Dataset semantics: removed list members remain. There are no schedules, incremental watermarks, source edits, or mirror/delete-missing mode.

## Field catalogs

The **field catalog** names the Dataset fields Freckle can render as columns and map into workflow inputs — entries may hold extra fields, but only cataloged ones are mappable. Catalog format (`--file catalog.json`, either `{ "fieldCatalog": [...] }` or the bare array):

```json
[{ "id": "email", "path": "/email", "label": "Email", "type": "string", "visible": true, "order": 0 }]
```

Types: `string`, `number`, `boolean`, `json`. An empty catalog is seeded automatically from the first field-bearing manual entry, webhook batch, CSV import, or Push to Dataset write; a connection's output Dataset is seeded from the workflow's output shape. Empty objects remain valid for constant-only Workflow rows and leave the catalog empty until a later field-bearing write. Once a catalog is non-empty, ingestion never extends or changes it; edits are explicit:

```bash
freckle workbook dataset catalog replace <workbook-id> <dataset-id> --file catalog.json
```

## Connections

```bash
freckle workbook dataset connection create <workbook-id> <input-dataset-id> <workflow-id> --file mapping.json --output-label "Enriched" --trigger-policy manual
freckle workbook dataset connection inspect <workbook-id> <connection-id>
freckle workbook dataset connection trigger <workbook-id> <connection-id>
freckle workbook dataset connection trigger <workbook-id> <connection-id> --limit 10
freckle workbook dataset connection run <workbook-id> <connection-id> <entry-id>...
freckle workbook dataset connection rerun-failed <workbook-id> <connection-id>
freckle workbook dataset connection runs <workbook-id> <connection-id> --limit 25
freckle workbook dataset connection set-trigger-policy <workbook-id> <connection-id> --trigger-policy auto
```

`connection create` requires an active (non-archived) Workflow with a published revision, creates the output Dataset in the same Workbook, and returns the connection with `outputDatasetId` — keep both ids. Add `--unfold-output-id <outputId>` to unfold (below).

### Input mappings

The mapping file assigns every workflow input a cataloged field or a constant:

```json
{
  "email": { "kind": "field", "fieldId": "email" },
  "region": { "kind": "constant", "value": "EMEA" }
}
```

Keys are the workflow's input ids (see `shape` on `workflow saved list` or `schema` on `workflow saved inspect`); `fieldId` is a field catalog id on the input Dataset. Field types must be assignable to the input types. The mapping is checked at creation *and* re-checked against the workflow's current contract at every trigger — publishing a revision that breaks the mapping makes triggers reject with a diagnostic.

### Pending and triggering

An entry is **pending** for a connection when its current version has no recorded run for that connection — new entries, updated entries, and upserted entries all pend; a finished run un-pends that version.

- A manual `trigger` admits pending entries oldest-first (dataset order, top of the table), at most 100 per call (`--limit 1..100` to admit fewer, e.g. a sample of the first rows). Loop until `startedCount` is 0 to drain a large Dataset.
- `--trigger-policy auto` starts runs as entries become pending. Switching a connection to auto does **not** catch up already-pending entries — trigger manually first, then flip.
- Failed runs never retry automatically. `rerun-failed` re-runs failed current-version entries, reusing their ledger records (no retry history).
- `runs` pages the ledger: each record binds one input entry version to one Workflow run, with status (`running`/`completed`/`failed`/`discarded`) and failure detail.

### Explicit entry runs

`connection run` sends one ordered batch of 1–1,000 unique Dataset Entry ids. The entries must be current members of the connection's input Dataset; local argument errors make no request. The response preserves one result per requested id in the same order:

- `started` or `rerun` means Workflow Run Acceptance succeeded and includes the Dataset Entry Run and Workflow Run ids.
- `skipped` means an active run already exists; `rejected` means the entry was unavailable or belonged to another Dataset.
- `failed` means admission reached a stable failure such as stale input, Workflow Run rejection, an unavailable connection, or an internal error. Read each stable `reason` and `diagnostic`.

Missing entries and logically deleted entries both return `rejected/not_found`; entries found in another Dataset return `rejected/wrong_dataset`.

A mixed response is successful: inspect every result instead of treating a zero exit status as proof that every entry was accepted. These results report **Workflow Run Acceptance, not execution completion**; use `connection runs` or Workflow Run inspection to follow accepted runs to terminal state.

Connections are live bindings, not revision pins. Workflow Run Acceptance selects the latest Workflow Revision for each entry, so publishing a newer Workflow Revision changes later runs without recreating the connection.

### Outputs and unfold

Each successful run upserts output entries keyed to its input entry: re-running an input replaces its outputs in place (re-pending them for any downstream connection), results from a stale input version are discarded, and a failed run writes nothing. A downstream Workflow Dataset Connection with an auto trigger policy may admit those new or replaced outputs without another manual trigger. Output values are exactly the workflow output; lineage (`producedByRunId`, `producedFromEntryId`, `producedFromEntryVersion`) sits beside the value.

**Unfold** elects one array-of-objects workflow output at creation (`--unfold-output-id`): each array element becomes its own output entry, sibling workflow outputs are not collected, and re-runs remove surplus elements the newer result no longer produces.

## Limits and workarounds

- A connection's mapping, unfold config, and output label cannot be edited, and connections cannot be deleted. To change a mapping: create a new connection on the same input Dataset (allowed — one Dataset can feed many connections), which creates a fresh output Dataset; leave the old connection on `manual` and it stays inert.
- Datasets cannot be renamed or unarchived; a Dataset can be hard-deleted only while no connection references it.
- No CSV export; read output entries with `dataset entry list`.
- An input Dataset may feed many connections, and a connection never crosses Workbooks.
- Archived Workbooks/Datasets refuse ingestion and triggers; archived Workbooks are hard-deleted 30 days after archiving.
