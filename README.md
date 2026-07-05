# depmesh

`depmesh` is a CLI tool for making relationships between project files and artifacts an explicit part of your architecture.

Instead of leaving coding agents to infer context from filenames, source code, search results, or embeddings, define those relationships explicitly in `depmesh.toml`: tests that verify a module, specifications that govern it, artifacts affected by a document, import chains, or any project-specific relation that matters to development.

Agents and developers can then query those relations through a single stable interface to find related artifacts, inspect change impact, locate tests or specifications, and follow the project structure in a unified, deterministic way. So no dependency, no constraint, and no project-specific convention is forgotten or overlooked.

## Example

Before changing a CLI module, ask `depmesh` for the specifications and tests connected to it:

```bash
> depmesh -p llm dependencies -r governed_by -r tested_by ./depmesh/cli/application.py

## governed_by

Specifications that apply to the artifact.

- @/specs/architecture/entities.md
- @/specs/architecture/errors.md
- @/specs/architecture/modules_layout.md
- @/specs/architecture/naming.md
- @/specs/architecture/static_analysis.md
- @/specs/architecture/tests.md
- @/specs/behavior/cli.md
- @/specs/behavior/file_paths.md

## tested_by

Tests that verify the artifact.

- @/depmesh/cli/tests/test_application.py

```

## Rationale

Coding agents often need to answer practical questions before editing:

- Which tests should be read before changing this file?
- Which specifications govern this module?
- Which files import this shared helper?
- Which artifacts are affected by this specification change?

`depmesh` answers those questions through configured relations.

For example, a project can define relations such as:

- `tested_by` — tests that verify an artifact.
- `governed_by` — specifications that apply to an artifact.
- `imports` — Python files imported by an artifact.
- `imported_by` — Python files that import an artifact.

## Features

- Unified interface for discovering project dependencies.
- Configurable ways to detect dependencies behind the scenes: path patterns, fixed lists, calling CLI commands, or running project-specific scripts.

## Quick Usage

List available relations first:

```bash
depmesh relations
```

Query dependencies for an artifact:

```bash
depmesh dependencies ./src/app.py
```

Query selected relations:

```bash
depmesh dependencies --relation governed_by --relation tested_by ./src/app.py
```

Initialize a starter configuration:

```bash
depmesh init
```

Read detailed agent-oriented usage:

```bash
depmesh skill usage
```

Other built-in docs:

```bash
depmesh skill configuration
depmesh skill initialization
```

## Installation

Install `depmesh` from PyPI in the environment where your agent or tools run:

```bash
uv tool install depmesh

# or
pip install depmesh
```

Then initialize a starter configuration in the project root:

```bash
depmesh init
```

The starter `depmesh.toml` is valid, but it is only a starting point. Edit it so it describes the dependency relations that matter in your project.

Tell agents to use `depmesh` by adding a short note to `AGENTS.md`:

```markdown
Use `depmesh` to discover dependencies between project artifacts.
Agents MUST use `depmesh` for dependency types supported by its configuration.
At the start of each work session, run `depmesh skill usage`.
```

You can ask a coding agent to help fill the configuration. A good prompt is:

```text
Inspect this project and update depmesh.toml with useful dependency relations.
Start by reading output of `depmesh skill initialization` and `depmesh skill configuration`.
```

This repository uses `depmesh` for its own dependency mapping. See [depmesh.toml](./depmesh.toml) for a real configuration example.

## Configuration

`depmesh` is useful only when the project has a meaningful `depmesh.toml`.

The configuration declares:

- relations that can be queried.
- rules that match queried artifacts.
- sources that produce dependency artifacts.

Minimal relation example:

```toml
version = 1

[[relations]]
id = "tested_by"
description = "Tests that verify the artifact."

[[rules]]
relation = "tested_by"
input = { type = "glob", pattern = "./src/{**package_path}/{*module}.py" }
output = { type = "files", pattern = "./src/{package_path}/tests/test_{module}.py" }
```

This defines one relation named `tested_by`. The rule matches source files like `./src/cli/app.py`, captures `cli` as `package_path` and `app` as `module`, and looks for `./src/cli/tests/test_app.py` as the dependency.

Run `depmesh skill configuration` for the agent-oriented configuration guide.

For the full configuration contract, see [the configuration specification](./specs/behavior/config.md).

## Specifications

Project behavior and architecture are specified in [./specs](./specs). Start with [./specs/intro.md](./specs/intro.md) when looking for the source of truth.

## Development

Development commands run through Docker:

```bash
./bin/dev.sh uv run -- pytest
./bin/dev.sh uv run -- depmesh relations
```

Build development containers only after approved Docker or dependency changes:

```bash
./bin/dev-build-containers.sh
```
