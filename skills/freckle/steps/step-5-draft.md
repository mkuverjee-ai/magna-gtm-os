# Step 5: Workbook Up, Draft Validated

**Gate:** the frozen step-4 plan comes first — the first line of Workflow Draft YAML, and the first `workflow draft init`, come after it. Missing plan → return to step 4.

## Stand up the Workbook

The Workbook and its input Dataset go up **before any Workflow YAML** — they are what the user watches in the UI, so they land first. Commands and semantics are in [WORKBOOKS.md](../WORKBOOKS.md); read it before creating anything. Skip items already satisfied by the frozen plan's reuse decisions; a Workflow-artifact request with no Workbook skips this whole section.

- Create the Workbook (`workbook create --label ...`) or reuse the frozen existing one.
- Create the input Dataset and ingest the data — `dataset build new csv` for a CSV into a new Dataset, `dataset csv import` / `dataset entry create` for an existing one, `dataset webhook create` for an external feed (give the user the endpoint URL), or `dataset hubspot create` for a new Dataset plus its manual HubSpot source and first import. For HubSpot, use the frozen credential, object type, repeated ordered properties, and exactly one of `--list-id`, `--all-records`, `--criteria-json`, or `--criteria-file`; never combine a list with filter groups, preserve the full filter-group structure, and use a stable create request ID. Capture the returned Dataset and source IDs. Ingest the full data now; step 6's sample gate controls how much *runs*, not how much is loaded.
- If the frozen mapping needs catalog fields the Dataset lacks, apply the frozen catalog edit (`dataset catalog replace`).
- Create every new Push destination in the same Workbook, apply its frozen field catalog, and capture its id before authoring. Reuse a user-specified Dataset as directed; otherwise reuse only the destination pinned by the inspected Workflow design. For an existing Dataset, run `catalog replace` only when fields are missing, using the frozen complete catalog that preserves all existing fields. Commands and provenance semantics are in [push-to-dataset.md](../workflow/push-to-dataset.md).

## Author the draft

Reusing a saved Workflow as-is → nothing to draft; read [step-6-run.md](step-6-run.md) now.

Read [draft-syntax.md](../workflow/draft-syntax.md) before authoring.

- Create a starter draft, then edit the YAML directly:

  ```bash
  freckle workflow draft init <workflow-slug> --file workflow.yaml
  ```

  For changes to an existing saved Workflow, or a clone-and-extend, start from the draft exported with `workflow saved get-draft` instead — see [cli-reference.md#saved-workflows](../workflow/cli-reference.md#saved-workflows). In a clone-and-extend, keep the preserved segment intact and edit only what the frozen plan changes.

- Author the frozen diagram faithfully: every drawn provider, branch, Research Agent role, and end state appears in the draft, in the drawn order, and every branch routes on its drawn condition to its drawn target. Plumbing nodes (collectors, switches, JS transforms) are yours to add — the diagram deliberately omits them, but they must not invert or rewire a drawn branch. Before writing, compare the intended draft to the diagram; a missing, reordered, inverted, or rewired provider, branch, or end state is a plan change (step 4). If validation friction or node wiring makes the plan impractical, stop and ask the user to approve the smallest revised plan instead of simplifying silently.
- Give every Code (`code`), Research Agent (`researchAgent`), and Apollo Find People (`apolloFindPeople`) node you author both a `title` and a `description`. For every other node, both fields are optional. The title names this node instance's job in the Workflow; the description explains its authored intent. For each Code node, write its description in plain user language to summarize the specific transformation or decision and the resulting output. Never copy the generic Code Node Definition description, such as “Runs sandboxed JavaScript code to transform workflow data”. Preserve missing authored metadata on unchanged historical nodes; do not generate or backfill it. Put both fields directly on the node, not in `config`; limits and syntax are in [draft-syntax.md](../workflow/draft-syntax.md).
- Keep the draft's workflow inputs aligned with the frozen mapping table: every mapped input exists, with the type the mapping assumes.
- If the plan branches — parallel enrichments or a waterfall — re-read [collector.md](../workflow/collector.md) before wiring the convergence collector.
- Re-read [apollo-find-people.md](../workflow/apollo-find-people.md) and [push-to-dataset.md](../workflow/push-to-dataset.md) when those nodes are present. Bind complete Apollo people objects directly for a handoff and expose the Push receipt as planned.
- Check the authored `outputs` map against the frozen result-fields table; declare the typed object's top-level fields explicitly.
- Preview dynamic nodes after their config exists in the draft (`workflow node preview <nodeId> --file workflow.yaml`), then update the draft if the preview changes the surface.
- Validate, fix diagnostics, and rerun until it passes:

  ```bash
  freckle workflow draft validate --file workflow.yaml
  ```

**Completion** — every box checked (the draft boxes fall away when reusing a saved Workflow as-is):

- [ ] The Workbook, input Dataset, and every Push destination exist in the same Workbook, with their ids and frozen catalogs captured.
- [ ] Every authored Code, Research Agent, and Apollo Find People node has a `title` and `description`.
- [ ] The authored `outputs` map matches the frozen result-fields table, with the typed object's top-level fields explicit.
- [ ] Complete handoff arrays feed their Push nodes, and the draft's inputs match the frozen mapping.
- [ ] You have run `workflow draft validate` on the final draft and seen exit 0.

Completion met → read [step-6-run.md](step-6-run.md).
