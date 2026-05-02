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
  - shared entity base classes.
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
- `./depmesh/protocol/` — module responsible for output protocol types and rendering. Contains:
  - protocol enums.
  - renderer selection.
  - protocol-specific renderers.
  - serialized record construction for external output protocols.
- `./depmesh/skills/` — module responsible for built-in skill text loaded by the CLI and renderers.
- `./depmesh/workspace/` — module responsible for workspace management, including:
  - finding and parsing config.
  - detecting current project root.
  - operations with the filesystem.
- `./depmesh/cli/` — module responsible for the CLI interface of the `depmesh` tool.

## Submodules

Modules can have submodules that are responsible for more specific parts of the functionality.

When a module contains a small closed family of interchangeable components, and each component has meaningful component-specific behavior, the module SHOULD prefer one implementation submodule per component.

Shared package-level code for such component families SHOULD be limited to common types, public unions, selection helpers, and iteration glue.

Some submodules have specific names that reflect their responsibilities and MUST be similar across different modules.

List of specific submodules:

- `utils` — submodule responsible for utility functions that are not related to the domain logic.
- `errors` — submodule responsible for defining custom exception types.
- `domain` — submodule responsible for domain-specific logic related to the module's responsibilities.
- `entities` — submodule responsible for defining types and entities related to the module's responsibilities.
- `tests` — submodule containing module tests.

The `errors`, `entities`, and `tests` submodules MUST follow the corresponding architecture specifications when they are present.

The shared `entities` submodule in `./depmesh/core/` MUST define the common Pydantic entity base used by higher-level modules.

### Test submodules

Each submodule MUST have a corresponding `tests` submodule that contains tests for the code in the parent submodule.

The name of a test submodule MUST be built from the name of the parent submodule by adding the `test_` prefix. The structure of the test submodule SHOULD mirror the structure of the parent submodule.

Examples:

- `./depmesh/core/utils.py` -> `./depmesh/core/tests/test_utils.py`
- `./depmesh/domain/entities.py` -> `./depmesh/domain/tests/test_entities.py`
