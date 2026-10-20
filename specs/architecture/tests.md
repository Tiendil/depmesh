# Test architecture

## Goal of the document

This document describes test organization, ownership, and coverage.

## Scope

Python test organization and architectural expectations; the following are out of scope:

- framework/CI configuration.
- exact fixture names.
- publishing checks.
- performance benchmarks.

## Dictionary

- `unit test` — tests one module or a small related group of functions/entities.
- `integration test` — tests multiple modules through a public boundary.
- `fixture` — reusable data or setup.
- `architecture test` — verifies a project-wide architectural convention.
- `behavior example test` — verifies a behavior-spec example or rule.

## General principles

Tests MUST belong to the Python project and run through development containers, preferably `./bin/dev.sh uv run -- pytest [<path>]`.
They SHOULD be deterministic for the same repository/filesystem state.
Required shared state MUST be prepared at test start or via class/module autouse fixtures.

Tests SHOULD prefer public-boundary end-to-end coverage where practical, using:

- real code.
- temporary files.
- explicit fixtures.
- small fakes.

Mocks, stubs, and patching SHOULD be minimal.

Tests MUST NOT use networks, user-specific files outside test-created temporary directories, or alter Docker configuration/runtime parameters.
They SHOULD verify observable behavior/local validation, not declarations, and separate orthogonal cases.
Typing SHOULD use static analysis/review/architecture checks.
Only broad-convention architecture tests MAY inspect annotations; entity tests MUST NOT restate declarations.
Boolean assertions MUST use `assert condition` or `assert not condition` rather than identity checks.

## Mocking

The following SHOULD be preferred:

- real code.
- fixtures.
- constructors.
- temporary files.
- small fakes.

Necessary Python replacements SHOULD use the standard pytest mocking tool, scoped to the test and targeting the lookup location.
Use `mocker.patch("<import.path>", ...)` for imported names/settings when `pytest-mock` is available, and `mocker.patch.object(...)` for available objects/classes.
Direct `MagicMock` is only for local fakes passed into subjects.
Ordinary attribute replacement SHOULD NOT use `monkeypatch` when the standard fixture is available.

## Test module layout

Tests SHOULD live under the nearest owning package's `tests`, mirroring implementation structure where clearer and retaining nested component ownership.
Files MUST use `test_<module>.py`.
**Example:** `discovery/predicates/glob.py` maps to `discovery/predicates/tests/test_glob.py`, not a flattened discovery test package.
Integration tests MAY belong to the exercised public boundary; CLI tests SHOULD live in `depmesh/cli/tests/`.

Reusable utilities SHOULD use:

- `tests.make` — Small valid-data factories for:

  - Entities.
  - Relations.
  - Rules.
  - Other project data.

- `tests.helpers`:

  - Assertions.
  - Setup.
  - Cleanup.
  - Workflows.

`make` MUST NOT contain assertions/verification; `helpers` MUST NOT contain ordinary constructors fitting `make`.
Tests MAY reuse other modules' test utilities for non-owned setup/integration, but reuse MUST remain test-only and MUST NOT create production dependencies on tests.

## Test organization

Tests SHOULD group by subject.
Production functions MUST have test classes when they own non-trivial behavior; classes SHOULD have test classes when they own non-trivial behavior.
Test classes MUST use `Test<PascalCaseSubject>` and group the subject's method tests.
Method cases MUST use `test_<snake_case_method>__<snake_case_behavior>`; module-function cases MAY use `test_<case>`.
**Example:** `TestLoadWorkspace.test_success` tests a function; `TestArtifact.test_parse__invalid_value` tests a method.
Test-only helpers need no test class.
Standalone tests SHOULD be limited to module invariants/file checks without a natural function/class owner.

Every meaningful execution path MUST have a method or parametrized case, including:

- success/defaults.
- empty/invalid inputs.
- handled errors.
- warnings.
- individual branches.

Tests MUST cover corner cases, including:

- boundaries.
- empty collections/strings.
- missing optionals.
- duplicates.
- unsupported/malformed input.
- missing paths.
- normalization.
- repeated calls exposing state leaks.

## Entity tests

Tests SHOULD verify local invariants and MUST verify owned behavior/invariants.
They SHOULD cover:

- custom field/model validation.
- non-trivial defaults/factories.
- normalization.
- methods/properties.
- serialization/deserialization.
- invalid-value rejection.

Tests MUST NOT exist merely for file symmetry or verify passive argument assignment/model construction.
Plain `NewType`, enum existence, and passive fields MUST NOT be tested unless the owner supplies non-trivial:

- conversion.
- validation.
- serialization.
- compatibility behavior.

Passive-only modules SHOULD omit meaningless test files.
Tests SHOULD NOT repeat unchanged shared-base or trivial Pydantic behavior.
Entity tests MUST NOT access filesystems unless the entity explicitly owns filesystem-dependent normalization.
They MUST NOT verify CLI rendering.
Low-level model tests MAY assert `pydantic.ValidationError`.

## Error tests

Tests SHOULD verify customized error behavior.

### Testing `errors.py` modules

Declarative-only errors SHOULD NOT get tests for layout symmetry.
Unit tests SHOULD exist only for behavior beyond inherited construction/static attributes, and MAY cover:

- custom construction.
- validation/normalization.
- custom code computation.
- message formatting.
- structured details.
- intermediate-class behavior.

They MUST NOT merely assert static:

- codes.
- messages.
- guidance.
- fields.

Exact production messages MUST NOT be asserted unless behavior specs make them stable contracts.
Unchanged inheritance/shared-base behavior SHOULD NOT be retested.
Optional `test_errors.py` SHOULD be omitted when producers cover all meaningful behavior.

### Testing error-producing behavior

Code propagation tests SHOULD compare against the owning error's declaration; literal code assertions MUST require an independently specified compatibility contract.
Boundary tests SHOULD verify expected low-level failures, including external-input Pydantic failures, become returned Depmesh or `llm_tool_cli` errors, or warning cells.
Result tests SHOULD inspect local/shared error values through result state, preserve mixed lists, and keep unexpected exceptions distinct from rendered expected failures.
Propagation-boundary tests MUST verify retained shared diagnostic information.
Producer tests SHOULD assert failure type and relevant context fields.
Internal-invariant tests MAY assert raised `InternalError` subclasses.
Tests SHOULD verify that the following survive until the CLI:

- error values.
- typed context.
- private causes.
- callback propagation.

They SHOULD distinguish no-match/warnings from fatal failure.

CLI tests SHOULD verify:

- specified exit categories and default non-zero exits for unmapped project/shared errors.
- error-list order and technical-exception separation.
- automation `error` records when possible.
- stdout delivery in every protocol.
- warning insertion order, successful exits for warnings alone, and protocol rendering after success or expected failure.

Tests SHOULD reuse automation payload/error assertions provided by `llm_tool_cli` while keeping the following local:

- parsing.
- filtering.
- stdout integration.
- Depmesh policies.

Output-producing domain tests MUST have a function-scoped fresh collecting emitter with restoration.
CLI tests MUST use setup/finalization provided by `llm_tool_cli` without resetting application buffers themselves.

## Behavior coverage

Behavior and architecture specs define expected behavior and conventions.
Tests SHOULD cover their implemented, runtime-testable examples/rules.
Changes to runtime code SHOULD be verified by tests covering affected behavior.
Changes limited to specifications, documentation, or static-analysis configuration MAY omit runtime tests when no runtime behavior is affected.
Coverage SHOULD include:

- Configuration:

  - Discovery.
  - `--config`.
  - TOML structure.
  - Defaults.
  - Relation/rule/predicate/source validation.
  - Normalization.
  - Invalid configuration.

- CLI:

  - Command forms.
  - Options/protocols.
  - Cell shape.
  - Relation lists.
  - Dependency grouping/order.
  - Relation filters.
  - Configured reverse queries.
  - Warnings.
  - Errors/exits.

## Fixtures and temporary data

Files SHOULD be temporary; data SHOULD be minimal.
Short fixtures SHOULD be inline, including configuration and output.
Reusable files MAY replace obscure inline data.
Expected normalized paths SHOULD use forward slashes.
Before ending, tests MUST restore:

- cwd.
- modified process globals.
- contexts.
- protocol.
- installed workspace configuration.
- mocks.

## Assertions

Tests SHOULD prefer structured values and parse automation JSON Lines before assertions.
Exact rendering SHOULD be asserted only for stable protocol/CLI/persisted contracts; selected lines/fields/records MAY be asserted otherwise.
Exclusive branches SHOULD assert both positive and negative outcomes.
Cell tests MUST compare content, metadata, and order independently of generated ids.
CLI tests SHOULD verify repeated invocations preserve payloads while allowing different ids.
Generic formatting tests belong to `llm_tool_cli`; local construction and CLI integration MUST remain covered here.
