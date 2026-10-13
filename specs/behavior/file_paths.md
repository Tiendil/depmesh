# File paths

## Goal of the document

This document describes how Depmesh commands and dependency rules apply the shared project-path contract.

## Scope

This specification covers path input bases, existence policies, and pattern boundaries.
Generic path syntax, normalization, containment, symlink handling, enumeration, and path diagnostics are governed by `specs/behavior/paths.md` in the `llm-tool-cli` repository.
Dependency relation semantics and output formatting are out of scope.

## Shared project paths

Depmesh MUST use the shared project-path contract at CLI and dependency normalization boundaries.
The project root MUST be the local directory containing the active configuration file, selected according to `specs/behavior/config.md`.

## CLI file path inputs

CLI input parameters that accept project file paths MUST accept root-anchored, relative filesystem, and absolute filesystem paths.
Relative filesystem inputs MUST use the command's current working directory as their base.
Command execution MUST normalize every accepted input to a canonical project-path identifier before dependency matching or output construction.
CLI dependency inputs MAY reference locations that do not yet exist.

New CLI and configuration examples and protocol output SHOULD use canonical root-anchored paths unless demonstrating relative or absolute filesystem input compatibility.

## Configured predicates and sources

Configured concrete paths and dependency identifiers produced by sources MUST use the configuration root as their relative filesystem base.
Predicates, list sources, and command sources MAY refer to locations that do not yet exist.
File sources MUST use shared enumeration of existing regular files, with the warning and error policies specified in `specs/behavior/config.md`.
Template substitution MUST precede path interpretation.

## File path patterns

Glob predicates and file sources accept patterns rather than concrete path identifiers.
Patterns MUST retain project anchoring and containment, using the configuration root as their relative filesystem base.
Their matching syntax, wildcard behavior, capture syntax, and existence semantics are specified in `specs/behavior/config.md`.
