# Module structure

## Goal of the document

This document describes the module structure of the project.

## Scope

The scope of this specification is limited to the list of project modules and their intended responsibilities.

The following topics are out of scope:

- detailed implementation design.
- dependency rules.
- runtime behavior.

## Dictionary

- `module` — a Python package or module that owns a coherent area of project functionality.
- `submodule` — a Python package or module inside another module that owns a narrower part of its parent module's functionality.
- `test submodule` — a module or file containing tests for a corresponding parent module or submodule.

## Modules

- `./depmesh/` — root module of the project, contains all code related to the `depmesh` tool.
- `./depmesh/core/` — module responsible for the core functionality not related to domain logic.
- `./depmesh/domain/` — module responsible for the general domain logic that is used in all parts of the project. Contains:
  - domain-specific types.
  - data structures.
  - code related to pure domain logic.
- `./depmesh/workspace/` — module responsible for workspace management, including:
  - finding and parsing config.
  - detecting current project root.
  - managing plugins.
  - operations with the filesystem.
- `./depmesh/cli/` — module responsible for the CLI interface of the `depmesh` tool.

## Submodules

Modules can have submodules that are responsible for more specific parts of the functionality.

Some submodules have specific names that reflect their responsibilities and MUST be similar across different modules.

List of specific submodules:

- `utils` — submodule responsible for utility functions that are not related to the domain logic.
- `errors` — submodule responsible for defining custom exception types.
- `domain` — submodule responsible for domain-specific logic related to the module's responsibilities.
- `entities` — submodule responsible for defining types and entities related to the module's responsibilities.
- `tests` — submodule containing module tests.

### Test submodules

Each submodule MUST have a corresponding `tests` submodule that contains tests for the code in the parent submodule.

The name of a test submodule MUST be built from the name of the parent submodule by adding the `test_` prefix. The structure of the test submodule SHOULD mirror the structure of the parent submodule.

Examples:

- `./depmesh/core/utils.py` -> `./depmesh/core/tests/test_utils.py`
- `./depmesh/domain/entities.py` -> `./depmesh/domain/tests/test_entities.py`
