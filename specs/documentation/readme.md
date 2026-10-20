# README Documentation

## Goal of the document

This document describes the root README's content, structure, and tone.

## Scope

This specification covers the root `README.md`.
The following are out of scope:

- publishing.
- generated help.
- detailed CLI/configuration syntax.
- agent development rules.
- other documentation.

## Audience

The README MUST primarily address humans discovering Depmesh.
It MAY discuss coding agents but MUST NOT duplicate the full built-in agent skills.
It SHOULD quickly explain:

- the problem and Depmesh's role.
- how to try main commands.
- where to find detailed usage and configuration documentation.
- how to develop the project.

## Source Material

The README MUST reflect current `./specs/` behavior and architecture.
It MAY use `pyproject.toml` for package identity, repository links, and installation context.
Existing prose MUST NOT override conflicting specs or metadata.

## Structure

The README MUST start with one project-name h1, followed by introductory paragraphs that SHOULD explain its value plainly.
These h2 sections MUST follow in order:

1. `Example`
2. `Rationale`
3. `Features`
4. `Quick Usage`
5. `Installation`
6. `Configuration`
7. `Specifications`
8. `Development`

`Example` MUST be the first h2.
`Features` MUST use compact bullets with bold feature names and short descriptions.
Additional h2 sections MUST NOT appear without updating this specification.
Helpful lower-level subsections MAY appear; deep implementation details SHOULD be avoided.

## Content Requirements

The README MUST explain:

- Depmesh is a CLI discovering dependencies between project artifacts.
- Useful results require useful project-specific `depmesh.toml` configuration.
- This repository uses Depmesh; its `depmesh.toml` is a real example.
- `depmesh init` creates starter configuration that should be reviewed and edited.
- Coding agents can help fill `depmesh.toml`.
- `human` is the terminal default; `--protocol llm` is for coding agents.
- Development uses Docker-backed `./bin/dev.sh` and `./bin/dev-tests.sh`.

The README MUST:

- link configuration descriptions to the configuration behavior spec.
- link command descriptions to the CLI behavior spec.
- link detailed-documentation guidance to the skill fixture spec or mention built-in skills.
- identify `./specs/` as the behavior and architecture source.
- include PyPI installation examples with both `uv` and `pip`.
- include a short `AGENTS.md` snippet directing agents to use Depmesh.

It MUST mention and illustrate these primary workflows:

- List relations — command example: `depmesh relations`.
- Query dependencies — command example: `depmesh dependencies ...`.
- Initialize configuration — command example: `depmesh init`.
- Read built-in skills — command example: `depmesh skill usage`.

Human-facing examples SHOULD use command defaults.

## Style

The README SHOULD be:

- concise.
- practical.
- confident.
- accurate.

It SHOULD use short explanations, bullets, and commands.

It SHOULD avoid promises of unimplemented behavior and exhaustive manual content; detailed guidance belongs in skills and specs.
