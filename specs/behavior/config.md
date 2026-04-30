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
- plugin implementation.
- plugin loading internals.
- dependency discovery algorithms.
- caching.
- performance requirements.

This specification defines configuration semantics that the implementation MUST honor, but it does not require any particular implementation strategy.

## Dictionary

- `configuration file` - a TOML file named `depmesh.toml` that configures relations, dependency discovery rules, and optional plugins for one project.
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
- `plugins` - list of plugin Python import paths.
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
reverse_id = "tested_by"
reverse_description = "Artifacts tested by the input artifacts."

[[rules]]
relation = "tests"
artifacts = [
  { type = "glob", pattern = "./depmesh/{module}.py" },
]
dependencies = [
  { type = "path", path = "./depmesh/tests/test_{module}.py" },
]
```

## Plugins

The `plugins` field MAY be omitted.

If present, `plugins` MUST be an array of Python import path strings.

A plugin declaration MUST NOT have any interpretation other than a Python import path.

Plugin declaration example:

```toml
plugins = ["depmesh_plugins.python"]
```

Plugin import paths MUST be non-empty strings.

Plugin import paths MUST be unique within one configuration file.

Plugins MUST be interpreted in configuration order.

## Relations

The `relations` field MUST contain the relation definitions referenced by rules.

At least one relation MUST be configured.

Each relation definition MUST include:

- `id` - relation id used for forward dependencies.
- `reverse_id` - reverse relation id used for reverse dependencies.

Each relation definition MAY include:

- `description` - relation description.
- `reverse_description` - reverse relation description.

Relation ids and reverse relation ids MUST be non-empty strings.

Relation ids and reverse relation ids MUST be unique across all configured relations.

Relation ids and reverse relation ids MUST contain only:

- lowercase ASCII letters.
- ASCII digits.
- `_`.

If `description` is omitted, its value MUST be `None`.

If `reverse_description` is omitted, its value MUST be `None`.

The following relation fields MUST be non-empty strings when present:

- relation descriptions.
- reverse relation descriptions.

## Rules

The `rules` field MAY be omitted.

If present, `rules` MUST be an array of rule definitions.

Each rule definition MUST include:

- `artifacts` - artifact matchers.
- `relation` - forward relation id for dependencies produced by the rule.
- `dependencies` - dependency expressions evaluated for matched artifacts.

The `relation` field MUST reference a configured relation `id`.

The `relation` field MUST NOT reference a `reverse_id`.

The `dependencies` field MUST contain at least one dependency expression.

Rules MUST be evaluated as forward dependency rules.

Reverse dependency queries MUST be derived from the same configured relations and rules.

If multiple rules match the same artifact, all matching rules MUST contribute dependencies.

If multiple dependency expressions in matching rules produce the same dependency for the same relation, the dependency MUST be treated as a duplicate.

## Artifact matchers

The `artifacts` field MUST be an array of artifact matcher tables.

The `artifacts` field MUST contain at least one artifact matcher.

A rule MUST match an input artifact when at least one matcher in its `artifacts` field matches the artifact.

Each artifact matcher MUST include:

- `type` - artifact matcher type.

Supported artifact matcher types MUST include:

- `path` - fixed artifact path.
- `glob` - glob pattern.
- `regex` - regular expression.

Future artifact matcher types MAY be added in later schema versions.

Every template variable referenced by a rule's dependency expressions MUST be provided by every artifact matcher that can match the rule.

Configuration loading MUST fail if a dependency expression references a template variable that is not provided by every artifact matcher that can match the rule.

Relative paths and glob patterns MUST be resolved against the configuration root.

Absolute paths MAY be used, but project configurations SHOULD prefer relative paths.

For matching, file paths inside the configuration root SHOULD be normalized to a relative path that starts with `./` and uses `/` as the separator.

### Path matcher

A `path` matcher MUST match exactly one artifact path after path normalization.

A `path` matcher MUST include:

- `type = "path"`.
- `path` - fixed artifact path.

Example:

```toml
artifacts = [
  { type = "path", path = "./depmesh/domain/entities.py" },
]
```

A `path` matcher MUST NOT define captures.

### Glob matcher

A `glob` matcher MUST use `/` as the path separator.

A `glob` matcher MUST include:

- `type = "glob"`.
- `pattern` - glob pattern.

`*` MUST match zero or more characters inside one path segment.

`**` MUST match zero or more path segments.

`?` MUST match one character inside one path segment.

A glob matcher MAY define captures with `{name}`.

A glob capture name MUST contain only ASCII letters, ASCII digits, and `_`, and MUST NOT start with a digit.

`{name}` MUST match zero or more characters inside one path segment.

If a glob matcher defines captures, every successful match MUST make those captures available to dependency expressions in the same rule.

Example:

```toml
artifacts = [
  { type = "glob", pattern = "./depmesh/{module}.py" },
  { type = "glob", pattern = "./depmesh/{module}/__init__.py" },
]
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
artifacts = [
  { type = "regex", pattern = "^\\./depmesh/(?P<module>[a-z_]+)\\.py$" },
]
```

The supported regular expression dialect is implementation-defined for schema version `1`, but the implementation MUST document any syntax that differs from Python regular expressions before relying on it in examples or generated configuration.

## Dependency expressions

A dependency expression MUST be a typed table.

Each dependency expression MUST include:

- `type` - dependency expression type.

Supported dependency expression types MUST include:

- `path` - fixed dependency path.
- `glob` - glob pattern that expands to dependency paths.
- `regex` - regular expression that finds dependency paths in the project.
- `command` - shell command that prints dependency identifiers.

Future dependency expression types MAY be added in later schema versions.

Dependency expressions MAY use template variables.

A template variable MUST use `{name}` syntax and MUST reference a capture produced by the rule's artifact matchers.

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
dependencies = [
  { type = "path", path = "./depmesh/tests/test_{module}.py" },
]
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
dependencies = [
  { type = "glob", pattern = "./specs/**/*{module}*.md" },
]
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
dependencies = [
  { type = "regex", pattern = "^\\./specs/.+{module}.+\\.md$" },
]
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
dependencies = [
  { type = "command", command = "python -m tools.find_imports {module}" },
]
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
- duplicate relation ids or reverse relation ids.
- rules that reference unknown relation ids.
- malformed artifact matchers.
- malformed dependency expressions.
- dependency expressions that reference unknown template variables.
- unknown top-level fields.
