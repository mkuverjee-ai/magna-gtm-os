# Step 2: Objective Pinned

**This step is the build.** A fully pinned objective makes steps 3–6 mechanical; a half-pinned one poisons all of them. Spend disproportionate effort here: run the [shared batch grill](../SKILL.md#shared-operating-rules) relentlessly before producing any plan. Keep an explicit design tree and unknowns list; each round asks every currently unblocked decision together, while dependent decisions wait for later rounds.

## Reuse first

Scan the **Active Organization** — and only it — before designing anything.

- `freckle workbook list` — each Workbook row includes its Datasets (with field paths) and its connections (which Workflow reads which Dataset, and the trigger policy), so the list alone shows what each Workbook already does.
- `workflow saved list` — each row includes the Workflow's input/output shape when it has a published revision ([cli-reference.md#saved-workflows](../workflow/cli-reference.md#saved-workflows)).

Classify what you find, most reuse first:

- **Feed and run** — a Workbook is already wired for this goal; the new data just needs ingesting and running. This decision ends the design work: confirm the fit with `workbook inspect`, then go straight to [step-6-run.md](step-6-run.md) (its wiring items no-op; the sample gate still applies).
- **Wire an existing Workflow** — a saved Workflow already does the job as-is; only the Workbook wiring is new. Steps 3–5 shrink: no node scouting or drafting, only data mapping and the plan.
- **Clone-and-extend** — a saved Workflow covers a validated segment of the goal (input trigger, enrichment waterfall, provider spine, normalized outputs, or downstream action) and needs nodes added, replaced, or removed. A partial match qualifies: a Workflow that lacks the final requested fields, scoring, routing, or destinations still counts when it covers a validated segment. Inspect its metadata (`workflow saved inspect`), export its draft (`workflow saved get-draft`), and note what will be preserved exactly and what changes.
- **Start new** — nothing materially reduces the work, or reuse would fight the requested shape.

Prefer the highest classification any candidate reaches. Present the best reuse option before continuing the interview.

## Design tree

Seed the tree with the branches below. Dependencies determine the frontier: for example, the data source unlocks its key and cadence questions, while the enrichment goal plus provider inspection unlock provider and fallback questions. Ask every independent branch on the current frontier in the same numbered round, with a recommended answer for each.

- **The data.** What rows exist and where: a CSV in hand, records arriving from an outside system (webhook), a manual HubSpot import, or rows the user will paste in? For CSV rows, which field uniquely identifies a row (the key column — re-imports update rather than duplicate)? For HubSpot, resolve the authorized credential ID, object type (`contacts`, `companies`, or `deals`), properties to retain, and exactly one selection mode: a stable list ID, all records, or exact preserved filter groups. Roughly how many rows?
- **The destination.** Add this data to an existing Workbook's Dataset, or start a new Workbook? New Workbooks need a label from the user.
- **The cadence.** Follows from the data source: a webhook feed runs continuously (automatic trigger policy); everything else, including HubSpot imports, is a one-shot/manual batch (manual trigger policy). Recurring HubSpot imports are not available.
- **The workflow.** Enrichment goal, failure behavior, required output columns, and whether this is new or changing an existing Workflow.

When Apollo Find People is a candidate, read [apollo-find-people.md](../workflow/apollo-find-people.md) before finishing the interview; resolve whether its people are in-Workflow evidence or a Dataset handoff, and ask for the people-per-organization count when unspecified.

- Resolve questions answerable from the repo, current folder, Workbook inspects, saved Workflows, or node catalog by inspection. While independent lookups run, continue with every unaffected frontier question.
- Recompute the frontier after every reply or lookup. Continue until every unknown about the user's intended Workbook wiring, Workflow purpose, outputs, failure behavior, or run behavior is answered by the user or resolved by inspection.

A request the user explicitly scopes to a Workflow artifact — invoke with JSON inputs, publish a revision, edit a draft — skips the data and destination branches; classify against saved Workflows only. Exception: a Workflow containing Push to Dataset still needs its same-Workbook destination Dataset, catalog, sources, and readers resolved; it may skip input ingestion and connection creation, not Push destination preparation.

**Completion** — every box checked:

- [ ] Every relevant Workbook and saved Workflow in the Active Organization is classified on the reuse ladder.
- [ ] The reuse decision is resolved, and the best reuse option was presented to the user.
- [ ] The unknowns list is empty: every user-intent shape-changing unknown was answered by the user or resolved by inspection.
- [ ] You can restate in plain English: the objective, the data and its key, the destination Workbook decision, the cadence, the outputs, the reuse decision, the failure policy, and the run expectation.

Completion met with a feed-and-run decision → read [step-6-run.md](step-6-run.md). Otherwise → read [step-3-contract-map.md](step-3-contract-map.md) **in the same turn** and continue straight through — the next thing the user sees is the step-4 plan, which opens with this restatement and is where they confirm it.
