# Build With Freckle

Freckle work lands in a **Workbook**: an input Dataset holding the user's rows, a Workflow wired to it, and an output Dataset collecting the newest result for each row. The Workflow is the reusable engine; the Workbook is what the user actually gets. When a user asks Freckle to do something, the destination is a Workbook unless they explicitly scope the request to a Workflow artifact — and even then, the path below still applies; the workbook parts simply fall away.

**This path is gated.** If the request asks Freckle to produce, change, or run anything, however small or clear it seems, your next action is to read [steps/step-1-context.md](steps/step-1-context.md) — the first command you run comes from that file. Several steps end in a question only the user can answer, so this path completes only in conversation with the user; finishing silently means the path was not followed.

Before anything else, write these six steps into your todo list, one item per step, using these exact labels — the user sees this list, so the labels stay jargon-free:

1. [Pick a workspace](steps/step-1-context.md) — derive the destination org from a named Workflow or Workbook, or the user picks it from the full org table.
2. [Nail down the goal](steps/step-2-objective.md) — check reuse across Workbooks and Workflows, then grill until no shape-changing unknowns remain.
3. [Scout the nodes and map the data](steps/step-3-contract-map.md) — inspect every planned node's contract and price; design the data mapping and outputs.
4. [Sign off on the plan](steps/step-4-plan.md) — render the workbook picture, diagram, result-fields table, and Credit Cost Summary; user approval freezes the plan.
5. [Set up the workbook and build it](steps/step-5-draft.md) — stand up the Workbook and load the data first, then author the frozen plan faithfully; validate to exit 0.
6. [Wire it up and run it](steps/step-6-run.md) — ship the Workflow, connect it to the Workbook, run through the sample gate.

Read each step file only when entering that step, and start the next step only after the current step's completion criterion passes. The user gates are steps 1, 2, and 4; steps 3, 5, and 6 flow without pausing — plan approval at step 4 covers the wiring and run intent, and step 6 pauses only for a deviation or its sample gate. When a message to the user ends a step, describe what happens next accurately; never promise an action that belongs to a later step.

Every message to the user speaks to a GTM or marketing audience, not developers. Product language is fine — Workbook, Dataset, node, Workflow, org, run, provider, Research Agent — users know those words. Translate programming jargon: "the checks pass" not "validation exits 0", "what each column will show" not "typed object output", "connected" not "bound to the output port". Keep the tone plain and a little playful.

The work is **contract-first**: inspect node contracts before authoring, preview dynamic nodes after their config exists, validate drafts before save or publish, and map dataset fields only against the workflow's published input shape. The server-backed node catalog, Workflow compiler, and workbook inspect output are authoritative — anything they can tell you, look up there. Node, saved-workflow, and run commands live in [workflow/cli-reference.md](workflow/cli-reference.md); workbook commands and semantics live in [WORKBOOKS.md](WORKBOOKS.md); the steps tell you when to use them.

## Non-Building Requests

| Request | Load |
| --- | --- |
| Scoped tweak to an existing Workflow or Workbook — swap a provider, change an output field, adjust config or a mapping | [REFINE.md](REFINE.md) — it owns the fit test and escalates redesigns back here |
| Run an existing saved Workflow directly with JSON inputs, inspect runs, list saved Workflows | [workflow/cli-reference.md](workflow/cli-reference.md) — apply its sample gate before any run over user rows |
| Workbook housekeeping that changes nothing about what runs — inspect, archive, delete entries, rotate webhook secrets | [WORKBOOKS.md](WORKBOOKS.md) |
| Inspect node capabilities | [workflow/cli-reference.md#node-catalog](workflow/cli-reference.md#node-catalog) |
| Debug a failing draft validation | [workflow/draft-syntax.md](workflow/draft-syntax.md) |
| Reason about an existing enrichment Workflow | [workflow/waterfall.md](workflow/waterfall.md), [workflow/collector.md](workflow/collector.md), [workflow/research-agent.md](workflow/research-agent.md) — recognize provider ordering, fallback branches, the collector, and the Research Agent's role before touching them |

Changing an existing Workflow or Workbook beyond a scoped tweak — a redesign of its shape — is building: it goes through the gated path above.
