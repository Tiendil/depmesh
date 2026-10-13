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

Application of the shared path contract is covered by `specs/behavior/cli.md` for command inputs and `specs/behavior/config.md` for configured paths, patterns, capture binding, and source failure policies.
Generic path and glob semantics belong to `specs/behavior/paths.md` in the `llm-tool-cli` repository; shared implementation ownership is covered by `specs/architecture/modules_layout.md`.

The shared root configuration-version field with Depmesh-owned supported versions and defaults is covered by `specs/architecture/modules_layout.md` and `specs/behavior/config.md`; session-directory configuration remains absent.

Prohibited journaling for dependency-result and generic content cells, and shared emitter ownership, are covered by `specs/architecture/modules_layout.md` and `specs/behavior/cli.md`; terminal-error journaling and delivery-failure recovery are covered by `specs/architecture/errors.md` and `specs/behavior/cli.md`.

- `./specs/intro.md` — this file, contains a list of all specifications and their brief descriptions.
- `./specs/dictionary.md` — dictionary of project-specific terms shared by multiple specifications, including returned expected operational errors.
- `./specs/architecture/entities.md` — specification of project entity and data structure architecture, including direct use of the shared library's entity base and canonical project path identifier type, with logic cells and their ordered collections as the primary domain-to-CLI result interface.
- `./specs/architecture/errors.md` — specification of project error and diagnostic architecture, including shared Result propagation with a fixed environment-error list, centralized CLI failure handling, scoped warning cells delivered after final results, exception-based predicate matching, explicitly named environment-error and internal-exception hierarchies, and exception boundaries.
- `./specs/architecture/modules_layout.md` — specification of the project module structure, including runtime submission of command-facing cells and emitter-owned batch rendering and stream writing, shared entity infrastructure ownership, and shared lexical project path normalization boundary; shared file enumeration and rejection of symbolic links below the resolved project root are included; independent frozen static, runtime, and project configurations own application identity, effective protocol, and workspace paths without duplicate storage. Shared project loading and initialization contexts own discovery, validation, and project scopes using a filename from static settings. Shared command execution scopes and complete initialization-command registration are managed by the library.
- `./specs/architecture/naming.md` — specification of project code naming conventions.
- `./specs/architecture/static_analysis.md` — specification of static analysis, formatting, linting, spelling, and type-checking expectations.
- `./specs/architecture/tests.md` — specification of project test architecture, including returned error propagation, internal-exception separation, CLI mapping checks, shared automation payload extraction and error-cell assertions, local output parsing, and scoped output capture.
- `./specs/behavior/cli.md` — specification of the `depmesh` command line interface, including shared static, runtime, and project configuration and configuration path inputs, native environment-error records, ordered error lists, exit categories, direct shared-emitter submission, buffered result cells, and warnings retained on expected failure. Shared project loading and initialization contexts own discovery, validation, and project scopes using a filename from static settings. All cell kinds, including errors, use stdout in every protocol. Shared command execution scopes and complete initialization-command registration are managed by the library.
- `./specs/behavior/config.md` — specification of the `depmesh.toml` configuration file behavior, including independent immutable shared configuration bindings, discovery and home-relative explicit paths; file discovery uses shared enumeration without symbolic-link traversal. Shared project loading and initialization contexts own discovery, validation, and project scopes using a filename from static settings.
- `./specs/behavior/skill_fixtures.md` — specification of built-in skill documentation fixture behavior.
- `./specs/documentation/changelog.md` — specification of changelog tooling, source files, version record structure, and entry format.
- `./specs/documentation/readme.md` — specification of the root `README.md` content and purpose.
- `./specs/meta/general.md` — general requirements for specification documents.
