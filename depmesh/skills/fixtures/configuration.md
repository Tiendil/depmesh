# `depmesh` Configuration

`depmesh.toml` tells `depmesh` which dependency relations exist in a project and how to discover artifacts for each relation.

The file has two main parts:

- `relations` name the dependency types that can be queried.
- `rules` describe how a queried artifact is matched and where dependencies come from.

A rule has an `input` predicate and an `output` source. When the predicate matches the queried artifact, the source produces dependency artifacts for the rule's relation.

Glob and regex predicates can capture named values from the queried artifact. Output sources can reuse those captures as template variables. Capture names must match exactly: a capture named `module` is referenced as `{module}` in the output.

The configuration file is TOML with schema version `1`.

Minimal file:

```toml
version = 1

[[relations]]
id = "governed_by"
description = "Specifications that apply to the artifact."

[[relations]]
id = "governs"
description = "Artifacts governed by the specification."
```

Top-level fields:

- `version`: optional integer, currently `1`.
- `relations`: optional list of relation definitions.
- `rules`: optional list of dependency discovery rules.

Unknown top-level fields are invalid.

## Relations

Relations define the dependency vocabulary for the project. Each relation id can be listed with `depmesh -p llm relations` and selected with `depmesh -p llm dependencies --relation RELATION_ID`.

```toml
[[relations]]
id = "tests"
description = "Tests that verify the artifact."
```

Fields:

- `id`: required relation id.
- `description`: optional non-empty text.

Relation ids must be unique and contain only lowercase ASCII letters, digits, and underscores.

Descriptions should describe the artifacts returned by the relation and should make the queried artifact role clear when needed.

Use `artifact` as the default term for the queried relation source. When the returned dependencies must be called `artifacts`, choose a more specific source role instead, such as `specification`, `test`, `dictionary`, or `index`:

```toml
[[relations]]
id = "governs"
description = "Artifacts governed by the specification."
```

Relations are directional. Declare a second relation for reverse lookup:

```toml
[[relations]]
id = "imports"
description = "Python files imported by the artifact."

[[relations]]
id = "imported_by"
description = "Python files that import the artifact."
```

## Rules

Rules are the bridge between a queried artifact and the dependency artifacts returned for one relation.

Each rule says: for this relation, when the queried artifact matches this predicate, evaluate this source to produce dependencies.

```toml
[[rules]]
relation = "tests"
input = { type = "glob", pattern = "@/src/{*module}.py" }
output = { type = "files", pattern = "@/tests/test_{module}.py" }
```

Fields:

- `relation`: required relation id declared in `relations`.
- `input`: required artifact predicate.
- `output`: required artifact source.

When the input predicate matches an input artifact, the output source produces dependencies for the configured relation.

## Recommendations

Prefer glob or regex patterns over enumerating individual files when a dependency rule applies to a family of artifacts.

Pattern-based rules are more scalable and more evolution-proof: they continue to cover new files that follow the same project layout without requiring configuration edits.

It is usually better to overspecify dependencies by adding a connection that is not required than to underspecify dependencies by missing a connection that should be reported.

## Paths

Paths in configuration should be stable from the configuration root, which is the directory containing the active `depmesh.toml`.

Project file paths should start with `@/` and use `/`.

Relative paths and patterns may be used in configuration and are resolved against the directory containing `depmesh.toml`.

Dependency output uses canonical root-anchored paths such as `@/src/app.py`.

Examples:

```toml
input = { type = "one_of", artifacts = ["@/README.md"] }
output = { type = "files", pattern = "@/specs/**/*.md" }
```

## Captures And Templates

Captures connect matched artifact paths to generated dependency paths or commands.

Use captures when a dependency path is derived from part of the queried artifact path.

Output sources can reference captures with `{name}`:

```toml
[[rules]]
relation = "tests"
input = { type = "glob", pattern = "@/src/{*module}.py" }
output = { type = "list", artifacts = ["@/tests/test_{module}.py"] }
```

Every template variable used by `output` must be provided by the rule's `input` predicate.

## Predicates

Predicates decide whether a rule applies to the queried artifact. Rule-level predicates live in `input`; source-local predicates can also filter source results.

Choose the narrowest predicate that describes the artifact family for the rule.

### one_of

Matches exactly one of the configured artifact ids.

```toml
input = { type = "one_of", artifacts = [
  "@/README.md",
  "@/pyproject.toml",
] }
```

### glob

Matches an artifact with a glob pattern.

```toml
input = { type = "glob", pattern = "@/src/{*module}.py" }
input = { type = "glob", pattern = "@/packages/{**package_path}/README.md" }
```

`{*name}` captures part of one path segment. `{**name}` captures zero or more path segments.

### regex

Matches the normalized artifact id with a regular expression.

```toml
input = { type = "regex", pattern = "^@/src/(?P<module>[a-z_]+)\\.py$" }
```

Named capture groups are available as output template variables.

### any

Matches when at least one child predicate matches.

```toml
input = { type = "any", items = [
  { type = "glob", pattern = "@/src/{*module}.py" },
  { type = "glob", pattern = "@/src/{*module}/__init__.py" },
] }
```

For template validation, `any` exposes only captures provided by every child predicate.

### all

Matches when every child predicate matches.

```toml
input = { type = "all", items = [
  { type = "glob", pattern = "@/src/{*module}.py" },
  { type = "not", item = { type = "glob", pattern = "@/src/**/__init__.py" } },
] }
```

For template validation, `all` exposes captures provided by any child predicate.

### not

Matches when its child predicate does not match.

```toml
input = { type = "not", item = { type = "glob", pattern = "@/src/**/__init__.py" } }
```

`not` exposes no captures.

## Sources

Sources produce dependency artifacts after a rule predicate matches. Sources may return fixed artifact ids, filesystem paths, command output, or combinations of other sources.

Sources can use template variables from the rule predicate captures.

### list

Produces fixed artifact ids.

```toml
output = { type = "list", artifacts = ["@/README.md", "@/docs/index.md"] }
```

### files

Produces files under the configuration root, optionally filtered by a glob pattern.

```toml
output = { type = "files", pattern = "@/tests/test_{module}.py" }
```

Without `pattern`, it produces all files under the configuration root.

### command

Runs a shell command from the configuration root. The command prints one dependency id per stdout line.

```toml
output = { type = "command", command = "python ./tools/list_imports.py @/src/{module}.py" }
```

Empty stdout lines are ignored. Non-zero exits should produce warnings when query processing can continue.

### union

Produces the union of child sources.

```toml
output = { type = "union", items = [
  { type = "files", pattern = "@/tests/test_{module}.py" },
  { type = "files", pattern = "@/tests/{module}/test_*.py" },
] }
```

### intersection

Produces artifacts returned by every child source.

```toml
output = { type = "intersection", items = [
  { type = "files", pattern = "@/specs/**/*.md" },
  {
    type = "filter",
    source = { type = "files", pattern = "@/specs/**/*.md" },
    predicate = { type = "regex", pattern = "^@/specs/.+{module}.+\\.md$" },
  },
] }
```

### difference

Produces artifacts from `include` except artifacts from `exclude`.

```toml
output.type = "difference"
output.include = { type = "files", pattern = "@/specs/**/*.md" }
output.exclude = { type = "list", artifacts = ["@/specs/meta/general.md"] }
```

### filter

Filters a child source with a predicate.

```toml
output = {
  type = "filter",
  source = { type = "files", pattern = "@/specs/**/*.md" },
  predicate = { type = "not", item = { type = "one_of", artifacts = ["@/specs/meta/general.md"] } },
}
```
