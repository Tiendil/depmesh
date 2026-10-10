# Module structure

## Goal of the document

This document describes the module structure of the project.

## Scope

The scope of this specification is limited to the list of project modules and their intended responsibilities.

The following topics are out of scope:

- detailed implementation design.
- dependency rules.
- runtime behavior.
- entity, error, and test conventions beyond module placement.

## Dictionary

- `module` — a Python package or module that owns a coherent area of project functionality.
- `submodule` — a Python package or module inside another module that owns a narrower part of its parent module's functionality.
- `test submodule` — a module or file containing tests for a corresponding parent module or submodule.

## Modules

- `./depmesh/` — root module of the project, contains all code related to the `depmesh` tool.
- `./depmesh/core/` — module responsible for the core functionality not related to domain logic. Contains:
  - shared error base classes.
  - shared warning storage.
  - domain-independent utilities.
- `./depmesh/domain/` — module responsible only for universal domain entities and logic required by all or most other modules. Contains:
  - shared domain-specific types.
  - shared domain data structures.
  - pure domain logic that is independent of more specific subsystems.
  - no subsystem-specific rule evaluation, protocol rendering, workspace loading, or CLI behavior.
- `./depmesh/discovery/` — module responsible for dependency discovery logic. Contains:
  - dependency discovery rules.
  - artifact predicate definitions and matching behavior.
  - artifact source definitions and evaluation behavior.
  - dependency query results.
  - dependency query evaluation.
- `./depmesh/runtime/` — module responsible for command-facing domain operations. Contains:
  - workspace loading through shared configuration mechanics and local workspace construction.
  - input normalization and relation selection for dependency queries.
  - aggregation and ordering of dependency results across input artifacts.
  - warning snapshots and construction of complete result logic cells.
  - relation listing and configuration initialization with logic-cell results.
  - no CLI argument parsing, protocol selection, or output writing.
- `./depmesh/protocol/` — module responsible for projecting project data into output cells. Contains:
  - grouped Markdown dependency content for human and LLM output.
  - structured dependency, relation, warning, and skill cell construction.
  - dependency-result logic cells built on the shared logic-cell base.
  - use of shared content logic cells for protocol-independent payloads and protocol-specific output-cell types inside dependency projections.
- `./depmesh/skills/` — module responsible for built-in skill document definitions and packaged Markdown resources.
- `./depmesh/workspace/` — module responsible for workspace management, including:
  - configuration schema and validated workspace entities.
  - constructing configured relations and dependency rules.
  - the packaged starter configuration.
- `./depmesh/cli/` — module responsible for argument parsing, runtime invocation, protocol selection, and writing returned logic cells, with shared error handling and stream and exit policies.

The public `depmesh.runtime.commands` boundary MUST expose command-facing operations returning logic cells or ordered collections of their subclasses through shared results.
The runtime MUST assemble domain-result cells before returning them to the CLI.
The CLI MUST NOT query discovery rules, aggregate internal query results, read warning storage, or construct domain-result payloads.
Internal discovery and workspace APIs MAY retain their own typed results.

Output protocol values, the abstract `OutputCell` and its protocol-specific subtypes, the `LogicCell` base and protocol dispatch, shared content logic cells, rendering contexts, sequence rendering and environment-error cell construction, and text writing MUST be owned by `llm_tool_cli.protocol` and used directly.
Depmesh MUST own concrete dependency-result logic cells and their protocol-specific projections.
Logic-cell projections MUST return the corresponding shared output-cell subtype.
The CLI MUST pass complete logic-cell sequences to shared rendering with the selected protocol and Depmesh's tool label.
Protocol-independent content MUST use shared content logic cells without an output-cell class supplied by the CLI.
Depmesh MUST NOT maintain renderer wrappers or a parallel formatter family.
Environment errors MUST use the shared typed error logic cell, which owns their content and metadata projection.

The CLI MUST use `llm_tool_cli.skills` directly for skill-document loading and propagate its returned errors without local adapters.

## Submodules

Modules can have submodules that are responsible for more specific parts of the functionality.

When a module contains a small closed family of interchangeable components, and each component has meaningful component-specific behavior, the module SHOULD prefer one implementation submodule per component.

Shared package-level code for such component families SHOULD be limited to common types, public unions, selection helpers, and iteration glue.

Some submodules have specific names that reflect their responsibilities and MUST be similar across different modules.

List of specific submodules:

- `utils` — submodule responsible for utility functions that are not related to the domain logic.
- `errors` — submodule responsible for defining environment-error models and internal exception types.
- `domain` — submodule responsible for domain-specific logic related to the module's responsibilities.
- `entities` — submodule responsible for defining types and entities related to the module's responsibilities.
- `tests` — submodule containing module tests.

The `errors`, `entities`, and `tests` submodules MUST follow the corresponding architecture specifications when they are present.

The common Pydantic entity base used by higher-level modules MUST be owned by `llm_tool_cli.core.entities`.

Lexical root-anchored project path normalization, its canonical identifier type, filesystem resolution and containment, symlink rejection, and file enumeration MUST be owned by `llm_tool_cli.paths` and used directly.
Depmesh MUST retain pattern template substitution and context-specific warning handling.
Enumeration failures MUST use the shared `FilesUnreadable` diagnostic without a duplicate project error type.

### Test submodules

Each submodule MUST have a corresponding `tests` submodule that contains tests for the code in the parent submodule.

The name of a test submodule MUST be built from the name of the parent submodule by adding the `test_` prefix. The structure of the test submodule SHOULD mirror the structure of the parent submodule.

Examples:

- `./depmesh/core/utils.py` -> `./depmesh/core/tests/test_utils.py`
- `./depmesh/domain/entities.py` -> `./depmesh/domain/tests/test_entities.py`
