# Skill Fixtures

## Goal of the document

This document describes packaged Markdown documentation printed by `depmesh skill`.

## Scope

This specification covers built-in skill fixtures.
The following are out of scope:

- exact prose.
- CLI parsing.
- rendering.
- configuration semantics beyond examples.
- external agent-skill installation.

## Availability

Built-in skill documentation MUST be included in the installed distribution and be available without project configuration.

## Fixture set

Every document offered by the skill command MUST have packaged Markdown content.
Required document names MUST follow `specs/behavior/cli.md`; their content requirements follow below.
Each fixture MUST start with one h1 identifying Depmesh and the document's subject.

## Usage fixture

Usage MUST describe:

- command invocation/output and protocols.
- root discovery and `--config`.
- root-anchored project artifact ids.
- access to other skills.

It MUST NOT describe configuration syntax beyond documentation commands or tell agents when/why to use Depmesh; that decision belongs to the user/workflow.

## Configuration fixture

Configuration MUST describe `depmesh.toml` and its project-root meaning, using schema-compatible examples.
It SHOULD illustrate:

- minimal and generated starter configurations.
- relations.
- rules.
- predicates.
- sources.
- captures/templates.
- directional reverse relations.

It SHOULD explain command-based validation of configuration changes.

## Initialization fixture

Initialization MUST explain:

- `depmesh init`.
- no overwrite.
- `--config` target/root selection.
- configuration-only creation.

It SHOULD guide starter review/filling and validation using current commands.
It SHOULD provide rule-writing heuristics and descriptions focused on returned artifacts and the queried source's role.
`artifact` SHOULD be the default source term unless returned dependencies are called artifacts, requiring a more specific source role.
Examples SHOULD include governance, static Python imports, and predictable test mapping.

## Style

Fixtures MUST be self-contained tool documentation, without requiring source/spec inspection for usage.
They SHOULD use concise Markdown, prefer implemented stable behavior, and use `depmesh -p llm ...` for agent-facing commands.
Examples SHOULD cover:

- commands.
- TOML.
- output.
