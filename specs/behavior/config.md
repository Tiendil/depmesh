# Configuration

## Goal of the document

This document describes the behavior and semantics of the `depmesh.toml` configuration file, including:

- where it is found.
- how it is interpreted.
- how relations are declared.
- how dependency discovery rules are configured.

## Scope

The scope of this specification is limited to configuration file behavior.

The following topics are out of scope:

- CLI invocation.
- output protocols.
- output ordering.
- exit codes.
- project module ownership.
- dependency discovery algorithms.
- caching.
- performance requirements.

This specification defines configuration semantics that the implementation MUST honor, but it does not require any particular implementation strategy.

## Dictionary

- `configuration file` - a TOML file named `depmesh.toml` that configures relations and dependency discovery rules for one project.
- `configuration root` - the directory that contains the active configuration file.
- `rule` - a configuration entry that connects matching input artifacts to output artifact sources for one relation.
- `artifact predicate` - one configured predicate that can make a rule apply to an input artifact or filter source results.
- `artifact source` - a configured source that produces output artifacts.
- `capture` - a named value extracted from an input artifact predicate and made available to output sources in the same rule.
- `template variable` - a reference to a capture inside an artifact source or source-local predicate.

## Configuration file discovery

The canonical configuration file name MUST be `depmesh.toml`.

When the CLI is invoked without `--config`, `depmesh` MUST discover the configuration file by searching from the current working directory toward the filesystem root.

Discovery MUST stop at the first directory that contains `depmesh.toml`.

The directory containing the discovered file MUST be the configuration root.

When `--config PATH` is provided, `depmesh` MUST use that file as the configuration file and MUST NOT perform upward discovery.

If `PATH` is relative, it MUST be resolved relative to the current working directory.

When `--config PATH` is provided, the directory containing the resolved file MUST be the configuration root.

If no configuration file can be found or the configured path cannot be read, configuration loading MUST fail.

Configuration loading MUST be deterministic for the same:

- configuration file content.
- current working directory.
- filesystem state.

## TOML structure

The configuration file MUST be valid TOML 1.1.

The top-level configuration MAY contain these fields:

- `version` - configuration schema version.
- `relations` - list of configured relations.
- `rules` - list of dependency discovery rules.

Unknown top-level fields MUST cause configuration loading to fail.

The initial schema version MUST be `1`.

If `version` is omitted, `depmesh` MUST treat the configuration as schema version `1`.

If `version` is present, it MUST be an integer.

If `version` is not supported, configuration loading MUST fail.

Example:

```toml
version = 1

[[relations]]
id = "tests"
description = "Tests related to the input artifacts."

[[rules]]
relation = "tests"
input = { type = "glob", pattern = "./depmesh/{*module}.py" }
output = { type = "list", artifacts = ["./depmesh/tests/test_{module}.py"] }
```

## Relations

The `relations` field MAY be omitted.

If present, `relations` MUST be an array of relation definitions.

If omitted, `relations` MUST be treated as an empty array.

The `relations` field MUST contain the relation definitions referenced by rules.

Each relation definition MUST include:

- `id` - relation id used to query dependencies produced by rules for this relation.

Each relation definition MAY include:

- `description` - relation description.

Relation ids MUST be non-empty strings.

Relation ids MUST be unique across all configured relations.

Relation ids MUST contain only:

- lowercase ASCII letters.
- ASCII digits.
- `_`.

If `description` is omitted, its value MUST be `None`.

The following relation fields MUST be non-empty strings when present:

- relation descriptions.

Relations are single-directional.

Configurations that need reverse lookups MUST declare a separate relation and separate rules for that direction.

## Rules

The `rules` field MAY be omitted.

If present, `rules` MUST be an array of rule definitions.

Each rule definition MUST include:

- `input` - artifact predicate applied to input artifacts.
- `relation` - relation id for dependencies produced by the rule.
- `output` - artifact source evaluated for matched input artifacts.

The `relation` field MUST reference a configured relation `id`.

Rules MUST be evaluated as single-direction dependency rules.

A rule MUST match an input artifact when its `input` predicate matches the artifact.

If multiple rules match the same artifact, all matching rules MUST contribute dependencies.

If artifact source composition produces the same dependency more than once for the same relation, the dependency MUST be treated as a duplicate.

## Artifact predicates

The `input` field MUST be an artifact predicate table.

Every source-local `predicate` field MUST also be an artifact predicate table.

Each artifact predicate MUST include:

- `type` - artifact predicate type.

Supported artifact predicate types MUST include:

- `one_of` - fixed artifact identifiers.
- `glob` - glob pattern.
- `regex` - regular expression.
- `any` - composition that matches when any child predicate matches.
- `all` - composition that matches when all child predicates match.
- `not` - composition that matches when its child predicate does not match.

Future artifact predicate types MAY be added in later schema versions.

Every template variable referenced by a rule's `output` source MUST be provided by the rule's `input` predicate.

Configuration loading MUST fail if an `output` source references a template variable that is not provided by the rule's `input` predicate.

Relative artifact paths and glob patterns MUST be resolved against the configuration root.

Absolute paths MAY be used, but project configurations SHOULD prefer relative paths.

For matching, file paths inside the configuration root SHOULD be normalized to a relative path that starts with `./` and uses `/` as the separator.

### One-of Predicate

A `one_of` predicate MUST match an artifact when it is equal to one of the configured artifact identifiers after path normalization.

A `one_of` predicate MUST include:

- `type = "one_of"`.
- `artifacts` - array of fixed artifact identifiers.

The `artifacts` field MUST contain at least one artifact identifier.

Example:

```toml
input = { type = "one_of", artifacts = [
  "./depmesh/domain/entities.py",
  "./depmesh/domain/__init__.py",
] }
```

A `one_of` predicate MUST NOT define captures.

### Glob Predicate

A `glob` predicate MUST use `/` as the path separator.

A `glob` predicate MUST include:

- `type = "glob"`.
- `pattern` - glob pattern.

`*` MUST match zero or more characters inside one path segment.

`**` MUST match zero or more path segments.

`?` MUST match one character inside one path segment.

A glob predicate MAY define captures with `{*name}` and `{**name}`.

A glob capture name MUST contain only ASCII letters, ASCII digits, and `_`, and MUST NOT start with a digit.

`{*name}` MUST match zero or more characters inside one path segment and expose the matched text as capture `name`.

`{**name}` MUST match zero or more path segments and expose the matched text as capture `name`.

If a rule's input glob predicate defines captures, every successful match MUST make those captures available to the output source in the same rule.

Example:

```toml
input = { type = "glob", pattern = "./depmesh/{*module}.py" }
```

### Regex Predicate

A `regex` predicate MUST be matched against the normalized artifact identifier.

A `regex` predicate MUST include:

- `type = "regex"`.
- `pattern` - regular expression.

Regex predicates MAY define captures with named capture groups.

Named captures from a rule's input regex predicate MUST be made available to the output source in the same rule.

Example:

```toml
input = { type = "regex", pattern = "^\\./depmesh/(?P<module>[a-z_]+)\\.py$" }
```

The supported regular expression dialect is implementation-defined for schema version `1`, but the implementation MUST document any syntax that differs from Python regular expressions before relying on it in examples or generated configuration.

### Any Predicate

An `any` predicate MUST match an artifact when at least one child predicate matches the artifact.

An `any` predicate MUST include:

- `type = "any"`.
- `items` - array of child artifact predicate tables.

The `items` field MUST contain at least one child predicate.

For template validation, an `any` predicate MUST expose only captures that are provided by every child predicate.

Child predicates MUST be evaluated in configuration order.

When more than one child predicate could match an artifact, the captures from the first matching child predicate MUST be used.

Example:

```toml
input = { type = "any", items = [
  { type = "glob", pattern = "./depmesh/{*module}.py" },
  { type = "glob", pattern = "./depmesh/{*module}/__init__.py" },
] }
```

### All Predicate

An `all` predicate MUST match an artifact only when every child predicate matches the artifact.

An `all` predicate MUST include:

- `type = "all"`.
- `items` - array of child artifact predicate tables.

The `items` field MUST contain at least one child predicate.

For template validation, an `all` predicate MUST expose captures provided by any child predicate.

If multiple child predicates produce the same capture name for one artifact, the predicate MUST NOT expose conflicting capture values to output sources.

Example:

```toml
input = { type = "all", items = [
  { type = "glob", pattern = "./depmesh/{*module}.py" },
  { type = "regex", pattern = "^\\./depmesh/(?P<module>[a-z_]+)\\.py$" },
] }
```

### Not Predicate

A `not` predicate MUST match an artifact only when its child predicate does not match the artifact.

A `not` predicate MUST include:

- `type = "not"`.
- `item` - one child artifact predicate table.

A `not` predicate MUST NOT expose captures.

For template validation, a `not` predicate MUST expose no captures, even when its child predicate defines captures.

Example:

```toml
input = { type = "all", items = [
  { type = "glob", pattern = "./specs/**/*.md" },
  { type = "not", item = { type = "one_of", artifacts = ["./specs/meta/general.md"] } },
] }
```

## Artifact sources

The `output` field MUST be an artifact source table.

Each artifact source MUST include:

- `type` - artifact source type.

Supported artifact source types MUST include:

- `files` - project files, optionally scoped by a glob pattern.
- `command` - shell command that prints dependency identifiers.
- `list` - fixed configured artifact identifiers.
- `union` - composition that produces artifacts from all child sources.
- `intersection` - composition that produces artifacts produced by every child source.
- `difference` - composition that produces artifacts from one source except artifacts produced by another source.
- `filter` - composition that filters artifacts produced by a child source with a predicate.

Future artifact source types MAY be added in later schema versions.

Artifact sources MAY use template variables.

A template variable MUST use `{name}` syntax and MUST reference a capture produced by the rule's input predicate.

If an artifact source references an unknown template variable, configuration loading MUST fail.

Template substitution MUST happen before evaluating the artifact source.

### Files Source

A `files` source MUST produce filesystem paths under the configuration root.

A `files` source MUST include:

- `type = "files"`.

A `files` source MAY include:

- `pattern` - glob pattern that limits produced files.

If `pattern` is omitted, a `files` source MUST produce all files under the configuration root.

Relative file source patterns MUST be resolved against the configuration root.

File source results MUST be deterministic for the same filesystem state.

Example:

```toml
output = { type = "files", pattern = "./depmesh/tests/test_{module}.py" }
```

### List Source

A `list` source MUST produce the configured artifact identifiers after template substitution and path normalization.

A `list` source MUST include:

- `type = "list"`.
- `artifacts` - array of artifact identifiers.

The `artifacts` field MUST contain at least one artifact identifier.

Example:

```toml
output = { type = "list", artifacts = ["./specs/{module}.md"] }
```

### Command Source

A `command` source MUST execute after template substitution.

A `command` source MUST include:

- `type = "command"`.
- `command` - shell command.

The command MUST be executed with the configuration root as the working directory.

The command MUST write dependency identifiers to stdout, one dependency identifier per line.

Empty stdout lines MUST be ignored.

Whitespace around each stdout line SHOULD be trimmed.

The command's stderr output SHOULD be treated as diagnostics and MAY be exposed as warnings.

If the command exits with a non-zero status, dependency query processing SHOULD produce a warning and SHOULD continue when possible.

Example:

```toml
output = { type = "command", command = "python -m tools.find_imports {module}" }
```

### Union Source

A `union` source MUST produce all artifacts produced by its child sources.

A `union` source MUST include:

- `type = "union"`.
- `items` - array of child artifact source tables.

The `items` field MUST contain at least one child source.

Duplicate artifacts produced by child sources MUST be treated as duplicates.

Example:

```toml
output = { type = "union", items = [
  { type = "list", artifacts = ["./depmesh/tests/test_{module}.py"] },
  { type = "files", pattern = "./depmesh/tests/{module}/test_*.py" },
] }
```

### Intersection Source

An `intersection` source MUST produce only artifacts produced by every child source.

An `intersection` source MUST include:

- `type = "intersection"`.
- `items` - array of child artifact source tables.

The `items` field MUST contain at least one child source.

Example:

```toml
output = { type = "intersection", items = [
  { type = "files", pattern = "./specs/**/*.md" },
  {
    type = "filter",
    source = { type = "files", pattern = "./specs/**/*.md" },
    predicate = { type = "regex", pattern = "^\\./specs/.+{module}.+\\.md$" },
  },
] }
```

### Difference Source

A `difference` source MUST produce artifacts produced by its include source, except artifacts also produced by its exclude source.

A `difference` source MUST include:

- `type = "difference"`.
- `include` - child artifact source table that produces the initial artifact set.
- `exclude` - child artifact source table that produces artifacts to remove from the initial artifact set.

Duplicate artifacts produced by either child source MUST be treated as duplicates before the difference is calculated.

Example:

```toml
output.type = "difference"
output.include = { type = "command", command = "python -m tools.list_related_specs {module}" }
output.exclude = { type = "list", artifacts = ["./specs/meta/general.md"] }
```

### Filter Source

A `filter` source MUST produce only artifacts from its child source that match its predicate.

A `filter` source MUST include:

- `type = "filter"`.
- `source` - child artifact source table that produces candidate artifacts.
- `predicate` - artifact predicate table used to filter candidate artifacts.

Example:

```toml
output = {
  type = "filter",
  source = { type = "files", pattern = "./specs/**/*.md" },
  predicate = { type = "not", item = { type = "one_of", artifacts = ["./specs/meta/general.md"] } },
}
```

## Path normalization

Configuration-relative file paths SHOULD be written with a leading `./`.

Configuration-relative file paths MUST NOT escape the configuration root unless the field explicitly uses an absolute path.

Path normalization MUST remove redundant `.` path segments.

Path normalization MUST preserve meaningful case on case-sensitive filesystems.

## Invalid configuration

Configuration loading MUST fail for:

- invalid TOML.
- unsupported schema version.
- missing required relation fields.
- duplicate relation ids.
- rules that reference unknown relation ids.
- malformed artifact predicates.
- malformed artifact sources.
- output sources that reference unknown template variables.
- unknown top-level fields.
