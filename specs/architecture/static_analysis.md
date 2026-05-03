# Static analysis architecture

## Goal of the document

This document describes project expectations for autoformatting, linting, spelling checks, type checking, and the allowed ways to fix findings reported by these tools.

## Scope

The scope of this specification is limited to static analysis and polishing work for existing `depmesh` code.

The following topics are out of scope:

- continuous integration workflow structure.
- exact dependency versions.
- release preparation.
- broad refactoring.
- introducing new runtime behavior while fixing static analysis findings.
- changing Docker configuration or development container runtime parameters.

## Dictionary

- `polishing` - a change whose purpose is to satisfy formatting, linting, spelling, type-checking, or test-quality requirements without changing intended behavior.
- `autoformatter` - a tool that rewrites code mechanically according to configured formatting rules.
- `semantic checker` - a tool that reports code-quality, spelling, security, or typing findings that usually require human judgment.
- `suppression` - an inline or configuration-level instruction that disables a static analysis finding.

## General principles

Polishing MUST preserve intended project behavior.

Polishing MUST NOT introduce new features, new user-visible behavior, or broad refactors.

Polishing MUST NOT weaken project static analysis configuration to make findings disappear.

Development-related static analysis operations MUST run through the project development container.

Agents SHOULD prefer fixing the root cause of a finding over suppressing the finding.

Suppressions MUST be narrow. A suppression SHOULD be attached to the smallest expression, line, or file scope that correctly represents the exception.

Suppressions MUST NOT be added for findings the agent does not understand.

When a finding cannot be fixed without changing behavior, changing architecture, or making an uncertain domain decision, the agent MUST ask the developer before applying the change.

## Polishing loop

Polishing SHOULD start with autoformatting before manual lint or type fixes.

The normal autoformatting command is:

```bash
./bin/dev-format.sh
```

The normal formatting check command is:

```bash
./bin/dev-check-formatting.sh
```

The normal semantic static analysis command is:

```bash
./bin/dev-check-semantics.sh
```

After a manual fix for a static analysis finding, the next verification SHOULD restart from autoformatting or the formatting check. This keeps import cleanup, import ordering, and code formatting consistent after each fix.

Autoformatting SHOULD run tools in this conceptual order:

1. remove unused imports and unused variables.
2. sort imports.
3. format code.

Semantic checks SHOULD run after autoformatting is clean.

When spelling checks are part of the configured command set, spelling findings SHOULD be fixed before flake8 and mypy findings.

## Autoformatter findings

Autoformatter changes MAY be applied mechanically when they only remove unused code, sort imports, or reformat code.

If an autoformatter removes a symbol that appears to be required for dynamic behavior, public API compatibility, or side effects, the agent MUST stop and inspect the context before accepting the change.

If an import is kept only for side effects, the code SHOULD make that dependency explicit enough that import cleanup tools do not remove it accidentally.

## Spelling findings

Spelling findings SHOULD be fixed when the intended word is clear from context.

Spelling findings in external names, serialized values, fixture data, command output expectations, URLs, or compatibility strings MUST NOT be changed unless the surrounding behavior explicitly permits the spelling change.

When the spelling checker reports a project-specific term, the preferred fix is to add the term to the appropriate spelling allowlist if such an allowlist exists.

## Flake8 findings

Flake8 findings SHOULD be fixed by making the code clearer, more explicit, or more local.

Commented-out code reported by flake8 MUST be removed unless the comment is part of documented behavior, example text, or fixture data.

An undefined name caused by a missing import SHOULD be fixed by adding the necessary import at the top of the file according to the configured import ordering.

An undefined name not explained by a missing import MUST NOT be guessed. The agent MUST ask the developer or leave the finding reported.

Cognitive complexity findings SHOULD NOT be fixed by broad refactoring during polishing. If the existing behavior is clear and the finding is accepted for the current design, the agent MAY add a narrow `noqa` suppression for the cognitive-complexity code.

Security findings MUST NOT be suppressed unless the code intentionally owns the reported behavior and the suppression is narrow. If the security implication is unclear, the agent MUST ask the developer.

Print-output findings SHOULD be fixed by using the project-owned output or diagnostic mechanism when one exists. Print-output findings in tests MAY be handled according to the test's intent.

## Mypy findings

Mypy findings SHOULD be fixed only when the correct type behavior is clear from code context or stable project architecture.

The agent MAY add missing type annotations when the annotation is directly implied by the implementation.

The agent MAY fix trivial mismatches between an annotation and the value that the code already uses.

The agent MAY add an explicit conversion when the code already implies that conversion and the conversion preserves behavior.

The agent MAY add an assertion that a value is not `None` when the control flow already guarantees that condition and the assertion makes the guarantee explicit.

The agent MUST NOT introduce new domain types, protocols, or architectural abstractions only to satisfy mypy during polishing.

The agent MUST NOT add or remove class attributes only to satisfy mypy unless the requested task is specifically about changing that class contract.

The agent MUST NOT add `type: ignore[import-untyped]` for missing third-party type information. The agent SHOULD ask the developer whether to install missing type stubs or handle the dependency another way.

`type: ignore` comments MUST include an explicit error code when mypy supports one for the finding.

## Verification

After polishing, the agent SHOULD run the smallest relevant tests for touched behavior when code was changed.

When only specifications, documentation, or static analysis configuration were changed, tests MAY be skipped if there is no runtime behavior to verify.

If a static analysis command still fails after the allowed fixes are applied, the remaining findings MUST be reported to the developer with enough detail to decide the next action.
