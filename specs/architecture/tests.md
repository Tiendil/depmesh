# Test architecture

## Goal of the document

This document describes the architecture of project tests, including where tests live, how they relate to modules, and how they cover entities and errors.

## Scope

The scope of this specification is limited to test organization and architectural testing expectations.

The following topics are out of scope:

- exact test framework configuration.
- exact fixture names.
- continuous integration configuration.
- package publishing checks.
- performance benchmarks.

## Dictionary

- `unit test` - a test focused on one module or one small group of closely related functions or entities.
- `integration test` - a test that checks multiple modules through a public boundary such as configuration loading or CLI command execution.
- `fixture` - test data or setup used by one or more tests.
- `behavior example test` - a test that verifies an example or rule from a behavior specification.

## General principles

Tests MUST be written as part of the Python project.

Development-related test execution MUST happen through the project development container commands.

The preferred command form for running tests is:

```bash
./bin/dev.sh uv run -- pytest
```

Tests SHOULD be deterministic for the same repository state and filesystem state.

Tests SHOULD prefer end-to-end coverage through public boundaries when that is practical for the behavior under test.

Tests SHOULD use mocks, stubs, and monkeypatching as little as possible.

Tests SHOULD prefer real project code, temporary files, and explicit fixtures over mocked collaborators.

Tests MUST NOT depend on network access.

Tests MUST NOT depend on user-specific files outside test-created temporary directories.

Tests MUST NOT modify Docker configuration or runtime parameters.

## Test module layout

Each implementation module or submodule SHOULD have corresponding tests under a `tests` submodule owned by the same parent module.

The name of a test file MUST be built from the name of the tested module by adding the `test_` prefix.

The structure of tests SHOULD mirror the implementation structure when that makes ownership clear.

Examples:

- `./depmesh/core/utils.py` -> `./depmesh/core/tests/test_utils.py`
- `./depmesh/domain/entities.py` -> `./depmesh/domain/tests/test_entities.py`
- `./depmesh/workspace/config.py` -> `./depmesh/workspace/tests/test_config.py`

Cross-module integration tests MAY live under the module that owns the public boundary being exercised.

CLI integration tests SHOULD live under `./depmesh/cli/tests/`.

## Test organization

Tests SHOULD be organized around the tested function or tested class.

Each module-level function SHOULD have a corresponding test class.

Each class SHOULD have a corresponding test class.

Test classes MUST use `Test<SubjectName>` naming, where `<SubjectName>` is the tested function or class name converted to PascalCase.

Examples:

- function `build_plugin` -> `class TestBuildPlugin`.
- class `Accumulator` -> `class TestAccumulator`.
- class `Rule` -> `class TestRule`.

Tests for a class MUST group method tests inside the class's test class.

Tests for a class method MUST use this method name format:

```text
test_<method_name>__<test_name>
```

`<method_name>` MUST be the tested method name in snake case.

`<test_name>` MUST describe the execution path or behavior being verified in snake case.

Examples:

- `test_flush_if_time__no_measures`.
- `test_flush_if_time__measures_not_ready`.
- `test_replace_tags__circular_replacement`.

When a test class tests one module-level function, test methods MAY omit the function name and use this format:

```text
test_<test_name>
```

Examples:

- `TestBuildPlugin.test_success`.
- `TestBuildPlugin.test_import_error`.
- `TestBuildPlugin.test_wrong_plugin_type`.

Standalone test functions SHOULD be used only for module-level invariants or file-level checks that do not naturally belong to one tested function or class.

Every possible execution path of a tested function or method MUST have a corresponding test method or parametrized test case.

Execution paths include:

- successful path.
- default-value path.
- empty-input path.
- invalid-input path.
- handled error path.
- warning-producing path.
- branch-specific path.

Tests MUST cover corner cases for each tested function or method.

Corner cases include:

- boundary values.
- empty collections and empty strings.
- missing optional values.
- duplicate values.
- unsupported values.
- malformed input.
- paths that do not exist.
- values that require normalization.
- repeated calls that may reveal state leaks.

## Entity tests

Entity tests SHOULD verify local invariants of entities.

Entity tests SHOULD cover:

- entity-specific Pydantic field validation.
- entity-specific Pydantic model validation.
- normalization behavior owned by the entity.
- entity-specific methods and properties.
- rejection of invalid values that the entity is responsible for rejecting.

Entity tests SHOULD NOT test behavior inherited unchanged from the shared base entity.

Entity tests SHOULD NOT test trivial Pydantic behavior unless the entity customizes that behavior.

Entity tests MUST NOT require filesystem access unless the entity itself explicitly owns path normalization that depends on filesystem semantics.

Entity tests MUST NOT verify CLI rendering.

Entity tests MAY assert `pydantic.ValidationError` for invalid low-level model construction.

## Error tests

Error tests SHOULD verify behavior customized by concrete error classes.

Error tests SHOULD cover:

- custom error codes.
- custom message formatting.
- custom structured details.
- behavior added by an intermediate error class.

Error tests SHOULD NOT test unchanged inheritance from project or module root error classes.

Error tests SHOULD NOT test behavior inherited unchanged from the shared base error class.

Tests for exception boundaries SHOULD verify that expected low-level failures are converted into project-specific errors or warning strings.

Tests for exception boundaries SHOULD verify that `pydantic.ValidationError` from external input is converted into project-specific errors or warning strings.

CLI tests SHOULD verify that fatal errors are mapped to the expected exit code category.

CLI tests SHOULD verify that unmapped project exceptions use the default non-zero exit code.

CLI tests for the automation protocol SHOULD verify that fatal errors are rendered as `error` records when possible.

Warning tests SHOULD verify that non-fatal problems add warning strings to the core warning storage.

Warning tests SHOULD verify that the core warning storage preserves warning insertion order.

Warning tests SHOULD clear the core warning storage before and after tests that use it.

CLI warning tests SHOULD verify that warnings do not cause a non-zero exit code when the command otherwise succeeds.

CLI warning tests SHOULD verify that the CLI clears the core warning storage at the start of each command.

CLI warning tests SHOULD verify that stored warning strings are rendered according to the selected output protocol.

## Behavior coverage

Behavior specifications are the source of expected externally visible behavior.

Tests SHOULD cover the examples in behavior specifications when the corresponding behavior is implemented.

Configuration tests SHOULD cover:

- configuration discovery.
- supported TOML structure.
- relation validation.
- rule validation.
- matcher validation.
- dependency expression validation.
- path normalization.
- invalid configuration failures.

CLI tests SHOULD cover:

- command forms.
- option parsing.
- output protocol selection.
- dependency output grouping and ordering.
- relation filtering.
- reverse queries.
- warnings.
- errors and exit codes.

## Fixtures and temporary data

Tests that need files SHOULD create those files in temporary directories.

Tests SHOULD keep fixture data as small as possible while preserving the behavior being verified.

Inline fixture data SHOULD be preferred for short configuration files and short expected outputs.

Reusable fixture files MAY be added when inline data would obscure the test.

Fixture paths SHOULD use forward slashes in expected normalized identifiers.

Tests that change the current working directory MUST restore it before the test ends.

## Assertions

Tests SHOULD assert structured values before rendered text when structured values are available.

Rendered output tests SHOULD assert exact output only for stable protocol contracts.

Rendered output tests MAY assert selected lines or records when exact text is intentionally outside the relevant specification.

Automation protocol tests SHOULD parse JSON Lines output before asserting record contents.
