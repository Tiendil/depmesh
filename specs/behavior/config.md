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
- `rule` - a configuration entry that connects matching input artifacts to dependency expressions for one relation.
- `artifact matcher` - one configured pattern that can make a rule apply to an input artifact.
- `dependency expression` - a configured expression that produces dependencies for an artifact matched by a rule.
- `capture` - a named value extracted from an artifact matcher and made available to dependency expressions in the same rule.
- `template variable` - a reference to a capture inside a dependency expression.

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

The configuration file MUST be valid TOML.

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
artifact = { type = "glob", pattern = "./depmesh/{*module}.py" }
dependency = { type = "path", path = "./depmesh/tests/test_{module}.py" }
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

- `artifact` - artifact matcher.
- `relation` - relation id for dependencies produced by the rule.
- `dependency` - dependency expression evaluated for matched artifacts.

The `relation` field MUST reference a configured relation `id`.

Rules MUST be evaluated as single-direction dependency rules.

A rule MUST match an input artifact when its `artifact` matcher matches the artifact.

If multiple rules match the same artifact, all matching rules MUST contribute dependencies.

If dependency expression composition produces the same dependency more than once for the same relation, the dependency MUST be treated as a duplicate.

## Artifact matchers

The `artifact` field MUST be an artifact matcher table.

Each artifact matcher MUST include:

- `type` - artifact matcher type.

Supported artifact matcher types MUST include:

- `paths` - fixed artifact paths.
- `glob` - glob pattern.
- `regex` - regular expression.
- `any` - composition that matches when any child matcher matches.
- `all` - composition that matches when all child matchers match.
- `not` - composition that matches when its child matcher does not match.

Future artifact matcher types MAY be added in later schema versions.

Every template variable referenced by a rule's dependency expression MUST be provided by the rule's artifact matcher.

Configuration loading MUST fail if a dependency expression references a template variable that is not provided by the rule's artifact matcher.

Relative artifact paths and glob patterns MUST be resolved against the configuration root.

Absolute paths MAY be used, but project configurations SHOULD prefer relative paths.

For matching, file paths inside the configuration root SHOULD be normalized to a relative path that starts with `./` and uses `/` as the separator.

### Paths matcher

A `paths` matcher MUST match an artifact when it is equal to one of the configured artifact paths after path normalization.

A `paths` matcher MUST include:

- `type = "paths"`.
- `paths` - array of fixed artifact paths.

The `paths` field MUST contain at least one path.

Example:

```toml
artifact = { type = "paths", paths = [
  "./depmesh/domain/entities.py",
  "./depmesh/domain/__init__.py",
] }
```

A `paths` matcher MUST NOT define captures.

### Glob matcher

A `glob` matcher MUST use `/` as the path separator.

A `glob` matcher MUST include:

- `type = "glob"`.
- `pattern` - glob pattern.

`*` MUST match zero or more characters inside one path segment.

`**` MUST match zero or more path segments.

`?` MUST match one character inside one path segment.

A glob matcher MAY define captures with `{*name}` and `{**name}`.

A glob capture name MUST contain only ASCII letters, ASCII digits, and `_`, and MUST NOT start with a digit.

`{*name}` MUST match zero or more characters inside one path segment and expose the matched text as capture `name`.

`{**name}` MUST match zero or more path segments and expose the matched text as capture `name`.

If a glob matcher defines captures, every successful match MUST make those captures available to dependency expressions in the same rule.

Example:

```toml
artifact = { type = "glob", pattern = "./depmesh/{*module}.py" }
```

### Regex matcher

A `regex` matcher MUST be matched against the normalized artifact identifier.

A `regex` matcher MUST include:

- `type = "regex"`.
- `pattern` - regular expression.

Regex matchers MAY define captures with named capture groups.

Named captures MUST be made available to dependency expressions in the same rule.

Example:

```toml
artifact = { type = "regex", pattern = "^\\./depmesh/(?P<module>[a-z_]+)\\.py$" }
```

The supported regular expression dialect is implementation-defined for schema version `1`, but the implementation MUST document any syntax that differs from Python regular expressions before relying on it in examples or generated configuration.

### Any matcher

An `any` matcher MUST match an artifact when at least one child matcher matches the artifact.

An `any` matcher MUST include:

- `type = "any"`.
- `items` - array of child artifact matcher tables.

The `items` field MUST contain at least one child matcher.

For template validation, an `any` matcher MUST expose only captures that are provided by every child matcher.

Child matchers MUST be evaluated in configuration order.

When more than one child matcher could match an artifact, the captures from the first matching child matcher MUST be used.

Example:

```toml
artifact = { type = "any", items = [
  { type = "glob", pattern = "./depmesh/{*module}.py" },
  { type = "glob", pattern = "./depmesh/{*module}/__init__.py" },
] }
```

### All matcher

An `all` matcher MUST match an artifact only when every child matcher matches the artifact.

An `all` matcher MUST include:

- `type = "all"`.
- `items` - array of child artifact matcher tables.

The `items` field MUST contain at least one child matcher.

For template validation, an `all` matcher MUST expose captures provided by any child matcher.

If multiple child matchers produce the same capture name for one artifact, the matcher MUST NOT expose conflicting capture values to dependency expressions.

Example:

```toml
artifact = { type = "all", items = [
  { type = "glob", pattern = "./depmesh/{*module}.py" },
  { type = "regex", pattern = "^\\./depmesh/(?P<module>[a-z_]+)\\.py$" },
] }
```

### Not matcher

A `not` matcher MUST match an artifact only when its child matcher does not match the artifact.

A `not` matcher MUST include:

- `type = "not"`.
- `item` - one child artifact matcher table.

A `not` matcher MUST NOT expose captures.

For template validation, a `not` matcher MUST expose no captures, even when its child matcher defines captures.

Example:

```toml
artifact = { type = "all", items = [
  { type = "glob", pattern = "./specs/{**path}.md" },
  { type = "not", item = { type = "paths", paths = ["./specs/meta/general.md"] } },
] }
```

## Dependency expressions

A dependency expression MUST be a typed table.

Each dependency expression MUST include:

- `type` - dependency expression type.

Supported dependency expression types MUST include:

- `path` - fixed dependency path.
- `glob` - glob pattern that expands to dependency paths.
- `regex` - regular expression that finds dependency paths in the project.
- `command` - shell command that prints dependency identifiers.
- `union` - composition that produces dependencies from all child expressions.
- `intersection` - composition that produces dependencies produced by every child expression.
- `difference` - composition that produces dependencies from one expression except dependencies produced by another expression.

Future dependency expression types MAY be added in later schema versions.

Dependency expressions MAY use template variables.

A template variable MUST use `{name}` syntax and MUST reference a capture produced by the rule's artifact matcher.

If a dependency expression references an unknown template variable, configuration loading MUST fail.

Template substitution MUST happen before evaluating the dependency expression.

### Path expression

A `path` expression MUST produce at most one dependency.

A `path` expression MUST include:

- `type = "path"`.
- `path` - fixed dependency path.

Relative path expressions MUST be resolved against the configuration root.

If the resolved path does not exist as a file, the expression SHOULD produce a warning and SHOULD NOT produce a dependency.

Example:

```toml
dependency = { type = "path", path = "./depmesh/tests/test_{module}.py" }
```

### Glob expression

A `glob` expression MUST produce all filesystem paths matched by the pattern after template substitution.

A `glob` expression MUST include:

- `type = "glob"`.
- `pattern` - glob pattern.

Relative glob expressions MUST be resolved against the configuration root.

Glob expression results MUST be deterministic for the same filesystem state.

Example:

```toml
dependency = { type = "glob", pattern = "./specs/**/*{module}*.md" }
```

### Regex expression

A `regex` expression MUST search normalized project paths and produce paths that match the regular expression after template substitution.

A `regex` expression MUST include:

- `type = "regex"`.
- `pattern` - regular expression.

Regex expression results MUST be deterministic for the same filesystem state.

The supported regular expression dialect has the same requirements as regex artifact matchers.

Example:

```toml
dependency = { type = "regex", pattern = "^\\./specs/.+{module}.+\\.md$" }
```

### Command expression

A `command` expression MUST execute after template substitution.

A `command` expression MUST include:

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
dependency = { type = "command", command = "python -m tools.find_imports {module}" }
```

### Union expression

A `union` expression MUST produce all dependencies produced by its child expressions.

A `union` expression MUST include:

- `type = "union"`.
- `items` - array of child dependency expression tables.

The `items` field MUST contain at least one child expression.

Duplicate dependencies produced by child expressions MUST be treated as duplicates.

Example:

```toml
dependency = { type = "union", items = [
  { type = "path", path = "./depmesh/tests/test_{module}.py" },
  { type = "glob", pattern = "./depmesh/tests/{module}/test_*.py" },
] }
```

### Intersection expression

An `intersection` expression MUST produce only dependencies produced by every child expression.

An `intersection` expression MUST include:

- `type = "intersection"`.
- `items` - array of child dependency expression tables.

The `items` field MUST contain at least one child expression.

Example:

```toml
dependency = { type = "intersection", items = [
  { type = "glob", pattern = "./specs/**/*.md" },
  { type = "regex", pattern = "^\\./specs/.+{module}.+\\.md$" },
] }
```

### Difference expression

A `difference` expression MUST produce dependencies produced by its include expression, except dependencies also produced by its exclude expression.

A `difference` expression MUST include:

- `type = "difference"`.
- `include` - child dependency expression table that produces the initial dependency set.
- `exclude` - child dependency expression table that produces dependencies to remove from the initial dependency set.

Duplicate dependencies produced by either child expression MUST be treated as duplicates before the difference is calculated.

Example:

```toml
dependency.type = "difference"
dependency.include = { type = "glob", pattern = "./specs/**/*.md" }
dependency.exclude = { type = "path", path = "./specs/meta/general.md" }
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
- malformed artifact matchers.
- malformed dependency expressions.
- dependency expressions that reference unknown template variables.
- unknown top-level fields.
