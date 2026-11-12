# Credit Cost and Forecast Summaries

This is the single source of truth for user-facing credit messaging. Apply it when planning or running a Workflow.

## Calculate the maximum

Use current catalog data internally. `creditCostModel` tells you whether a node's `creditCost` is charged at most once for a billable execution or once per billable result; these are implementation details, not user-facing terms.

For one input row:

1. Add each at-most-once node's `creditCost` once, including every provider that could run across fallback branches.
2. For each per-result node with a configured result cap, add `creditCost × cap`. Without a cap, keep `creditCost × billable results` as a formula and say a finite maximum is unavailable until the cap is known.
3. When the Dataset size is fixed, multiply the complete per-row maximum by the row count. If any component remains uncapped, show its full-workbook formula instead of a finite total.

For a saved Workflow reused unchanged:

1. Run `workflow saved inspect`, capture the quoted revision id and `costEstimate`, and use `estimatedStaticCreditCost` as the at-most-once subtotal.
2. When `dynamicNodeCosts` is non-empty, export that exact revision before resolving caps:

   ```bash
   freckle workflow saved get-draft <workflowId> --revision-id <revisionId> --out <absolute-path>/workflow.yaml
   ```

3. Trace each result-priced node's cap through the exported draft's config, constants, and fixed request construction. Apply its unit price only when the cap is fixed and verified. When the cap is input-dependent or cannot be verified, keep `creditCost × billable results` as an uncapped formula and state that a finite maximum is unavailable.

Identify the quoted revision in the summary. The latest revision is mutable and inspect-before-admission is not atomic, so say the maximum or formula can change if a new revision or catalog price lands before the run.

## Plan: Credit Cost Summary

In the approved plan, omit credits from the result-fields table. Follow it with this exact heading:

**Credit Cost Summary**

Report:

- maximum credits per row;
- maximum credits for the whole Workbook only when the Dataset size and every result cap are fixed;
- any uncapped per-result formula that prevents a finite maximum;
- that averages and forecasts become eligible after the first 10 input rows’ runs reach terminal states and require authoritative actual charged credits; and
- that the current CLI cannot retrieve actual charged credits, so the later **Credit Forecast Summary** reports that limitation instead of an observed average or forecast and repeats the planning maximum. Once an authoritative product response supplies charged credits, use the same 10-row sample for the observed forecast.

Label every user-facing credit amount **credits**. Describe per-result formulas in plain language when needed, without exposing the catalog's billing-model labels. State that the maximum is an upper bound at current prices, not a range or a guaranteed charge; a row may use 0 credits. Authenticated dollar equivalents follow the rules below.

## After the sample: Credit Forecast Summary

After the first 10 input rows’ runs reach terminal states, return this heading even when a trustworthy forecast is unavailable:

**Credit Forecast Summary**

An observed forecast requires actual charged credits for each of those 10 rows from an authoritative product response. When available, report:

- sample size and actual sample credits;
- average credits per row (`sample credits ÷ 10`); and
- for a fixed Dataset, forecast total credits (`average credits per row × row count`).

Label this as a sample-based forecast, not a guarantee. Use authoritative actual charged credits as the sole observed-spend source; outputs, selected branches, catalog maximums, and a zero lower bound remain planning context.

Under the current CLI limitation, the **Credit Forecast Summary** states that the average and forecast are unavailable, then repeats the planning maximum for context and labels it as a maximum rather than an observed forecast.

## Dollar equivalents

Add dollars only when an authenticated product response supplies the user's plan-specific credit-to-dollar rate. Then show dollars per row beside credits, and show a total-workbook dollar figure only for a fixed Dataset size. Name the plan/rate source and calculation.

The current CLI does not expose the user's plan-specific rate. State that dollar equivalents are unavailable from the current CLI; never infer a rate from plan names, public pricing, or generic assumptions.

**Completion:** the plan has one **Credit Cost Summary** based on a verified maximum or an explicit uncapped formula; after the first 10 input rows’ runs reach terminal states, one **Credit Forecast Summary** reports actual charged credits or the explicit current-CLI limitation; credit-cost quantities use the label “credits,” while authenticated plan-rate dollar equivalents remain allowed; no per-data-point credit allocation or unsupported range appears; and total dollars appear only for a fixed Dataset size.
