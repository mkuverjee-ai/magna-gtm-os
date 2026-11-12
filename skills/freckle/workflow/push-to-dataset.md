# Push to Dataset

Read this reference whenever `pushToDataset` is planned, added, reconfigured, or encountered in an existing Workflow.

Push to Dataset is a **handoff**: it persists an object array during a Workflow Run so another Workflow can consume those entries from a Dataset. It is not in-run fan-out and does not replace ordinary final Workflow outputs.

## Pick the destination

- Every Push destination belongs to the current Workbook.
- Use a Dataset the user explicitly names, even when it already has other sources.
- Without an explicit target, reuse an existing Dataset only when an inspected Workflow already pins it as the shared handoff for the same design. A Dataset-wide `workflow_node` source does not identify its writers and is not enough evidence by itself. Otherwise create a dedicated Dataset.
- Several Push to Dataset nodes — including several Apollo Find People paths — may share one destination.
- Create the Dataset and fill in its field catalog before authoring the Workflow, then pin its id in node config. For an existing Dataset, preserve every catalog field unchanged and add only missing fields required by the handoff or downstream mappings; `catalog replace` replaces the complete catalog.
- Inspect connections reading the destination before running. Committed entries can immediately enter automatic downstream connections.

## Contract

Inspect the full current catalog entry first:

```bash
freckle workflow node inspect pushToDataset
```

Pin the returned version. The current shape is:

```yaml
uses: pushToDataset@<inspected-version>
config:
  datasetId: <target-dataset-id>
with:
  values: <whole object-array endpoint>
```

`values` must be an array of JSON-compatible objects. Each object becomes one Dataset Entry unchanged. The `result` receipt contains `datasetId` and `pushedCount`; expose that receipt as the producing Workflow's normal output when the pushed values are its handoff.

The target Dataset must already exist and be writable. Push does not create it or validate entries against its field catalog. Only cataloged fields render as columns and map into downstream Workflow inputs, so fill in the catalog for every field the handoff and its readers need. Seeding is a backstop, not a substitute: a push into an empty catalog seeds one field per top-level key of the pushed values, and Push never modifies a non-empty catalog.

## Write semantics

- One execution accepts at most 1,000 objects and 5 MiB of compact serialized JSON.
- The batch is atomic. An empty array succeeds with `pushedCount: 0` after validating the destination and writes no entries.
- The Dataset creates or reuses one `workflow_node` Dataset Source. Each entry's source key is based on Workflow Run, node, and array index.
- Replaying the same run/node/index reuses its entry. A separate Workflow Run uses different source keys and therefore creates distinct entries.
- The receipt confirms committed entries, not completion of downstream Workflow Runs. Automatic downstream admission is best-effort after commit and recoverable by the normal pending-entry sweep.

## Run gate

Sample the first ten input Dataset Entries when the normal sample gate applies. Inspect the Push receipts and the entries committed to every Push destination before continuing the remaining upstream inputs. For a newly built chain, keep downstream connections manual until their own sample has passed; then catch up pending entries before switching them to automatic.

**Completion** — every box checked:

- [ ] Every Push node has a same-Workbook, already-existing destination id in its config.
- [ ] The complete object-array source is known.
- [ ] Every Push destination's field catalog is filled in, covering the pushed fields and the downstream mappings.
- [ ] The Push receipt is represented in the producing Workflow's outputs.
- [ ] Destination readers are understood.
- [ ] Sample verification includes the committed entries.
