# Step 6: Wire Up and Run

**Gate (authored drafts only):** before saving or publishing, check the draft against the frozen diagram and result-fields table one last time: every drawn provider, branch, Research Agent role, and end state must be present, in order, and routed on its drawn condition to its drawn target, and each result field must come from its pinned source node — for guarded `oneOf` outputs, checked per entry: each guard branch case paired with the source that case activates, on the guard node the plan implies (plumbing nodes beyond the diagram are expected). Any missing, reordered, inverted, or rewired one is a plan change (step 4). Save or publish only after validation exits 0.

Plan approval already authorized the pinned wiring and run intent — proceed on that authority. Pause here only when the fidelity check finds a deviation, the intent was somehow never pinned, or the sample gate applies.

Workbook commands and semantics for everything below are in [WORKBOOKS.md](../WORKBOOKS.md); read it before wiring. Read [credit-cost.md](../workflow/credit-cost.md) before reporting run costs.

## Ship the Workflow

Skip when reusing a saved Workflow as-is or feeding an already-wired Workbook.

- New Workflow: `workflow saved create`; keep the returned `workflow.id`. New revision of an existing Workflow: `workflow saved lifecycle publish`. Commands are in [cli-reference.md#saved-workflows](../workflow/cli-reference.md#saved-workflows).

## Connect the Workbook

The Workbook, input Dataset, and ingested data already exist from step 5. Feed-and-run arrives here directly instead: ingest the new rows into the existing input Dataset (ingestion commands in [WORKBOOKS.md](../WORKBOOKS.md)), then skip to the sample gate.

- Create every planned connection with its frozen mapping: `dataset connection create ... --file mapping.json --trigger-policy manual` — **always manual at creation**, even when the plan says automatic; each flip happens after that connection's sample gate. Keep every returned `connection.id` and `outputDatasetId`. Skip connections that are already wired.
- For a HubSpot input, poll `dataset hubspot inspect <workbook-id> <source-id>` until `latestRun.status` is `completed` before triggering the connection. Report `pagesProcessed`, `recordsRead`, `insertedCount`, `updatedCount`, and `unchangedCount`; if it fails, report `latestRun.error` and stop — downstream work waits for a completed import. A user-requested later refresh uses `dataset hubspot run-again ... --request-id <new-stable-id>` with no selection flags, then the same inspect gate. Imports are full scans with merge-only semantics; there are no schedules, incremental watermarks, source edits, or mirror/delete behavior.

## Run through the sample gate

- 20 or fewer input rows: `dataset connection trigger` and inspect every run to a terminal state.
- More than 20 rows: `dataset connection trigger --limit 10`, watch `dataset connection runs` until those reach terminal states, read the produced entries from the output Dataset, show the user a Markdown table of those sample inputs and results, add the **Credit Forecast Summary** required by `credit-cost.md`, and ask whether to continue before running the rest.
- At 10 or more input rows, return the **Credit Forecast Summary** after the first 10 input rows’ runs reach terminal states. For 20 or fewer rows triggered together, report it when inspection finishes; for fewer than 10 rows, say the sample is too small for a forecast.
- When Push is present, also inspect each Push receipt and the entries committed to every Push destination. Include a representative pushed-entry table in the sample report. A Push sample still means ten upstream input entries; Apollo's people-per-organization count remains the user-approved value.
- Sample approved (or not needed): loop `dataset connection trigger` until `startedCount` is 0 — each call admits at most 100 pending entries.
- For a chained Workbook graph, repeat the gate from upstream to downstream. Keep newly created downstream connections manual until their pending Push entries pass their own sample, then catch them up before switching to automatic.
- Failures: report failed runs from the ledger; `dataset connection rerun-failed` only when the user asks — failed rows never retry automatically.
- Plan says automatic: after the catch-up trigger above, `dataset connection set-trigger-policy auto` (flipping first would strand already-pending rows — auto does not catch up).

A Workflow-artifact request with no Workbook runs rows per [cli-reference.md#run-saved-workflows](../workflow/cli-reference.md#run-saved-workflows) instead, applying its sample gate.

## Hand off the created assets

End a creation flow with a complete list of clickable links to every newly created Workbook and Workflow:

- Workbook: `[<label>](https://next.freckle.io/workbooks/<workbook-id>)`
- Workflow: `[<label>](https://next.freckle.io/tools/<workflow-id>)`

Keep Dataset ids for execution and verification; the created-assets handoff contains the Workbook and Workflow links only.

**Completion** — every box checked:

- [ ] All created ids are captured: Workbook, Datasets, connections, Workflows, runs.
- [ ] Every started run reached a terminal state.
- [ ] Ordinary outputs and every Push destination were inspected.
- [ ] Results were shown to the user as Markdown tables — every input at 20 or fewer rows; 10 representative inputs, labeled as a sample, when more.
- [ ] The `credit-cost.md` Credit Forecast Summary was returned after the first 10 input rows’ runs reached terminal states.
- [ ] Every connection's trigger policy matches the frozen plan.
- [ ] The final handoff links every newly created Workbook and Workflow, with no Dataset ids in the created-assets list.
