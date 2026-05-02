# Error architecture

## Goal of the document

This document describes how project modules represent fatal errors and warnings, and how those values move from lower layers to the CLI.

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
- `module root error` - the `Error` exception class in a module's `errors` submodule; it is the root for fatal errors owned by that module.
- `exception boundary` - a module boundary where low-level exceptions are converted into project-specific exceptions or warnings.

## General principles

Fatal errors MUST be represented with project-specific exceptions before they cross module boundaries.

Non-fatal problems MUST be represented as warning strings, not as exceptions, when processing can continue and produce useful output.

Lower-level modules MUST NOT print errors, print warnings, write JSON Lines records, or terminate the process.

The CLI layer MUST be responsible for converting project errors and warnings into:

- exit codes.
- stderr messages.
- output protocol records.

Project-specific exceptions MUST expose stable error codes.

Error codes MUST use lowercase ASCII letters, ASCII digits, and `_`.

User-facing messages SHOULD be clear enough to diagnose the problem without exposing implementation stack details.

## Error ownership

Each module MAY define an `errors` submodule for errors owned by that module.

Shared base error types MUST be owned by a common lower-level module that does not depend on CLI behavior.

Module-specific error types MUST be defined in the module that can add the most useful context.

Production errors MUST NOT be defined in test modules.

Test-only error classes MAY be defined in test modules when they are required to verify error handling behavior.

## Error hierarchy

The project MUST define a single project root exception type for all expected fatal project errors.

The project root exception MUST be named `Error`.

The project root exception MUST inherit from `Exception`.

The project root exception MUST NOT inherit from Pydantic model classes.

The project root exception MUST be owned by the core module.

Each module that defines fatal errors SHOULD define one module root error class.

The module root error class MUST be named `Error`.

All fatal errors owned by that module MUST inherit from the module root error class.

A module root error class MUST inherit from the project root exception or from a parent module's root error class.

A module SHOULD NOT define multiple root error classes.

Modules outside the CLI module MUST NOT know about CLI exit codes.

Module root error classes SHOULD be abstract classification classes and SHOULD NOT be raised directly when a more specific concrete error is available.

Intermediate abstract error classes MAY exist under a module root when a module needs a narrower ownership boundary.

The hierarchy SHOULD keep module-specific root errors under the single project root exception.

Concrete error class names MAY differ, but project and module root error classes MUST be named `Error`.

## Exception data

Project-specific exceptions SHOULD carry:

- an error code.
- a human-readable message.
- optional structured details.
- an optional original cause.

Structured details MUST contain values that can be rendered deterministically.

Structured details SHOULD use strings, numbers, booleans, `None`, lists, and dictionaries when they need to be serialized by the CLI.

Exceptions MUST NOT require callers to parse their message text to understand the error category.

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

Modules that create Pydantic entities from external input MUST convert `pydantic.ValidationError` into project-specific errors or warning strings at the nearest exception boundary with useful context.

Pydantic validation errors MAY be used directly inside tests for low-level entity validation.

## Exception boundaries

Modules that call external systems MUST convert relevant low-level failures into project-specific errors or warning strings at the boundary where context is still available.

External systems include:

- filesystem operations.
- TOML parsing.
- Pydantic model validation for external input.
- regular expression compilation.
- shell command execution.

Unexpected programming errors MAY propagate during development, but code that handles expected user or environment failures MUST convert them into project-specific errors.

When converting an exception, the original exception SHOULD be preserved as the cause when it helps debugging.

## CLI mapping

The CLI MUST map fatal project errors to the exit code categories specified by the CLI behavior specification.

The CLI module MUST own the mapping from exception classes to exit codes.

The CLI mapping SHOULD be defined in the CLI module.

The CLI mapping MAY map specific module root error classes to specific exit codes.

The CLI mapping MAY map specific concrete error classes to specific exit codes when a module root is too broad.

The CLI mapping MUST define a default non-zero exit code for project exceptions that are not explicitly mapped.

The CLI SHOULD choose the most specific non-zero exit code that matches the failure.

The CLI MUST NOT return a non-zero exit code only because warnings were produced.

When a fatal error is rendered for the automation protocol, the `error` record MUST use the project error code.

When a warning is rendered for the automation protocol, the `warning` record MUST include the warning string as the `message` field.

Human and LLM protocols SHOULD render warnings in the output and fatal errors outside the requested output.
