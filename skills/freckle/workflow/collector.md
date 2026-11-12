# The Collector

A collector is one `code` node that converges multiple branches back into a single flow: it takes each branch's output as an optional input and emits one merged, typed value. After the collector, every downstream node binds to one source.

It is the cure for **node bloat**. In the draft, bloat looks like:

- the same `uses` key declared several times, differing only in which upstream branch feeds it — duplicated downstream chains per branch;
- several `outputs` entries that each pull `from: $nodes.<differentBranchNode>.<port>` where the user asked for one result;
- nodes whose output ports appear in no other node's `with` and in no `outputs.*.from` — dead-end chains that never rejoin.

When you find yourself about to copy a node per branch, stop and add one collector instead.

Two situations call for one:

- **Fan-in of unrelated enrichments** — independent enrichments over different data (company facts, person profile, tech stack) that a downstream node needs together (a `researchAgent` scoring step, a formatter, the Workflow Output). Run them in parallel — each binds its own upstream data — and merge them into one typed object.
- **Waterfall convergence** — fallback providers that produce the same logical value (see [waterfall.md](waterfall.md)) converge before downstream enrichment.

## Wiring

A node accepts at most one incoming activation (`duplicate_activation_target` diagnostic), so you cannot converge branches by pointing several `cases` at the collector. Converge through data bindings instead:

- Give the collector **no incoming activation** — no upstream `cases` entry targets it. Its activation gate is open; it is gated only by its data bindings.
- Declare branch-specific inputs optional in config, using the `?` type-shorthand suffix; bind them in `with` to each branch's output port:

  ```yaml
  collect:
    title: Collect profile
    description: Merge the branch lookups into one profile, preferring the primary provider.
    uses: code@<version-from-catalog>
    config:
      code: 'return input.primary ?? input.fallback ?? null'
      inputs:
        - { portId: primary, type: 'Profile?' }
        - { portId: fallback, type: 'Profile?' }
      outputType: 'nullable<Profile>'
    with:
      primary: $nodes.apolloLookup.profile
      fallback: $nodes.pdlLookup.profile
  ```

- Inside the sandbox, code reads declared ports off the frozen `input` object — `input.<portId>`, singular, the only namespace available there. `$inputs.<inputId>` belongs to draft YAML alone and never appears inside `code`.
- The scheduler waits for each bound source to reach a terminal outcome, then includes values from completed sources and omits inputs whose source is Not Selected. A source that always runs can bind to a required (non-`?`) input.
- When the collector produces the final result shape, expose its output port (`value`) as the Workflow Output.

## Re-gating downstream

Converge at the **earliest shared value, in the shape the next shared consumer needs** — not at the end of the Workflow, and not in the final output shape. When several branches each produce the same identifier that one downstream provider consumes (a LinkedIn URL feeding a profile-enrichment node), collect the identifier and run **one** provider node after the collector, shared by every branch.

A collector always runs, so it cannot activate the provider only on success by itself. Re-gate with one `switch` on the collector's own string output:

1. Collector emits the identifier with a sentinel word for the miss case (`return input.a ?? input.b ?? 'missing'`, `outputType: string`) — the sentinel keeps the provider's required input type non-nullable.
2. A `switch` node binds `value` to the collector's `value`, with `config: { cases: [missing], defaultCase: found }` — any real identifier falls to `found`, which activates the provider; the provider's required input binds to the collector's `value`.

The `switch` routes on the string directly — one node where a `code`-plus-`if` pair would spend two. Any JS that later consumes the identifier must treat the sentinel as absent (`input.url !== 'missing'`), not test emptiness.

Keep the collector **flat**: emit the bare identifier string. A metadata wrapper (`{ linkedInUrl, linkedInUrlSource }`) costs an extra node — endpoint references cannot reach into object fields, so the wrapper forces a second `code` whose only job is projecting the identifier back out for the `switch` and the provider. Metadata about which branch won belongs in the final formatter: bind the same branch outputs into it as optional inputs and recompute the source there (`input.aviatoUrl ? 'aviato' : input.freckleUrl ? 'freckle' : …`). Emit an object from the collector only when the next shared consumer consumes that whole shape.

On a miss the `switch` selects the sentinel case, the provider is Not Selected, and downstream optional bindings (`?`) carry the run forward. A sentinel at the switch is not where the waterfall's Research Agent backstop fires — the backstop is a rung above the collector, activated from the last structured provider's miss branch, so the sentinel means even research came up empty.

The same shape gates any conditional provider, not just waterfalls: when a provider needs one field of an upstream object (a company domain off a profile), one `code` projects the field with the sentinel, and one `switch` gates the provider on it.
