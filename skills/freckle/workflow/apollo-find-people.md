# Apollo Find People

Read this reference whenever `apolloFindPeople` is planned, added, or reconfigured.

## Decide the role

Classify Apollo Find People before planning:

- **Evidence** — the people answer a question inside the current Workflow, such as whether an organization has a CTO, and feed scoring or another decision. Keep the `people` array in the Workflow; Push to Dataset belongs only in the handoff role below.
- **Handoff** — the people are themselves useful downstream data. Push the complete person objects into a dedicated Dataset. Handoff is the default when the user asks to find people without naming an in-Workflow use for them.

If the user describes the work after the handoff, plan the pushed Dataset and its downstream Workflow connections as one Workbook graph. If they stop at finding people, leave the pushed Dataset ready for that follow-on work rather than inventing it.

Before freezing the plan, ask how many people Apollo should return for each search when the user has not said. Recommend **3**. Set that count as `request.numResults`; in the usual one-domain request it is the people count for that organization. It is separate from the ten-input-row run sample.

## Credit maximum

Apollo Find People's catalog `creditCost` is the price per billable person returned. Carry its per-input maximum as `creditCost × request.numResults`. For a run of known size, the maximum is `creditCost × request.numResults × input entries`; the actual charge follows the people returned and can be 0 when Apollo finds none.

## Contract and behavior

Inspect the full current catalog entry first:

```bash
freckle workflow node inspect apolloFindPeople
```

Pin the returned version. The current shape is:

- required `config: {}`;
- required `request` object input;
- direct `people` array output;
- no branch cases — `[]` is a successful no-match result.

The exact supported `request` keys are:

- `q_organization_domains_list` — required; 1–1000 non-empty domains.
- `numResults` — optional; integer from 1–100, default **5**.
- `person_titles` — optional; up to 100 non-empty included titles.
- `person_locations` — optional included locations.
- `person_not_titles` — optional excluded titles.
- `person_not_locations` — optional excluded locations.
- `person_seniorities` — optional included Apollo seniority values.
- `person_days_in_current_title_range` — optional current-title tenure range in days. Set `max` to find people who started their current title within the last N days; set `min` to require at least N days. At least one bound is required, and `min` cannot exceed `max`.
- `include_similar_titles` — optional boolean, default `true`.

Endpoint references bind whole values. When Workflow inputs do not already form the complete request object, construct it in a JavaScript transform node and bind that single value.

Apollo Find People runs on Freckle-provided Apollo access; there is no customer Apollo connection or `credentialId` to ask the user about.

## Handoff through Push to Dataset

Read [push-to-dataset.md](push-to-dataset.md), then bind the complete array directly:

```yaml
nodes:
  findPeople:
    uses: apolloFindPeople@<inspected-version>
    config: {}
    with:
      request: $nodes.buildApolloRequest.value
  pushPeople:
    uses: pushToDataset@<inspected-version>
    config:
      datasetId: <target-dataset-id>
    with:
      values: $nodes.findPeople.people
outputs:
  pushReceipt:
    type:
      fields:
        datasetId: string
        pushedCount: number
    from: $nodes.pushPeople.result
```

Push the person objects unchanged. Use the inspected `people` item contract to understand the available identity, contact, role, location, profile, organization, account, phone, employment-history, and intent fields. Catalog the fields required by the described downstream Workflow. When no downstream use is known yet, catalog the useful identity/contact/company fields such as `id`, `full_name`, `first_name`, `last_name`, `email`, `email_status`, `title`, `seniority`, `linkedin_url`, organization name/domain, and location.

**Completion** — every box checked:

- [ ] Apollo's role is explicitly evidence or handoff.
- [ ] An unspecified result count was asked about and resolved.
- [ ] Apollo's per-billable-person price and `request.numResults` maximum are in the Credit Cost Summary.
- [ ] The full node contract was inspected and its version pinned.
- [ ] A handoff has, in the plan: a same-Workbook Push destination, the complete-person binding, a field catalog, the Push receipt output, and any user-described downstream connections.
