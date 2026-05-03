# README Documentation

## Goal of the document

This document describes the expected content, structure, and tone of the project `README.md`.

## Scope

The scope of this specification is limited to the repository root `README.md`.

The following topics are out of scope:

- package metadata.
- generated command help.
- detailed CLI behavior.
- detailed configuration syntax.
- development environment rules for agents.
- documentation files other than the root `README.md`.

## Audience

`README.md` MUST be written primarily for humans who are discovering the project.

`README.md` MAY mention coding agents because `depmesh` is designed for agent workflows, but it MUST NOT duplicate the full built-in agent skill documentation.

`README.md` SHOULD help readers quickly understand:

- what problem `depmesh` solves.
- what `depmesh` does.
- how to try the main commands.
- where to find detailed usage and configuration documentation.
- how to work on the project.

## Structure

`README.md` MUST start with a single h1 heading containing the project name.

The first paragraphs after the h1 heading SHOULD explain the core value proposition in plain language.

`README.md` MUST use the following h2 sections in this order:

1. `Example`
2. `Rationale`
3. `Features`
4. `Quick Usage`
5. `Installation`
6. `Configuration`
7. `Specifications`
8. `Development`

The `Example` section MUST be the first h2 section after the introductory paragraphs.

Additional h2 sections MUST NOT be added without updating this specification first. Lower-level subsections MAY be added under the required h2 sections when they help human readers.

`README.md` SHOULD avoid deep implementation details.

## Content Requirements

`README.md` MUST mention that `depmesh` is a CLI tool.

`README.md` MUST explain that `depmesh` discovers dependencies between project artifacts.

`README.md` MUST explain that the project must have a useful `depmesh.toml` configuration for `depmesh` to be useful.

`README.md` MUST link to the configuration behavior specification when describing configuration.

`README.md` MUST mention that this repository uses `depmesh` and that its `depmesh.toml` can be used as a real configuration example.

`README.md` MUST explain how to initialize a starter configuration with `depmesh init`.

`README.md` MUST include installation examples for installing `depmesh` from PyPI with `uv` and `pip`.

`README.md` MUST explain that the generated starter configuration should be edited for the project.

`README.md` MUST mention that a user can ask a coding agent to help fill `depmesh.toml`.

`README.md` MUST include a short `AGENTS.md` instruction snippet that tells agents to use `depmesh`.

`README.md` MUST mention the primary workflows:

- listing relations.
- querying dependencies.
- initializing a starter configuration.
- reading built-in skill-style documentation.

`README.md` MUST include command examples for:

- `depmesh relations`.
- `depmesh dependencies ...`.
- `depmesh init`.
- `depmesh skill usage`.

Human-facing command examples SHOULD use command defaults.

`README.md` MUST point readers to `./specs/` as the source of project behavior and architecture.

`README.md` MUST describe development commands through `./bin/dev.sh`.

## Style

`README.md` SHOULD be concise and practical.

`README.md` SHOULD prefer short explanations, bullet lists, and command examples.

`README.md` SHOULD use a confident but accurate tone.

`README.md` SHOULD avoid promising behavior that is only planned or not implemented.

`README.md` SHOULD not be an exhaustive user manual; detailed command and configuration guidance belongs in built-in skill documentation and specifications.
