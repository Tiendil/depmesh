# `depmesh` Usage

`depmesh` is a command line interface for discovering configured dependency relations between project artifacts.

It hides the project-specific discovery mechanism behind one interface. A relation may be backed by path templates, fixed lists, file searches, static-analysis commands, or other configured sources, but the command usage stays the same.

An artifact is usually a root-anchored project path such as `@/src/app.py`. Treat artifact ids as strings accepted by the current project's `depmesh.toml`.

`depmesh` is useful only when the project has a proper `depmesh.toml` configuration. If configuration is missing or relation coverage looks incomplete, read `depmesh -p llm skill initialization` and `depmesh -p llm skill configuration`.

## Project Root

When `--config` is not provided, `depmesh` searches from the current working directory upward until it finds `depmesh.toml`. The directory containing that file is the project root for the command.

When `--config PATH` is provided, `depmesh` uses that file directly, and the directory containing it is the project root.

The project root matters because root-anchored artifact paths, glob patterns, file sources, and command sources are interpreted from that root. Run commands from inside the intended project, and prefer root-anchored artifact paths such as `@/src/app.py`.

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
--DEPMESH-CELL <id-1> BEGIN--
kind=relation
description=Specifications that apply to the artifact.
relation=governed_by
type=relation
--DEPMESH-CELL <id-1> END--
--DEPMESH-CELL <id-2> BEGIN--
kind=relation
description=Tests that verify the artifact.
relation=tested_by
type=relation
--DEPMESH-CELL <id-2> END--
```

2. Prepare to change a source file.

Query dependencies for that file to see what other files may be affected and should be read first:

```bash
depmesh -p llm dependencies @/src/app.py
```

If the relation list includes tests, specs, imports, or reverse imports, combine relation filters to focus the result:

```bash
depmesh -p llm dependencies --relation tested_by --relation governed_by --relation imported_by @/src/app.py
```

Example output:

```text
--DEPMESH-CELL <id-1> BEGIN--
kind=dependencies
media_type=text/markdown
relation=governed_by
type=dependencies

- @/specs/behavior/app.md
--DEPMESH-CELL <id-1> END--
--DEPMESH-CELL <id-2> BEGIN--
kind=dependencies
media_type=text/markdown
relation=imported_by
type=dependencies

- @/src/main.py
--DEPMESH-CELL <id-2> END--
--DEPMESH-CELL <id-3> BEGIN--
kind=dependencies
media_type=text/markdown
relation=tested_by
type=dependencies

- @/tests/test_app.py
--DEPMESH-CELL <id-3> END--
```

3. Add a new module.

Inspect relation names first, then query a nearby module with the same expected placement. This can reveal governing specifications and test locations to mirror:

```bash
depmesh -p llm relations
depmesh -p llm dependencies --relation governed_by --relation tested_by @/src/existing_module.py
```

Example output:

```text
--DEPMESH-CELL <id-1> BEGIN--
kind=dependencies
media_type=text/markdown
relation=governed_by
type=dependencies

- @/specs/architecture/modules.md
--DEPMESH-CELL <id-1> END--
--DEPMESH-CELL <id-2> BEGIN--
kind=dependencies
media_type=text/markdown
relation=tested_by
type=dependencies

- @/tests/test_existing_module.py
--DEPMESH-CELL <id-2> END--
```

4. Change a specification.

Use a reverse governance relation to find implementation files governed by it:

```bash
depmesh -p llm dependencies --relation governs @/specs/behavior/config.md
```

Example output:

```text
--DEPMESH-CELL <id-1> BEGIN--
kind=dependencies
media_type=text/markdown
relation=governs
type=dependencies

- @/src/config.py
- @/src/config_loader.py
--DEPMESH-CELL <id-1> END--
```

5. Change shared code.

Combine reverse lookup relations to identify callers and tests:

```bash
depmesh -p llm dependencies --relation imported_by --relation tested_by @/src/shared.py
```

Example output:

```text
--DEPMESH-CELL <id-1> BEGIN--
kind=dependencies
media_type=text/markdown
relation=imported_by
type=dependencies

- @/src/app.py
- @/src/service.py
--DEPMESH-CELL <id-1> END--
--DEPMESH-CELL <id-2> BEGIN--
kind=dependencies
media_type=text/markdown
relation=tested_by
type=dependencies

- @/tests/test_shared.py
--DEPMESH-CELL <id-2> END--
```

6. Edit several artifacts together.

Query them in one command to get a merged dependency set:

```bash
depmesh -p llm dependencies @/src/app.py @/src/service.py
```

Example output:

```text
--DEPMESH-CELL <id-1> BEGIN--
kind=dependencies
media_type=text/markdown
relation=tested_by
type=dependencies

- @/tests/test_app.py
- @/tests/test_service.py
--DEPMESH-CELL <id-1> END--
```

Run separate queries when you need to know which requested artifact produced each dependency.

## Output Protocols

Dependency results, relation lists, warnings, skill documents, and initialization confirmations use shared output cells. Human and LLM cells use `DEPMESH` framing. Cell content, metadata, and ordering are deterministic; generated cell IDs may differ. IDs in the examples are placeholders.

Human and LLM dependency output groups paths into one cell per relation. Automation emits one cell per dependency, retaining `type`, `relation`, and `dependency`. Relation cells use `relation` for the relation name; `id` identifies the cell. Skill documents use `content` for their text. Warnings use `type = warning` and `message`. Fatal errors use ordinary cells with `type = error`, a native `code`, diagnostic metadata, and the formatted message in `content`. They retain nonzero exits; human and LLM errors go to stderr, and automation errors go to stdout.

Help and version remain plain text.

Use `llm` when invoking `depmesh` as a coding agent. It is the normal choice for this documentation's examples.

Use `human` for compact terminal inspection by a person.

Without `--protocol`, `skill` uses `llm` and other commands use `human`. An explicit protocol overrides these defaults.

Use `automation` when an agent or another program needs automatic processing of `depmesh` output. Automation output is JSON Lines: each stdout line is one JSON object.

Example automation command:

```bash
depmesh -p automation dependencies @/src/app.py
```

Example automation output:

```jsonl
{"content":null,"dependency":"@/src/config.py","id":"<id-1>","relation":"imports","type":"dependency"}
{"content":null,"dependency":"@/tests/test_app.py","id":"<id-2>","relation":"tests","type":"dependency"}
```

Use full command names in agent workflows and generated notes. Short forms are human convenience aliases for interactive terminal use:

- `deps` is an alias for `dependencies`.
- `rels` is an alias for `relations`.

Global options go before the subcommand:

```bash
depmesh -p llm dependencies @/src/app.py
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
--DEPMESH-CELL <id-1> BEGIN--
kind=relation
description=Python files imported by the artifact.
relation=imports
type=relation
--DEPMESH-CELL <id-1> END--
--DEPMESH-CELL <id-2> BEGIN--
kind=relation
description=Tests that verify the artifact.
relation=tests
type=relation
--DEPMESH-CELL <id-2> END--
```

Use relation ids from this output with `dependencies --relation`.

## Query Dependencies

Query all configured relations for one artifact:

```bash
depmesh -p llm dependencies @/src/app.py
```

Human convenience alias:

```bash
depmesh deps @/src/app.py
```

Query more than one artifact at once:

```bash
depmesh -p llm dependencies @/src/app.py @/src/service.py
```

The result merges dependencies for all requested artifacts. It does not show which requested artifact produced each dependency.

Limit output to one or more relations:

```bash
depmesh -p llm dependencies --relation tests @/src/app.py
depmesh -p llm dependencies --relation imports --relation tests @/src/app.py
```

Example output:

```text
--DEPMESH-CELL <id-1> BEGIN--
kind=dependencies
media_type=text/markdown
relation=imports
type=dependencies

Python files imported by the artifact.

- @/src/config.py
- @/src/service.py
--DEPMESH-CELL <id-1> END--
--DEPMESH-CELL <id-2> BEGIN--
kind=dependencies
media_type=text/markdown
relation=tests
type=dependencies

Tests that verify the artifact.

- @/tests/test_app.py
--DEPMESH-CELL <id-2> END--
```

## Reverse Lookups

Relations are single-directional. Reverse lookups use a separate configured relation id.

Example:

```bash
depmesh -p llm dependencies --relation imported_by @/src/config.py
```

If the reverse relation is not listed by `depmesh -p llm relations`, it is not available.

## Warnings And Errors

Non-fatal problems can be included in command output:

```text
--DEPMESH-CELL <id-1> BEGIN--
kind=warning
message=relation `imports`: skipped unresolved dependency `third_party_package`
type=warning
--DEPMESH-CELL <id-1> END--
```

A missing configuration file, invalid relation id, invalid arguments, or query failure exits non-zero. Read the diagnostic and either fix the invocation or inspect the relevant configuration documentation:

```bash
depmesh -p llm skill configuration
depmesh -p llm skill initialization
```
