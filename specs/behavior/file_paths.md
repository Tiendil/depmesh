# File paths

## Goal of the document

This document describes the syntax, semantics, and resolution rules for local project file paths used by `depmesh`.

## Scope

The scope of this specification is limited to file path identifiers that refer to files inside the active project.

The following topics are out of scope:

- dependency relation semantics.
- artifact identifiers that are not local project file paths.
- filesystem discovery algorithms.
- output protocol formatting details, except for canonical file path representation.

## Dictionary

- `project root` - the root directory of the active `depmesh` project.
- `project file path` - a file path identifier that addresses a file inside the project root.
- `root-anchored file path` - a project file path that starts with `@/` and is resolved from the project root.
- `relative file path` - a project file path that does not start with `@/` and is resolved against an explicit base path provided by the context that accepts it.
- `canonical file path` - the normalized root-anchored representation of a project file path.
- `base path` - a project file path or project directory used by a context to resolve relative file paths.

## Project root

The project root MUST be a local filesystem directory.

For commands that use `depmesh.toml`, the project root MUST be the directory that contains the active configuration file.

A project file path MUST identify a location inside the project root.

A project file path MUST NOT identify a location outside the project root after path normalization.

A project file path MUST NOT use an absolute host filesystem path as its canonical representation.

## Root-anchored syntax

The canonical syntax for a project file path MUST be:

```text
@/path/inside/project.ext
```

The `@` marker MUST represent the project root.

The `/` character MUST separate path segments.

The path after `@/` MUST contain at least one path segment.

The canonical representation MUST NOT contain:

- empty path segments.
- `.` path segments.
- `..` path segments.
- a trailing `/`.

Examples of valid canonical file paths:

```text
@/README.md
@/specs/behavior/config.md
@/depmesh/discovery/paths.py
```

Examples of invalid canonical file paths:

```text
@
@/
@/specs/../README.md
@/specs//config.md
@/specs/
/home/user/project/README.md
```

## Path semantics

A project file path identifies a local project file by its normalized position under the project root.

File path identity MUST be based on the canonical file path, not on the textual form originally provided by a user, configuration file, command source, or other input.

Two file path inputs that normalize to the same canonical file path MUST identify the same project file.

The existence of a project file path MUST be checked by the context that uses it.

A field that declares existing-file semantics MUST reject or skip canonical file paths that do not correspond to an existing regular file, according to that field's behavior.

A field that declares reference semantics MAY accept canonical file paths that do not exist yet, for example when a configured rule describes an expected future dependency.

## Path normalization

Path normalization MUST produce a canonical file path.

Normalization MUST:

- resolve the input against the project root or an explicit base path.
- remove redundant `.` path segments.
- process `..` path segments.
- reject the path if processing `..` escapes the project root.
- use `/` as the path separator in the canonical representation.
- preserve meaningful path segment case.

Normalization MUST NOT require the referenced file to exist unless the calling context requires an existing file.

Implementations MUST reject inputs that cannot be normalized to a project file path inside the project root.

## Root-anchored resolution

A root-anchored file path MUST be resolved from the project root.

For example, in a project rooted at `/project`, the input:

```text
@/specs/behavior/config.md
```

resolves to:

```text
/project/specs/behavior/config.md
```

The normalized canonical representation remains:

```text
@/specs/behavior/config.md
```

Root-anchored inputs MAY contain redundant `.` or `..` segments before normalization, but the canonical representation MUST NOT contain them.

For example:

```text
@/specs/behavior/../dictionary.md
```

normalizes to:

```text
@/specs/dictionary.md
```

If a root-anchored input attempts to escape the project root, normalization MUST fail.

## Relative path resolution

Relative file paths MUST be accepted only by contexts that explicitly define a base path.

Relative file paths MUST NOT be resolved against the current working directory unless the accepting context explicitly defines the current working directory as the base path.

When the base path is a file, the relative path MUST be resolved against the directory that contains the base file.

When the base path is a directory, the relative path MUST be resolved against that directory.

After resolving a relative file path, depmesh MUST normalize the result to a canonical root-anchored file path.

For example, with base file:

```text
@/specs/behavior/config.md
```

the relative input:

```text
../dictionary.md
```

normalizes to:

```text
@/specs/dictionary.md
```

With the same base file, the relative input:

```text
../../../outside.md
```

MUST fail if it escapes the project root.

Relative file paths are intended for future features such as references inside files, generated dependency lists, and local navigation from one project file to another. New CLI and configuration examples SHOULD prefer root-anchored file paths unless relative addressing is central to the feature being described.

## CLI file path inputs

CLI input parameters that accept project file paths MUST accept:

- root-anchored file paths.
- classical relative filesystem paths.
- classical absolute filesystem paths.

CLI logic MUST normalize every accepted file path input to a canonical root-anchored file path before dependency matching, dependency output construction, or other project file path processing.

When a CLI input parameter receives a root-anchored file path, the path MUST be resolved from the project root and normalized to the canonical root-anchored form.

For example:

```text
@/specs/behavior/../dictionary.md
```

normalizes to:

```text
@/specs/dictionary.md
```

When a CLI input parameter receives a classical absolute filesystem path, the path MUST be normalized to a canonical root-anchored file path if it points inside the project root.

For example, in a project rooted at `/project`, the CLI input:

```text
/project/specs/behavior/config.md
```

normalizes to:

```text
@/specs/behavior/config.md
```

If a classical absolute filesystem path points outside the project root, the CLI MUST reject it.

When a CLI input parameter receives a classical relative filesystem path, the path MUST first be resolved to an absolute filesystem path relative to the command's current working directory.

The resolved absolute filesystem path MUST then be normalized to a canonical root-anchored file path if it points inside the project root.

For example, in a project rooted at `/project`, when the command's current working directory is `/project/specs`, the CLI input:

```text
behavior/config.md
```

first resolves to:

```text
/project/specs/behavior/config.md
```

and then normalizes to:

```text
@/specs/behavior/config.md
```

If a classical relative filesystem path resolves outside the project root, the CLI MUST reject it.

New CLI examples and protocol output SHOULD use canonical root-anchored file paths unless demonstrating classical relative or absolute filesystem input compatibility.

## Host filesystem paths

Absolute host filesystem paths MUST NOT be canonical project file path identifiers.

Implementations MAY accept an absolute host filesystem path as input only when the accepting context explicitly supports host path input. CLI input parameters that accept project file paths are one such context.

When accepted, an absolute host filesystem path MUST resolve to a location inside the project root and MUST normalize to a canonical root-anchored file path.

An absolute host filesystem path outside the project root MUST be rejected.

## File path patterns

Some depmesh features accept file path patterns instead of concrete file paths. Examples include glob predicates and file sources in `depmesh.toml`.

File path patterns are not project file paths and MUST NOT be treated as canonical file path identifiers.

When a file path pattern refers to project files, its path anchoring and project-boundary behavior MUST be consistent with project file paths.

A file path pattern that starts with `@/` MUST treat `@` as the project root.

A relative file path pattern MUST be accepted only by contexts that explicitly define a base path for pattern resolution.

Pattern matching MUST NOT produce canonical file paths outside the project root.

This specification defines only path anchoring and project-boundary behavior for file path patterns.

The feature that accepts a file path pattern MUST define the pattern's own matching syntax, wildcard behavior, capture syntax, and existence semantics.
