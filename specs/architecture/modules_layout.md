# Module structure

## Goal of the document

This document describes module ownership and public boundaries.

## Scope

This specification covers project modules and responsibilities.
The following are out of scope:

- implementation design.
- dependency rules.
- runtime behavior.
- entity/error/test conventions beyond placement.

## Dictionary

- `module` — a Python package/module owning coherent functionality.
- `submodule` — a narrower responsibility within a module.
- `test submodule` — tests of a parent module/submodule.

## Modules

All Depmesh code belongs under `depmesh/`:

- `core` — Error bases and domain-independent utilities.
- `domain` — Universal types, structures, and pure logic used by all/most modules; excludes:

  - Subsystem rules.
  - Rendering.
  - Workspace loading.
  - CLI behavior.

- `discovery`:

  - Rules.
  - Predicates/matching.
  - Sources/evaluation.
  - Query results/evaluation.

- `runtime` — No CLI parsing, protocol selection, or output writing; owns:

  - Input normalization.
  - Relation selection.
  - Cross-input aggregation/order.
  - Result-cell submission.
  - Relation listing.

- `protocol` — Dependency/relation cells and projections, grouped human/LLM Markdown, content cells and concrete output types from `llm_tool_cli`.
- `skills` — Document definitions and packaged Markdown.
- `workspace` — Schema, validated/compiled relations and rules, starter configuration.
- `cli`:

  - Parsing.
  - Runtime invocation.
  - Protocol/delivery setup.
  - Errors/streams/exits through `llm_tool_cli`.

Command-facing runtime operations MUST assemble/submit complete cells and return a result provided by `llm_tool_cli` without a value when no other result is useful.
CLI MUST NOT:

- query rules.
- aggregate internal results.
- read warning storage.
- assemble payloads.

Internal discovery/workspace APIs MAY retain typed results.

Depmesh MUST directly use the following from `llm_tool_cli`:

- protocol values.
- cell bases/subtypes.
- dispatch.
- content cells.
- rendering contexts.
- typed error cells.

Local dependency cells MUST own projections into matching shared output types.
Shared output MUST own batch rendering/writing; protocol MUST retain individual projection/formatting.
Project content MUST use shared cells without CLI-supplied output classes.
The following MUST NOT duplicate shared code:

- local render wrappers.
- formatter families.
- warning storage.
- warning projections.

CLI MUST directly use command scope from `llm_tool_cli`, without lifecycle wrappers, to bind output and finalize results then warnings.
Sources MUST submit shared warnings directly while retaining typed query results.
Dependency cells MUST prohibit journal delivery in their types and construction, without record conversion; relation content MUST retain shared journal prohibition.
`llm_tool_cli` MUST own the following without Depmesh services/wrappers:

- journal submission.
- default factories.
- processors.

Skill loading MUST directly use `llm_tool_cli.skills`, preserving errors without adapters.
Skill fixtures MUST live in `depmesh/skills/fixtures/` under the library's resource-loading convention; Depmesh MUST own document definitions and contents.
CLI MUST use application construction and shared skill/version command registration from `llm_tool_cli`, supplying `depmesh.skills`, its document definitions, and distribution identity `depmesh`.

Depmesh MUST use independent frozen settings from `llm_tool_cli` for static application identity, invocation protocol, and selected project.
Static settings MUST supply the default configuration filename before parsing; project settings MUST own the active path and derived root.

Root version MUST use strict integer validation from `llm_tool_cli` with local version constraints and defaults.
Depmesh MUST own supported versions/defaults; shared validation MUST apply its constraint.
Session-directory configuration MUST NOT exist without session storage behavior.
Compiled workspaces MUST contain relations/rules without copied paths/root.

CLI MUST use project-loading scope from `llm_tool_cli` through framework resources.
Initialization MUST use the command provided by `llm_tool_cli` with Depmesh schema and the workspace-owned starter template, retaining project scope through framework resources.
`llm_tool_cli` MUST own:

- discovery.
- loading.
- starter creation and validation.
- project setting construction, binding, and restoration.

Local preparation wrappers MUST NOT remain.

Workspace MUST compile the yielded validated configuration.
Shared init MUST emit the generic creation acknowledgement; domain payloads MUST remain runtime-owned.

Query orchestration MUST receive compiled workspace explicitly and read the active project root.
Lower discovery MAY receive explicit root/cwd.
Compiled workspaces MAY stay local; no global binding is required without a global consumer.

## Submodules

Submodules are optional unless required elsewhere.
Small closed interchangeable-component families SHOULD use one implementation submodule per meaningfully distinct component.
Shared family code SHOULD contain only:

- common types.
- public unions.
- selection.
- iteration glue.

Conventional names MUST stay consistent:

- `utils` — Non-domain utilities.
- `errors` — Environment models/internal exceptions.
- `domain` — Module-specific domain logic.
- `entities` — Owned types/entities.
- `fixtures` — Reusable configuration/docs/data.
- `tests` — Module tests.
- `tests.make` — Test-object construction.
- `tests.helpers` — Setup, mutation, workflows.

Errors/entities/tests MUST follow their architecture specs.
Higher modules MUST use `llm_tool_cli.core.entities` for the common Pydantic base.

Paths MUST directly use `llm_tool_cli.paths` for:

- lexical ids/normalization.
- resolution.
- containment.
- symlink rejection.
- glob preparation/matching/capture validation.
- enumeration.

Glob predicates MUST use shared matching after substitution and shared capture validation during schema loading, without local compilers/parsers.
Depmesh MUST retain templates, capture-to-output binding, and contextual warnings.
Enumeration errors MUST propagate shared diagnostics without duplication.

### Test submodules

Tests SHOULD live under the nearest owning package's `tests`, named with the parent's `test_` prefix; structure SHOULD mirror implementation.
Coverage MUST follow the test architecture's owned-behavior requirements rather than file symmetry.
**Example:** `domain/entities.py` maps to `domain/tests/test_entities.py`.

Reusable construction SHOULD live in `tests.make`; setup, assertions, and coordinated actions SHOULD live in `tests.helpers`.
Production MUST NOT import test utilities.

## Cross-module dependencies

### Import boundaries

Top-level modules MUST expose explicit stable boundaries through package roots or declared public submodules.
Public submodules SHOULD be cohesive and MUST NOT expose incidental helpers, storage details, or compatibility shims unless intentionally stable.
Initializers SHOULD export ergonomic common names and define `__all__`, but MUST NOT be required to re-export every submodule name.
Owned `errors` MUST be public.
Roots without useful APIs MAY be empty or have empty `__all__`.

Cross-module imports MUST use declared boundaries, never undeclared internals; same-owner submodules MAY import directly.
Configured dependency checks MUST enforce the specified ownership and dependency direction.
Check configuration MUST NOT permit undeclared dependencies merely to silence a finding.
`utils` is public only if explicitly declared.
**Example:** CLI may import `depmesh.workspace` or its declared public submodules, not its private implementation.

Modules MAY import protocol boundary values/helpers to expose owned concepts.
Typed-cell construction MUST NOT count as a boundary violation or protocol-specific rendering.
Only protocol/CLI modules MAY depend on protocol-specific formatter implementations; non-protocol modules SHOULD NOT own serialization details.
Protocol rendering means concrete external serialization, such as:

- text framing.
- LLM boundaries.
- JSON Lines.
- bytes.
- formatter ordering.
