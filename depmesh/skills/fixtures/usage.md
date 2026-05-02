# `depmesh` Usage

`depmesh` is a command line interface for discovering configured dependency relations between project artifacts.

It hides the project-specific discovery mechanism behind one interface. A relation may be backed by path templates, fixed lists, file searches, static-analysis commands, or other configured sources, but the command usage stays the same.

An artifact is usually a project-relative path such as `./src/app.py`. Treat artifact ids as strings accepted by the current project's `depmesh.toml`.

`depmesh` is useful only when the project has a proper `depmesh.toml` configuration. If configuration is missing or relation coverage looks incomplete, read `depmesh -p llm skill initialization` and `depmesh -p llm skill configuration`.

## Project Root

When `--config` is not provided, `depmesh` searches from the current working directory upward until it finds `depmesh.toml`. The directory containing that file is the project root for the command.

When `--config PATH` is provided, `depmesh` uses that file directly, and the directory containing it is the project root.

The project root matters because relative artifact paths, glob patterns, file sources, and command sources are interpreted from that root. Run commands from inside the intended project, and prefer project-relative artifact paths such as `./src/app.py`.

## This Documentation

This output is built-in skill-style documentation printed by `depmesh -p llm skill usage`.

Use it as the first reference for command usage in a session. Use the other built-in skill documents for narrower tasks:

- `depmesh -p llm skill configuration` explains `depmesh.toml` syntax and rule shapes.
- `depmesh -p llm skill initialization` explains `depmesh init`, starter configuration, and heuristics for filling useful rules.
- `depmesh -p llm skill usage` prints this document.

## Usage Patterns

1. List configured relations.

Always do this as the first step in a session or before relying on a relation name:

```bash
depmesh -p llm relations
```

The relation list tells you which dependency types exist in the current project and what each query returns.

Example output:

```text
## governed_by

Specifications that apply to the artifact.

## tested_by

Tests that verify the artifact.
```

2. Prepare to change a source file.

Query dependencies for that file to see what other files may be affected and should be read first:

```bash
depmesh -p llm dependencies ./src/app.py
```

If the relation list includes tests, specs, imports, or reverse imports, combine relation filters to focus the result:

```bash
depmesh -p llm dependencies --relation tested_by --relation governed_by --relation imported_by ./src/app.py
```

Example output:

```text
## governed_by

- ./specs/behavior/app.md

## imported_by

- ./src/main.py

## tested_by

- ./tests/test_app.py
```

3. Add a new module.

Inspect relation names first, then query a nearby module with the same expected placement. This can reveal governing specifications and test locations to mirror:

```bash
depmesh -p llm relations
depmesh -p llm dependencies --relation governed_by --relation tested_by ./src/existing_module.py
```

Example output:

```text
## governed_by

- ./specs/architecture/modules.md

## tested_by

- ./tests/test_existing_module.py
```

4. Change a specification.

Use a reverse governance relation to find implementation files governed by it:

```bash
depmesh -p llm dependencies --relation governs ./specs/behavior/config.md
```

Example output:

```text
## governs

- ./src/config.py
- ./src/config_loader.py
```

5. Change shared code.

Combine reverse lookup relations to identify callers and tests:

```bash
depmesh -p llm dependencies --relation imported_by --relation tested_by ./src/shared.py
```

Example output:

```text
## imported_by

- ./src/app.py
- ./src/service.py

## tested_by

- ./tests/test_shared.py
```

6. Edit several artifacts together.

Query them in one command to get a merged dependency set:

```bash
depmesh -p llm dependencies ./src/app.py ./src/service.py
```

Example output:

```text
## tested_by

- ./tests/test_app.py
- ./tests/test_service.py
```

Run separate queries when you need to know which requested artifact produced each dependency.

## Output Protocols

Use `llm` when invoking `depmesh` as a coding agent. It is the normal choice for this documentation's examples.

Use `human` for compact terminal inspection by a person.

Use `automation` only when another program consumes the command output directly.

Use full command names in agent workflows and generated notes. Short forms are human convenience aliases for interactive terminal use:

- `deps` is an alias for `dependencies`.
- `rels` is an alias for `relations`.

Global options go before the subcommand:

```bash
depmesh -p llm dependencies ./src/app.py
```

## List Relations

List configured relation ids and descriptions:

```bash
depmesh -p llm relations
```

Human convenience alias:

```bash
depmesh rels
```

Example output:

```text
## imports

Python files imported by the Python file.

## tests

Tests that verify the artifact.
```

Use relation ids from this output with `dependencies --relation`.

## Query Dependencies

Query all configured relations for one artifact:

```bash
depmesh -p llm dependencies ./src/app.py
```

Human convenience alias:

```bash
depmesh deps ./src/app.py
```

Query more than one artifact at once:

```bash
depmesh -p llm dependencies ./src/app.py ./src/service.py
```

The result merges dependencies for all requested artifacts. It does not show which requested artifact produced each dependency.

Limit output to one or more relations:

```bash
depmesh -p llm dependencies --relation tests ./src/app.py
depmesh -p llm dependencies --relation imports --relation tests ./src/app.py
```

Example output:

```text
## imports

Python files imported by the Python file.

- ./src/config.py
- ./src/service.py

## tests

Tests that verify the artifact.

- ./tests/test_app.py
```

## Reverse Lookups

Relations are single-directional. Reverse lookups use a separate configured relation id.

Example:

```bash
depmesh -p llm dependencies --relation imported_by ./src/config.py
```

If the reverse relation is not listed by `depmesh -p llm relations`, it is not available.

## Warnings And Errors

Non-fatal problems can be included in command output:

```text
## warnings

- relation `imports`: skipped unresolved dependency `third_party_package`
```

A missing configuration file, invalid relation id, invalid arguments, or query failure exits non-zero. Read the diagnostic and either fix the invocation or inspect the relevant configuration documentation:

```bash
depmesh -p llm skill configuration
depmesh -p llm skill initialization
```
