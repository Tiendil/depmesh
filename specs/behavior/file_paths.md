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

A project file path MUST identify a location inside the project root after normalization.

## Root-anchored syntax

Canonical file paths MUST start with `@/`, which denotes the project root, followed by one or more non-empty `/`-separated segments.
They MUST NOT contain `.` or `..` segments or a trailing `/`.

## Path semantics

A project file path identifies a local project file by its normalized position under the project root.

File path identity MUST be based on the canonical file path, not on the original input spelling.
Two file path inputs that normalize to the same canonical file path MUST identify the same project file.

The existence of a project file path MUST be checked by the context that uses it.

A field that declares existing-file semantics MUST reject or skip canonical file paths that do not correspond to an existing regular file, according to that field's behavior.

A field that declares reference semantics MAY accept canonical file paths that do not exist yet.

## Path normalization

Path normalization MUST produce a canonical file path while preserving meaningful segment case.
Root-anchored paths MUST be resolved from the project root; relative paths MUST use an explicit base.
Normalization MUST remove `.` segments and resolve `..` segments to the parent, rejecting traversal above the project root.

Normalization MUST NOT require the referenced file to exist unless the calling context requires an existing file.
Lexical normalization of a root-anchored path MUST NOT be treated as proof of filesystem containment.
Filesystem resolution MUST reject paths that escape the project root through symbolic links.

Implementations MUST reject inputs that cannot be normalized to a project file path inside the project root.

## Relative path resolution

Relative file paths MUST be accepted only by contexts that explicitly define a base path.

Relative file paths MUST NOT be resolved against the current working directory unless the accepting context explicitly defines the current working directory as the base path.

When the base path is a file, the relative path MUST be resolved against the directory that contains the base file.

When the base path is a directory, the relative path MUST be resolved against that directory.

After resolving a relative file path, depmesh MUST normalize the result to a canonical root-anchored file path.

## CLI file path inputs

CLI input parameters that accept project file paths MUST accept:

- root-anchored file paths.
- classical relative filesystem paths.
- classical absolute filesystem paths.

CLI logic MUST normalize every accepted file path input to a canonical root-anchored file path before dependency matching, dependency output construction, or other project file path processing.

Classical relative filesystem inputs MUST be resolved against the command's current working directory.
The CLI MUST reject relative or absolute filesystem inputs that resolve outside the project root.

New CLI and configuration examples and protocol output SHOULD use canonical root-anchored paths unless demonstrating relative or absolute filesystem input compatibility.

## Host filesystem paths

Absolute host filesystem paths MAY be accepted only by contexts that explicitly support them, including CLI project-file inputs.
They MUST resolve inside the project root and normalize to canonical root-anchored paths.

## File path patterns

Some depmesh features accept file path patterns instead of concrete file paths. Examples include glob predicates and file sources in `depmesh.toml`.

File path patterns are not project file paths and MUST NOT be treated as canonical file path identifiers.

When a file path pattern refers to project files, its path anchoring and project-boundary behavior MUST be consistent with project file paths.
A relative file path pattern MUST be accepted only by contexts that explicitly define a base path for pattern resolution.

Pattern matching MUST NOT produce canonical file paths outside the project root.

The feature that accepts a file path pattern MUST define the pattern's own matching syntax, wildcard behavior, capture syntax, and existence semantics.
