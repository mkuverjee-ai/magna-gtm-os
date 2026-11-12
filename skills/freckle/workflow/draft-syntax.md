# Workflow Draft YAML Syntax

YAML is the authoring representation for one Workflow Draft: parse it into data, then validate and compile it through the API.

## Top-Level Shape

```yaml
kind: workflow_draft
schemaVersion: 1
workflowId: example-workflow
types: {}
inputs: {}
nodes: {}
outputs: {}
```

- `kind` must be exactly `workflow_draft`.
- `schemaVersion` must be numeric `1`; the string `"1"` is invalid.
- `workflowId` is a saved-workflow slug: lowercase letters or digits separated by single hyphens.
- `types` is optional and contains workflow-scoped Named Types.
- `inputs`, `nodes`, and `outputs` are required maps. Empty maps are allowed.
- Unknown top-level properties are rejected.
- Optional sections are not defaulted during schema decode: omitted means omitted, and present empty maps stay present empty maps.

## Identifiers

Workflow Draft Identifiers are used for type ids, input ids, node ids, output ids, port ids, case ids, and object field ids.

- Pattern: `[A-Za-z_][A-Za-z0-9_]*`
- Invalid reserved ids: `__proto__`, `constructor`, `prototype`
- Quoting in YAML does not allow whitespace, dots, or other invalid characters.
- Named Type ids cannot be type keywords: `string`, `number`, `boolean`, `unknown`, `null`, or `nullable`.

`workflowId` is different: it uses the saved-workflow slug pattern `[a-z0-9]+(-[a-z0-9]+)*`.

## Workflow Inputs

Each entry under `inputs` maps an input id directly to type shorthand — the value is the shorthand itself, not an object with a `type` key:

```yaml
inputs:
  email: string
  domain: string?
```

## Nodes

Each entry under `nodes` declares one Workflow Node:

```yaml
nodes:
  findLinkedIn:
    uses: aviatoFindLinkedIn@1.0.0
    config: {}
    with:
      email: $inputs.email
    cases:
      found:
        to:
          - nextNode
```

- `title` is allowed on every node. When present, it must be a non-blank string of at most 60 characters that names what THIS node instance does in the workflow, not the node definition in general.
- `description` is allowed on every node. When present, it must be a non-blank string of at most 200 characters explaining that instance's authored intent.
- `uses` is required and pinned: `<definitionKey>@<major>.<minor>.<patch>`.
- `config` is strict JSON-compatible node configuration. If the contract has a config schema, missing `config` is rejected; if the contract has no config schema, authored `config` is rejected.
- `with` maps node input port ids to Workflow Draft Endpoint References.
- `nodes.<nodeId>.cases` maps branch case ids to `{ to: [<targetNodeId>, ...] }`.

Node config values must be `null`, strings, booleans, finite numbers, dense arrays, or plain objects with own enumerable string data properties. Config object keys belong to the node definition and do not have to be Workflow Draft Identifiers.

## Endpoint References

Workflow Draft Endpoint References name sources only:

- `$inputs.<inputId>`
- `$nodes.<nodeId>.<outputPortId>`

They are whole-endpoint references. They do not support field paths, expressions, literals, projections, or references to workflow outputs.

The containing position determines the consumer:

- `nodes.<nodeId>.with.<portId>` binds a source to a node input port.
- `outputs.<outputId>.from` declares the source used to materialize a workflow output.

To inject constants, normalize fields, or project a subset of an object, add a transform node that emits the desired value and bind to that output port.

## Workflow Outputs

Every Workflow Output declares a `type` and exactly one `from` source.

Use a simple string `from` when one Workflow Input or Node Output Port always provides the output:

```yaml
outputs:
  profile:
    type: LeadProfile
    from: $nodes.scoreLead.profile
  echoedEmail:
    type: string
    from: $inputs.email
```

Use guarded `from.oneOf` when the output genuinely comes from different branch-specific nodes:

```yaml
outputs:
  selectedProfile:
    type: LeadProfile
    from:
      oneOf:
        - when:
            node: lookup
            case: found
          source: $nodes.formatFound.value
        - when:
            node: lookup
            case: not_found
          source: $nodes.formatFallback.value
```

All `oneOf` entries for one Workflow Output must use the same guard Workflow Node. Each entry pairs one guard Branch Case with one source Node Output Port. Guarded sources cannot reference Workflow Inputs or outputs from the guard node itself; the source node must be downstream of the named Branch Case through Activation Ancestry. A single-entry `oneOf` is valid.

Runtime selection uses the guard node's exact Selected Branch Case. It is not first source, first present value, or first non-missing source. Non-selected guarded sources are ignored. If no guard case matches, required outputs fail and Optional outputs are omitted. Node failures still fail the Workflow Run regardless of output optionality.

## Branch Cases

Branch cases activate downstream nodes from a source node:

```yaml
nodes:
  lookup:
    cases:
      found:
        to:
          - usePayload
      not_found:
        to:
          - fallback
```

Omit case entries when no path is needed. The full path is `nodes.<nodeId>.cases.<caseId>.to`, and `to` must be a non-empty list of target node ids. Target arrays cannot repeat the same target node id. Compiler validation rejects self-targeting activations, unknown target nodes, duplicate upstream activations for the same target node, and cases not declared by the source node's contract.

Data bindings and Branch Cases are separate. A `with` entry says where a node input value comes from; a Branch Case says whether the target node is eligible to run. When a required node input consumes data that is only produced on one branch, bind the data with `with` and route that same Branch Case to the consumer node. If several nodes consume data from the same branch, use a fan-out Branch Case to activate all of them.

## Type Shorthand

The draft uses compact Workflow Draft Type Shorthand, not canonical Workflow Type objects.

| Shorthand | Meaning |
| --- | --- |
| `string` | Present string value |
| `number` | Present finite number value |
| `boolean` | Present boolean value |
| `unknown` | Opaque JSON-compatible value, not arbitrary JavaScript |
| `"null"` | Null Literal: present value must be `null`; quote it in YAML |
| `Company` | Type Reference to `types.Company` |
| `string[]` | Array whose elements are strings |
| `Company[]` | Array whose elements are resolved `Company` values |
| `nullable<string>` | Present value may be a string or `null` |
| `nullable<Company>` | Present value may be a resolved `Company` value or `null` |
| `string?` | Optional string in an optional context; the value may be absent |
| `nullable<string>?` | Optional boundary or field whose present value may be string or `null` |
| `null?` | Optional boundary or field whose present value, if present, must be `null` |
| `{ fields: ... }` | Inline object type with field ids mapped to type shorthand |

Important restrictions:

- A trailing `?` is allowed only in optional contexts: workflow inputs, workflow outputs, object fields, and node-owned type shorthand positions that opt into optionality. It is not allowed at the root of a `types.<typeId>` declaration.
- Array and nullable wrappers are shallow. Their inner value must be a scalar or a Named Type reference. Use Named Types for object arrays, nullable objects, or reusable nested composition.
- `null[]` and `nullable<null>` are invalid.
- `string[][]`, `nullable<string[]>`, and nested wrapper forms are invalid.
- Inline object shorthand is valid at every type-bearing draft position and may nest through field values. It cannot itself be wrapped in `[]` or `nullable<>`; declare a Named Type and reference it instead.
- Inline object shorthand declares an exact object: undeclared properties are rejected. Typed `additionalProperties` may appear in compiler-derived Node Contract types, but it is not authorable as Workflow Draft Type Shorthand.

Optional, Nullable, and the Null Literal mean different things:

- Optional means the value may be absent entirely.
- Nullable means the value is present and its type permits `null`.
- The Null Literal `"null"` permits exactly the present value `null`.

## Validation

```bash
freckle workflow draft validate --file workflow.yaml
```

Validation performs:

1. Type shorthand lowering and Named Type resolution.
2. Draft graph validation for endpoint references, Workflow Output Sources, and branch activations.
3. Node contract compilation, including config decoding, dynamic surfaces, and output-source checks.
4. Compiled workflow assembly and cycle checks.

Exit 0 with no output means valid. Nonzero exit means the draft is invalid; the output is a plain-text message followed by compiler diagnostics. Fix the reported issues and rerun.
