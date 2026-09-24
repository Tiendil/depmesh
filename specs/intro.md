# List of specifications

## Goal of the document

This document lists all specification documents and specification directories in the project and briefly describes their purpose.

## Scope

The scope of this specification is limited to the specification index.

Detailed requirements for individual specifications are out of scope except for brief descriptions needed to keep the index useful.

## Specification directories

- `./specs/` — directory with all specifications.
- `./specs/architecture/` — specifications related to the architecture of the system.
- `./specs/behavior/` — specifications related to the behavior of the system.
- `./specs/documentation/` — specifications related to project documentation artifacts.
- `./specs/meta/` — specifications related to requirements for specification documents.

## Specification documents

- `./specs/intro.md` — this file, contains a list of all specifications and their brief descriptions.
- `./specs/dictionary.md` — dictionary of project-specific terms shared by multiple specifications, including returned expected operational errors.
- `./specs/architecture/entities.md` — specification of project entity and data structure architecture, including direct use of the shared library's entity base.
- `./specs/architecture/errors.md` — specification of project error and diagnostic architecture, including shared Result propagation, centralized CLI failure handling, exception-based predicate matching, explicitly named environment-error and internal-exception hierarchies, and exception boundaries.
- `./specs/architecture/modules_layout.md` — specification of the project module structure and shared entity infrastructure ownership.
- `./specs/architecture/naming.md` — specification of project code naming conventions.
- `./specs/architecture/static_analysis.md` — specification of static analysis, formatting, linting, spelling, and type-checking expectations.
- `./specs/architecture/tests.md` — specification of project test architecture, including returned error propagation, internal-exception separation, and CLI mapping checks.
- `./specs/behavior/cli.md` — specification of the `depmesh` command line interface, including configuration path inputs, native environment-error records, ordered error lists, and exit categories.
- `./specs/behavior/config.md` — specification of the `depmesh.toml` configuration file behavior, including discovery and home-relative explicit paths.
- `./specs/behavior/file_paths.md` — specification of local project file path syntax, semantics, and resolution behavior.
- `./specs/behavior/skill_fixtures.md` — specification of built-in skill documentation fixture behavior.
- `./specs/documentation/changelog.md` — specification of changelog tooling, source files, version record structure, and entry format.
- `./specs/documentation/readme.md` — specification of the root `README.md` content and purpose.
- `./specs/meta/general.md` — general requirements for specification documents.
