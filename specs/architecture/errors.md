# Error architecture

## Goal of the document

This document describes the architecture of failure handling.

## Scope

This specification covers Python error/warning architecture.
The following are out of scope:

- exact messages.
- code inventories.
- terminal formatting.
- discovery algorithms.
- coverage requirements.

## Dictionary

- `fatal error` — prevents successful command completion.
- `non-fatal problem` — permits useful requested output.
- `error code` — a machine-readable fatal-error identifier.
- `module error category` — an `errors` model classifying its module's expected failures.
- `exception boundary` — converts known low-level failures to returned errors or warnings.

## General principles

Expected failures MUST cross boundaries as shared `Result[T]` environment-error values, except predicate matching as described below.
Depmesh MUST use `llm_tool_cli` results/error foundations and preserve shared errors unless translation adds domain meaning or recovery.
Package ownership alone MUST NOT trigger translation; raised shared exceptions MUST NOT become expected failures.
Internal errors MUST be raised and MUST NOT become cells in normal CLI handling.

Predicate matching is exempt from result conversion: it MUST return captures or `None`, MAY raise evaluation failures, and composites MUST propagate failures rather than treating them as non-matches.
Result-returning callers MUST recover helper error values within their propagation scope; unrelated matching exceptions MAY propagate unchanged.

Non-fatal problems MUST use warning cells submitted to scoped output, both provided by `llm_tool_cli`.
Lower modules MUST NOT print diagnostics/JSON Lines or terminate.
The CLI MUST own fatal-error protocol delivery and shared exit-based termination.

Errors MUST expose machine-readable codes identifying failure kinds independently of message text.
Project codes MUST use lowercase ASCII letters, ASCII digits, and `_`; adopted shared codes MUST retain native spelling.
Messages SHOULD diagnose problems without stack details.

## Error ownership

Depmesh bases MUST belong to `depmesh.core.errors`.
Shared errors MUST retain their:

- hierarchy.
- codes.
- messages.
- records.

Top-level error owners SHOULD define `errors` hierarchies with an `InternalError` root inheriting Depmesh's core internal base and an `EnvironmentError` root inheriting Depmesh's core environment base.
Category roots MUST explicitly use `EnvironmentError`/`InternalError`, not an ambiguous `Error` or boundary-only name.
Specific errors MUST belong where useful context can be added.
Unique cases SHOULD have subclasses.
Owners MUST export `errors` from their package initializer.
Production errors MUST NOT live in tests; test-only errors MAY verify handling.

## Error models and internal exceptions

Depmesh's environment-error base MUST inherit shared `EnvironmentError`, identify Depmesh-owned failures for policy, and inherit the shared default exit status without overriding it.
Errors MUST remain presentation-independent Pydantic models, define `code`/`message`, and MUST NOT inherit `Exception`.
They MAY add guidance and typed context.
Leaf classes SHOULD declare messages/guidance; call sites SHOULD supply only varying context.
Messages and guidance MAY use `{error.<field>}` formatting.
Diagnostic data MUST follow the shared contract in `specs/architecture/errors.md` in `llm-tool-cli`.
Core error bases MUST NOT depend on cells, formatters, or CLI output.

Project technical exceptions MUST inherit `depmesh.core.errors.InternalError`, itself inheriting `llm_tool_cli.core.errors.InternalError`.
They MUST NOT become environment errors merely through common ancestry or dependency origin.
Models and exceptions MUST remain separate.
Internal errors MUST NOT provide environment codes or diagnostic serialization.

## Results

Fallible functions SHOULD return `Result[T]`; failures MUST use shared `EnvironmentErrors`, which MAY mix shared/Depmesh values.
Success MUST use `Ok(value)`; failure MUST use `Err(errors)`.
Independent validation failures SHOULD be collected in one result.
Compatible propagation SHOULD preserve the original result/list without rewrapping.
Functions SHOULD NOT be duplicated solely by handling strategy.
Changing a function to return errors MUST update callers to handle/propagate/render according to their layer.

## Callback boundaries

Fallible callbacks/interchangeable components MUST expose result-aware interfaces.
Framework callbacks MAY adapt results when ordinary values/control-flow exceptions are required.
Pydantic validators MAY raise required validation exceptions internally; external-input boundaries MUST convert resulting failures to returned errors.

## `unwrap_to_error`

For simpler composition of result-returning functions, `unwrap_to_error` SHOULD be preferred over repeated manual failure checks, particularly for functions mainly composing other results.
Decorated functions MAY unwrap intermediate values.
The decorator MUST convert `UnwrapError` back to `Err` with its payload and MUST NOT hide internal/arbitrary exceptions.
Propagation unwraps MUST execute inside a recovery scope, including those in deferred iterators and callbacks.
Creating an iterator or callback inside that scope MUST NOT substitute for executing its fallible work there.
An unguarded failed unwrap is an internal error.

## Warnings

Warnings MUST represent only non-fatal problems allowing useful output.
They MUST NOT represent:

- invalid arguments.
- unloadable configuration.
- dependency query failures preventing valid results.

They MUST use warning cells and scoped delivery provided by `llm_tool_cli`, buffered until finalization after results or reported errors.

Examples include unresolvable files patterns and command-source stderr or non-zero exits when usable dependencies remain available.

## Pydantic validation errors

Raw external-input Pydantic errors MUST NOT cross high-level boundaries.
The nearest useful boundary MUST convert `pydantic.ValidationError` into returned errors or warning cells; shared loading MAY own conversion.
Low-level entity tests MAY assert Pydantic errors directly.

## Exception boundaries

External-system callers MUST convert relevant known failures at useful boundaries, including:

- filesystem operations.
- TOML parsing.
- external-input model validation.
- regex compilation.
- shell execution.

Expected raw filesystem/parser/validation failures MUST NOT escape high-level boundaries.
Unexpected bugs MUST remain exceptions; blanket conversion MUST NOT hide them.
Translation SHOULD add application meaning or recovery and SHOULD retain useful private causes.

## CLI mapping

`llm_tool_cli` MUST own skill failures and protocol-option validation/diagnostics.
Before result-based execution, Typer parsing MAY use standard invalid-argument behavior, including `typer.BadParameter`, `click.UsageError`, or `typer.Exit`.

After protocol installation, command handling provided by `llm_tool_cli` MUST own every environment error's:

- order.
- presentation.
- stdout delivery.
- exit.

Depmesh MUST NOT maintain another error-rendering/exit path.
Errors MUST remain typed shared cells until shared projection of content/guidance/metadata.
Shared error handling MUST NOT submit journal records or require workspace setup.
Non-CLI errors MAY declare shared-core exit overrides; termination MUST remain at the shared CLI boundary.

## Naming error classes

Names SHOULD be short/descriptive.
When clear, leaf names SHOULD omit these redundant suffixes:

- `Error`.
- `Exception`.
- `Failure`.
- `Internal`.
- `Environment`.

Roots MUST retain the explicit categories required above.

## Asserts

Assertions MAY aid typing/lint when prior flow guarantees invariants.
They MUST NOT validate external input or handle recoverable query failures, which MUST use environment errors.
Impossible states needing explicit handling SHOULD use internal errors.

## Other exception types

Production SHOULD use `InternalError` unless Python/third-party protocols require alternatives.
Such interfaces, Pydantic validators, and Typer/click parsing MAY use required exception types.
Shared technical result exceptions MAY implement controlled propagation but MUST NOT be mistaken for environment-error values.
Temporary `NotImplementedError` MAY appear during implementation and SHOULD be replaced before completion with implemented behavior or project internal errors.
