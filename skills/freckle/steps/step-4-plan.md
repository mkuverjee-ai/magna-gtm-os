# Step 4: Plan Accepted

Present the plan and get explicit approval. Once accepted, the plan is **frozen**.

- Open the plan message with the plain-English objective restatement from step 2 — this is where the user confirms it, together with the plan.
- Draw the **Workbook picture** first: input Dataset (source kind and key column) → Workflow → output Dataset. Add every Push destination as a named side handoff and continue into any downstream Workflow connections the user described. Name the destination Workbook — existing label or the new label the user chose — and state each connection's trigger policy: run on demand, or automatically as new entries arrive.
- Present the high-level workflow plan in plain English: why each provider is included, what triggers each fallback, and what the Research Agent should attempt. For a Workflow reused as-is, state that it runs unchanged and skip the diagram bullets below.
- Render a concise ASCII diagram every time, at **provider level**: inputs, structured providers, the branch conditions between them (found / not found), the Research Agent, and every end state — including the all-fallbacks-failed path. Plumbing — collectors, switches, and JS transform/extract nodes — is implied by the branches and stays out of the diagram. The draft will contain more nodes than the diagram shows; that is expected, not a deviation.
- Draw **one connected diagram** covering every scenario. Each provider and each downstream chain appears exactly once; branches split at a labeled miss condition and rejoin where the paths converge on the shared downstream. About to draw the same provider twice? Rejoin the branches above it instead.
- Check the planned node list for **node bloat**: duplicated downstream chains per branch, one Workflow Output per branch where the user asked for one result, or chains that never rejoin a shared downstream binding. Converge through one collector ([collector.md](../workflow/collector.md)) and re-render.
- Render a Markdown table of the **mapping**: each workflow input, and the dataset field or constant that feeds it.
- Render a Markdown table of planned result fields with columns `Data point` and `Source`; `Source` names the node that produces the field. Enumerate each top-level field of the planned typed object output as its own row — these are the output Dataset's columns. If unfold is planned, say each item of the named output becomes its own row and sibling outputs are not collected.
- Apply [credit-cost.md](../workflow/credit-cost.md) immediately below that table and render its **Credit Cost Summary** for approval.
- When Push is planned, render a `Dataset handoffs` table with destination label/id, producing node, complete object-array source, cataloged fields, and downstream readers. Its producing Workflow's result-fields table contains the Push receipt, not a duplicate people array.
- State the reuse decision from step 2 as part of the plan — feed-and-run, wire an existing Workflow, clone-and-extend of a named saved Workflow (with what is preserved and what changes), or start new.
- State the run intent from step 2 as part of the plan — what gets saved or published, which rows run, and whether the connection flips to automatic afterward.
- Ask for explicit confirmation that the user is fully okay with this exact plan before any building begins. Describe what approval triggers accurately: you will set up the Workbook and load the data, build and validate the Workflow, connect it, and run without asking again — the only later pause is the sample gate on more than 20 rows.

## Frozen

After acceptance, the drawn shape is binding: the Workbook picture, diagram, mapping, result-fields table, Credit Cost Summary, and Dataset handoffs pin the datasets, the Push destinations with their catalogs and downstream readers, the mapping, the trigger policy, the providers and their ordering, the branch structure, the Research Agent role, failure behavior, every end state, and the stated credit maximums or formulas. A draft that differs from that shape in any pinned element — even by simplification, substitution, or a temporary shortcut — is a plan change: stop and get explicit approval for a revised plan first. A planned fallback is a rung, not a replacement Workflow. Plumbing nodes are yours to add freely — collectors, switches, and JS nodes as the draft needs — as long as they implement exactly the drawn branches.

**Completion** — every box checked:

- [ ] The Workbook picture, ASCII diagram, mapping table, result-fields table, Credit Cost Summary, and any Dataset handoffs table are rendered in the plan message.
- [ ] The user explicitly confirmed the full plan — destination org, Workbook destination, Push destinations, downstream readers, trigger policies, reuse choice, run intent, and the stated credit maximum or uncapped formula.
- [ ] If the user changed anything, you returned to the earliest affected step and re-confirmed the revised plan before building.

Completion met → read [step-5-draft.md](step-5-draft.md).
