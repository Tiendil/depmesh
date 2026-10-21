# Configuration

## Goal of the document

This document describes Depmesh configuration, relations, and discovery rules.

## Scope

Configuration-file behavior; the following are out of scope:

- CLI invocation and output.
- ordering and exits.
- module ownership.
- discovery algorithms.
- caching/performance.

Requirements govern semantics without prescribing implementation strategy.

## Dictionary

- `configuration file` — project relations/rules in TOML, canonically `depmesh.toml`.
- `configuration root` — active file's containing directory.
- `rule` — connects matching inputs to output sources for one relation.
- `artifact predicate` — matches rule inputs or filters source results.
- `artifact source` — produces output artifacts.
- `capture` — named input-predicate value available to the same rule's outputs.
- `template variable` — capture reference in a source or source-local predicate.

## Configuration file discovery

Depmesh MUST follow the contract in `specs/behavior/config.md` in `llm-tool-cli`, with default filename `depmesh.toml`, for:

- discovery.
- resolution.
- loading.
- initialization.

Configuration commands MUST select and validate Depmesh configuration using invocation cwd and optional `--config` under that contract.
The selected file's parent MUST be configuration root; configuration failures MUST preserve the contract's diagnostic information.

## Active configuration

Configuration-dependent commands MUST validate the selected configuration before performing their requested work.
The selected configuration file and configuration root MUST remain consistent through execution and output.
Project-independent commands MUST NOT require or load workspace configuration.

## TOML structure

Top-level fields MAY be `version`, `relations`, and `rules`; unknown fields MUST fail.
The supported schema version and omitted-value default MUST be `1`.
Version values and diagnostics MUST follow the Version contract in `specs/behavior/config.md` in `llm-tool-cli`; non-integer or unsupported versions MUST fail.

```toml
version = 1

[[relations]]
id = "tests"
description = "Tests that verify the artifact."

[[rules]]
relation = "tests"
input = { type = "glob", pattern = "@/depmesh/{*module}.py" }
output = { type = "list", artifacts = ["@/depmesh/tests/test_{module}.py"] }
```

## Relations

Optional `relations` MUST be an array, defaulting empty, containing every relation referenced by rules.
Each entry MUST have a unique nonempty string `id` using only lowercase ASCII letters, ASCII digits, and `_`.
Optional `description` MUST be a nonempty string when present and default to `None`.
Relations are directional; reverse lookups MUST have separate relations/rules.

### Relation descriptions

Descriptions SHOULD explain returned right-side artifacts, not discovery mechanisms, and clarify the queried source's role.
The source SHOULD default to `artifact`; when outputs are called artifacts, it SHOULD instead use a specific domain role.
Descriptions SHOULD use roles such as:

- specification.
- test.
- source module.
- dictionary.
- index.
- artifact.

Reverse descriptions SHOULD be independently written.

**Example:** `governed_by`: “Specifications that apply to the artifact”; `governs`: “Artifacts governed by the specification.”
“Artifacts governed by the artifact” hides the queried role.

## Rules

Optional `rules` MUST be an array.
Each rule MUST contain `input` predicate, configured `relation` id, and `output` source.
Evaluation MUST be directional: input matches activate the rule and every matching rule MUST contribute.
Repeated outputs for the same relation MUST be treated as duplicates.

## Artifact predicates

Rule `input` and source-local `predicate` MUST be tables with `type`.
Nested predicates MUST also be tables; `items` MUST be arrays of child predicates and `artifacts` arrays of identifiers.
The following types MUST be supported; later schema versions MAY add types.
Output template variables MUST be provided by input captures; unknown references MUST fail loading.
Paths/patterns MUST follow Path interpretation below.

### One-of Predicate

`type = "one_of"` MUST require nonempty `artifacts`.
It MUST compare identifiers after normalization and MUST NOT define captures.

### Glob Predicate

`type = "glob"` MUST require `pattern` and follow the Glob patterns contract in `specs/behavior/paths.md` in `llm-tool-cli`.
Invalid pattern project paths MUST be non-matches; other pattern-preparation failures MUST propagate.
Successful input captures MUST become available to the rule's output.
**Example:** `@/depmesh/{*module}.py` captures the module name.

### Regex Predicate

`type = "regex"` MUST require `pattern` and match normalized identifiers.
Named groups MAY capture values; input captures MUST become available to output.
Schema-1 regex dialect is implementation-defined, but differences from Python regex MUST be documented before examples/generated configuration rely on them.

```toml
input = { type = "regex", pattern = "^@/depmesh/(?P<module>[a-z_]+)\\.py$" }
```

### Any Predicate

`type = "any"` MUST require nonempty child `items` and match when any child matches.
Children MUST be evaluated in configuration order, using the first matching child's captures.
Template validation MUST expose only names provided by every child.

```toml
input = { type = "any", items = [
  { type = "glob", pattern = "@/depmesh/{*module}.py" },
  { type = "glob", pattern = "@/depmesh/{*module}/__init__.py" },
] }
```

### All Predicate

`type = "all"` MUST require nonempty child `items` and match only when all match.
Template validation MUST expose names provided by any child.
Duplicate names MUST NOT expose conflicting values to outputs.

### Not Predicate

`type = "not"` MUST require one child `item` and match only its non-match.
It MUST expose no captures, including during template validation.

## Artifact sources

Rule `output` MUST be a table with `type`.
Nested sources MUST also be tables; `items` MUST be arrays of child sources and `artifacts` arrays of identifiers.
The following types MUST be supported; later schema versions MAY add types.
Sources MAY use `{name}` templates, which MUST reference input captures or fail loading.
Substitution MUST precede evaluation.

### Files Source

`type = "files"` MUST enumerate existing regular files under configuration root under the File enumeration contract in `specs/behavior/paths.md` in `llm-tool-cli`.
Optional `pattern` MUST limit matches; omission MUST select all files.
Pattern captures MUST constrain matching without binding other sources.
Invalid paths or glob syntax MUST produce an invalid-pattern warning and empty result; other enumeration failures MUST propagate.

```toml
output = { type = "files", pattern = "@/depmesh/tests/test_{module}.py" }
```

### List Source

`type = "list"` MUST require nonempty `artifacts`, producing them after template substitution/normalization.

### Command Source

`type = "command"` MUST require shell `command` and execute after substitution in configuration root.
Stdout MUST contain one dependency id per line; empty lines MUST be ignored and surrounding whitespace SHOULD be trimmed.
Stderr SHOULD be diagnostics and MAY become warnings.
Non-zero exits SHOULD warn and continue when possible.

```toml
output = { type = "command", command = "python -m tools.find_imports {module}" }
```

### Union Source

`type = "union"` MUST require nonempty child `items`, produce all their artifacts, and treat repeated artifacts as duplicates.

```toml
output = { type = "union", items = [
  { type = "list", artifacts = ["@/depmesh/tests/test_{module}.py"] },
  { type = "files", pattern = "@/depmesh/tests/{module}/test_*.py" },
] }
```

### Intersection Source

`type = "intersection"` MUST require nonempty child `items` and produce only artifacts present in every child result.

### Difference Source

`type = "difference"` MUST require child `include`/`exclude` sources.
It MUST remove exclude artifacts from include artifacts, treating duplicates in each child as duplicates before subtraction.

```toml
output.type = "difference"
output.include = { type = "command", command = "python -m tools.list_related_specs {module}" }
output.exclude = { type = "list", artifacts = ["@/specs/meta/general.md"] }
```

### Filter Source

`type = "filter"` MUST require child `source` and `predicate` tables and return only matching source artifacts.

```toml
output.type = "filter"
output.source = { type = "files", pattern = "@/specs/**/*.md" }
output.predicate = { type = "not", item = { type = "one_of", artifacts = ["@/specs/meta/general.md"] } }
```

## Path interpretation

Configured paths/globs and produced ids MUST follow `specs/behavior/paths.md` in `llm-tool-cli`, based at configuration root, after template substitution.
Predicates, lists, and commands MAY refer to missing targets.
Configurations SHOULD prefer canonical root-anchored paths except when demonstrating other input forms.

## Invalid configuration

Loading MUST reject:

- unsupported versions.
- missing required relation fields.
- duplicate relation ids.
- unknown rule relation ids.
- malformed predicates/sources.
- unknown output variables.
- unknown top-level fields.

## Compatibility rules

Compatibility SHOULD preserve:

- filename.
- version semantics.
- top-level/nested field names.
- predicate/source semantics.
- capture/template meanings.

New optional fields, versions, and predicate/source types MAY be compatible additions.
Breaking changes MUST be specified before implementation.
