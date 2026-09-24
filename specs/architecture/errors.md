# Error architecture

## Goal of the document

This document describes how project modules represent fatal errors and warnings, and how those values move from lower layers to the CLI, separating expected operational failures from internal exceptions.

## Scope

The scope of this specification is limited to error and warning architecture inside the Python implementation.

The following topics are out of scope:

- exact wording of user-facing messages.
- complete lists of future error codes.
- terminal formatting.
- dependency discovery algorithms.
- test coverage requirements.

## Dictionary

- `fatal error` - a problem that prevents the requested command from completing successfully.
- `non-fatal problem` - a problem discovered while processing a command that does not prevent the command from producing useful output.
- `error code` - a stable machine-readable identifier for a fatal error.
- `module error category` - an environment-error model in a module's `errors` submodule that classifies expected failures owned by that module.
- `exception boundary` - a module boundary where known low-level failures are converted into returned environment errors or warnings.

## General principles

Expected fatal failures MUST be represented as shared `EnvironmentError` values returned through `Result[T, EnvironmentErrors]` before they cross module boundaries.

Project modules MUST use `Result`, `Ok`, `Err`, `EnvironmentError`, and `EnvironmentErrors` from `llm_tool_cli` directly. Project-local result implementations or compatibility re-exports MUST NOT duplicate them.

Documented public environment errors from `llm_tool_cli` are part of the application error contract and MUST propagate as returned values without translation solely because of their package ownership.

Operations with expected failures MUST return a result. Operations without expected failures SHOULD keep their ordinary return values. Successful absence, a predicate that does not match, and a warning with useful output MUST NOT become fatal errors merely to fit the result interface.

Predicate matching and propagation of its evaluation exceptions are exempt from this specification's result-conversion requirements. Matching MUST return captures for a match or `None` for a non-match, and MAY raise evaluation failures. Composite predicates MUST propagate those failures without treating them as non-matches. Result-returning callers MUST recover error values from result-based helpers within their existing propagation scope; unrelated matching exceptions MAY propagate unchanged.

Non-fatal problems MUST be represented as warning strings, not as exceptions, when processing can continue and produce useful output.

Lower-level modules MUST NOT print errors, print warnings, write JSON Lines records, or terminate the process.

The CLI layer MUST be responsible for converting project errors and warnings into:

- exit codes.
- stderr messages.
- output protocol records.

Environment errors MUST expose stable error codes.

Project-owned error codes MUST use lowercase ASCII letters, ASCII digits, and `_`. Adopted shared error codes MUST retain their native spelling.

User-facing messages SHOULD be clear enough to diagnose the problem without exposing implementation stack details.

## Error ownership

Each module MAY define an `errors` submodule for errors owned by that module.

Shared base result and error types MUST be owned by a common lower-level module that does not depend on CLI behavior.

Module-specific error types MUST be defined in the module that can add the most useful context.

Production errors MUST NOT be defined in test modules.

Test-only error classes MAY be defined in test modules when they are required to verify error handling behavior.

## Error models and internal exceptions

Expected operational errors MUST be Pydantic models inheriting from the shared `EnvironmentError`, not exceptions.

Environment errors MUST carry a stable code and message, and MAY include corrective guidance and typed context fields owned by the concrete error.

A module MAY define an environment-error classification model when callers need to distinguish that module's failures. Environment-error categories MUST NOT encode CLI exit codes.

Internal and technical exceptions defined by the project MUST inherit from the project's core `InternalError`, which inherits from the shared exception `InternalError`.

Internal exceptions MUST NOT be converted into environment errors merely because they share a base class or originate in a dependency.

Environment-error model definitions and internal exception definitions MUST remain distinct. Category roots MUST explicitly use `EnvironmentError` or `InternalError` names instead of an ambiguous `Error` root. Internal exceptions MUST NOT provide environment-error codes or diagnostic-record serialization.

## Result propagation

A successful result MUST contain the requested value. A failed result MUST contain a non-empty `EnvironmentErrors` in diagnostic order.

The project MUST preserve returned error values when propagation does not add application-specific meaning or implement recovery.

Fallible callbacks and interchangeable components MUST expose result-aware interfaces so expected errors can reach their callers.

Framework callbacks that require ordinary return values or framework control-flow exceptions MAY adapt results at that framework boundary.

Pydantic validators MAY raise validation exceptions required by Pydantic internally; the external-input boundary MUST convert the resulting validation failure into a returned environment error.

The shared propagation decorator MAY translate its own result-unwrapping exception into a failed result within the decorated call. The CLI command boundary MAY recover environment errors from that same propagation exception for rendering and exit-code selection. Result unwrapping for propagation MUST stay inside one of these scopes; deferred iterators and callbacks MUST NOT let the unwrapping exception escape it.

An unguarded unwrap of a failed result outside a propagation scope is an internal error, not an expected operational failure.

## Error data

Environment-error context MUST use typed fields that can be rendered deterministically.

Error records MUST preserve native codes, formatted messages, and structured context. Callers MUST NOT parse message text to determine the error category.

Known low-level exceptions SHOULD be retained as private causes when useful for debugging. Causes MUST NOT become serialized diagnostic fields.

## Warnings

Warnings represent non-fatal problems discovered while processing a request.

Warnings MUST be used only when processing can continue and the command can still produce useful requested output.

Warnings MUST NOT be used for invalid command line arguments, invalid configuration that prevents loading, or dependency query failures that prevent producing a valid query result.

Warnings are plain strings stored in the core warning storage.

Warnings are not exceptions, Pydantic entities, or Python `warnings` module warnings.

The core module MUST provide singleton warning storage.

The core warning storage MUST be accessible to all project modules.

The core warning storage MUST store warnings as strings.

The core warning storage MUST preserve warning insertion order.

The core warning storage MUST provide operations to:

- add a warning string.
- read currently stored warning strings.
- clear stored warning strings.

Code that adds warnings SHOULD include enough context in the string for the CLI output to be useful.

The CLI MUST clear the core warning storage at the start of each command.

The CLI MUST read the core warning storage when rendering command output.

The CLI MUST render stored warnings according to the selected output protocol.

Examples of warning-producing situations include:

- a files source pattern that cannot be resolved inside the project.
- a command source that writes stderr output but still produces usable dependencies.
- a command source that exits with a non-zero status when other artifact sources can still produce useful output.

## Pydantic validation errors

Pydantic validation errors MUST NOT be exposed directly across high-level module boundaries for user-provided data.

Modules that create Pydantic entities from external input MUST convert `pydantic.ValidationError` into returned environment errors or warning strings at the nearest exception boundary with useful context. Shared configuration loading MAY own this conversion.

Pydantic validation errors MAY be used directly inside tests for low-level entity validation.

## Exception boundaries

Modules that call external systems MUST convert relevant low-level failures into returned environment errors or warning strings at the boundary where context is still available.

External systems include:

- filesystem operations.
- TOML parsing.
- Pydantic model validation for external input.
- regular expression compilation.
- shell command execution.

Unexpected programming errors MUST remain exceptions. Code that handles expected user or environment failures MUST convert only the relevant known failures into returned environment errors.

Raw filesystem, parser, or validation exceptions representing expected failures MUST NOT cross high-level boundaries unchanged. Blanket exception-to-result conversion MUST NOT hide programming errors.

Translation of an expected error SHOULD occur only when it adds application-specific meaning or implements recovery.

When converting an exception, the original exception SHOULD be preserved as the environment error's cause when it helps debugging.

## CLI mapping

The CLI MUST explicitly handle failed results and map their environment errors to the exit code categories specified by the CLI behavior specification.

Failure rendering and exit-code selection MUST be centralized at the CLI command boundary.

The CLI module MUST own the mapping from environment-error categories to exit codes.

The CLI mapping SHOULD be defined in the CLI module.

The CLI mapping MAY map specific module error categories to specific exit codes.

The CLI mapping MAY map specific concrete environment errors to specific exit codes when a category is too broad.

The CLI mapping MUST define a default non-zero exit code for environment errors that are not explicitly mapped.

The CLI MUST render every error in a failed result in list order. The first error MUST determine the exit category. Technical exceptions MUST NOT be rendered as expected environment errors.

Shared configuration errors MUST use the configuration exit category.

The CLI SHOULD choose the most specific non-zero exit code that matches the failure.

The CLI MUST NOT return a non-zero exit code only because warnings were produced.

When a fatal error is rendered for the automation protocol, the `error` record MUST use the error's native code, message, and structured fields. Adopted shared errors MUST NOT be remapped to legacy project diagnostics.

When a warning is rendered for the automation protocol, the `warning` record MUST include the warning string as the `message` field.

Human and LLM protocols SHOULD render warnings in the output and fatal errors outside the requested output.
