# depmesh

`depmesh` is a CLI tool for making relationships between project files and artifacts an explicit part of your architecture.

Instead of leaving coding agents to infer context from filenames, source code, search results, or embeddings, define those relationships explicitly in `depmesh.toml`: tests that verify a module, specifications that govern it, artifacts affected by a document, import chains, or any project-specific relation that matters to development.

Agents and developers can then query those relations through a single stable interface to find related artifacts, inspect change impact, locate tests or specifications, and follow the project structure in a unified, deterministic way. So no dependency, no constraint, and no project-specific convention is forgotten or overlooked.

## Example

Before changing a CLI module, ask `depmesh` for the specifications and tests connected to it:

The human protocol is the default:

```bash
depmesh dependencies -r governed_by -r tested_by @/depmesh/cli/application.py
```

```text
relation: governed_by

Specifications that apply to the artifact.

- @/specs/architecture/entities.md
- @/specs/architecture/errors.md
- @/specs/architecture/modules_layout.md
- @/specs/architecture/naming.md
- @/specs/architecture/tests.md
- @/specs/behavior/cli.md

relation: tested_by

Tests that verify the artifact.

- @/depmesh/cli/tests/test_application.py

```

For more structured output, use `depmesh -p llm dependencies ...` or `depmesh -p automation dependencies ...`.

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

- **Unified queries** — One interface for discovering project dependencies.
- **Configurable discovery** — Use path patterns, fixed lists, CLI commands, or project-specific scripts behind the scenes.

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

Query several artifacts together:

```bash
depmesh dependencies @/src/app.py @/src/service.py
```

Results are merged across inputs, deduplicated within each relation, and sorted by relation and dependency.
Run separate queries when you need to know which input produced each dependency.

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

The [CLI specification](./specs/behavior/cli.md) describes the complete command interface.

### Output protocols

Select the output protocol with the global `-p` option before the subcommand:

- `human` — Compact terminal text for people.
- `llm` — Framed cells for coding agents.
- `automation` — JSON Lines for programs.

For example:

```bash
depmesh -p llm dependencies @/src/app.py
```

Without `-p`, `skill` uses `llm` and other commands use `human`.
Human and LLM dependency output groups paths by relation; automation emits one record per dependency.

Ordinary results appear after successful command completion.
Warnings appear after results or reported errors.
Expected failures discard pending results and exit nonzero.
All output cells, including errors, go to stdout; framework argument-parsing diagnostics may still use stderr.

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

Without `--config`, Depmesh searches upward from the current working directory for `depmesh.toml`.
The directory containing the selected file is the project root.
Use a global `--config PATH` to select a file explicitly:

```bash
depmesh --config /path/to/project/depmesh.toml relations
```

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

Configured relative paths and patterns use the configuration directory as their base; relative CLI artifact paths use the invocation's current working directory.
Prefer root-anchored paths such as `@/src/app.py` when a reference should be independent of the current directory.

Run `depmesh skill configuration` for the agent-oriented configuration guide.

For the full configuration contract, see [the configuration specification](./specs/behavior/config.md).

## Specifications

Project behavior and architecture are specified in [./specs](./specs). Start with [./specs/intro.md](./specs/intro.md) when looking for the source of truth.

## Development

Development commands run through Docker:

```bash
./bin/dev-tests.sh
./bin/dev.sh uv run -- depmesh relations
```

Build development containers only after approved Docker or dependency changes:

```bash
./bin/dev-build-containers.sh
```
