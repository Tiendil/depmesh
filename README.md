# depmesh

`depmesh` is a CLI tool that helps agents and developers investigate how project artifacts depend on each other.

Use it to explore a codebase, find related files, inspect the impact of a possible change, locate tests or specifications, and follow project-specific relationships that are hard to remember or discover manually.

`depmesh` gives one stable interface for navigating dependency relationships, while each project decides how dependencies are discovered exactly: path patterns, fixed lists, filesystem searches, static-analysis commands, or project-specific scripts.

## Example

Before changing a CLI module, ask `depmesh` for the specifications and tests connected to it:

```bash
> depmesh dependencies --relation governed_by --relation tested_by ./depmesh/cli/application.py

governed_by:
  ./specs/architecture/entities.md
  ./specs/architecture/errors.md
  ./specs/architecture/modules_layout.md
  ./specs/architecture/naming.md
  ./specs/architecture/tests.md
  ./specs/behavior/cli.md

tested_by:
  ./depmesh/cli/tests/test_application.py
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
- `imports` — Python files imported by a Python file.
- `imported_by` — Python files that import a Python file.

## Features

`depmesh` has one single goal — **provide a consistent deterministic interface for discovering project dependencies.**

- You decide which relations are useful and how they are discovered.
- `depmesh` gives you and your agents a consistent interface to query them regardless of how they are extracted under the hood.

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
input = { type = "glob", pattern = "./src/{*module}.py" }
output = { type = "files", pattern = "./tests/test_{module}.py" }
```

This defines one relation named `tested_by`. The rule matches source files like `./src/app.py`, captures `app` as `module`, and looks for `./tests/test_app.py` as the dependency.

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
