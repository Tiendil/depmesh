# CLI Interface

## Goal of the document

This document describes how `depmesh` behaves as a command line interface: how users and tools invoke it, which commands and arguments are accepted, which output protocols are supported, and what output shape each command produces.

## Scope

The scope of this specification is limited to CLI behavior.

Dependency discovery rules, relation semantics, plugin behavior, and configuration file semantics are out of scope except for CLI options needed to select or report them.

## General behavior

`depmesh` is a command line tool that prints dependency information for one or more artifacts.

The root command MUST be the primary dependency query command:

```bash
depmesh [OPTIONS] ARTIFACT...
```

`ARTIFACT` is an artifact identifier accepted by the configured dependency rules. In the initial implementation this is expected to be a file path, but the CLI MUST NOT reserve syntax that would prevent later support for directories, URLs, DOI values, ISBN values, or other identifiers.

The CLI MUST write requested command output to stdout.

Diagnostics that are not part of the requested output MUST be written to stderr.

For `automation` output, stdout MUST contain only valid JSON Lines records.

The CLI MUST produce deterministic output for the same input, configuration, working directory, and project state.

## Commands

The CLI MUST support these commands and command forms:

- `depmesh [OPTIONS] ARTIFACT...` — query dependencies for one or more artifacts.
- `depmesh --skill` — print extensive agent-oriented instructions for using `depmesh`.
- `depmesh --help` — print root help information.
- `depmesh --version` — print the tool version.

## Output behavior

All output MUST use UTF-8.

Output MUST NOT contain terminal color, styling, or other control sequences.

Dependency query output MUST group dependencies by relation.

Dependency query output MUST order relation groups alphabetically by relation name.

Dependency query output MUST order dependencies alphabetically inside each relation group.

Dependency query output MUST use relation names for the current query direction.

If a relation between `x` and `y` is named `name_1` from `x` to `y` and `name_2` from `y` to `x`, forward output for `x` MUST group `y` under `name_1`, and reverse output for `y` MUST group `x` under `name_2`.

When multiple artifact identifiers are provided, dependency query output MUST contain merged dependencies for all input artifacts.

When multiple input artifacts have the same dependency for the same relation, dependency query output MUST contain that dependency once.

Dependency query output MUST NOT group dependencies by input artifact. Users and agents that need per-artifact dependencies SHOULD call `depmesh` separately for each artifact.

Output SHOULD include non-fatal problems discovered while processing the request.

Non-fatal problems SHOULD be represented as warnings.

## Output protocols

The CLI MUST support three output protocols:

- `human` — default protocol for terminal users.
- `llm` — text protocol optimized for coding agents that invoke `depmesh` as a tool.
- `automation` — protocol optimized for programs; output is serialized as JSON Lines.

`human` and `llm` MUST be separate protocols. Human output SHOULD be compact and easy to scan. LLM output SHOULD be explicit, stable, and self-contained for coding agents that receive the output as a tool result.

The output protocol MUST be selected with:

```bash
--protocol PROTOCOL
```

Allowed values MUST be:

- `human`
- `llm`
- `automation`

### Human output

Human output SHOULD use concise labels.

Human output SHOULD prefer relative paths when the input and dependency are inside the project.

Human output SHOULD avoid implementation metadata unless it is needed to understand the result.

### LLM output

The `llm` protocol MUST be used only when a coding agent invokes `depmesh` as a tool.

LLM output MUST use plain Markdown-compatible text.

LLM output SHOULD be concise and SHOULD avoid redundant information.

LLM output SHOULD include enough labels that individual lines remain understandable when quoted out of context.

LLM output SHOULD prefer stable identifiers and explicit paths over compact visual formatting.

LLM output MUST include the configured relation description between each relation `h2` heading and the dependency list for that relation.

### Automation output

Automation output MUST be serialized as JSON Lines.

Automation output MUST write one JSON object per line.

Automation output MUST use stable field names.

Automation output MUST emit records in deterministic order.

Automation output SHOULD represent warnings and errors as records when they are part of command output.

The common JSONL record fields MUST be:

```json
{"type":"record type"}
```

Known record types MUST include:

- `dependency` — one merged dependency entry.
- `warning` — non-fatal problem.
- `skill` — one section of agent-oriented tool usage information.
- `error` — fatal problem, emitted before a non-zero exit when possible.

Additional fields MAY be added in future versions. Consumers MUST ignore unknown fields.

## Global options

### `-h`, `--help`

`-h` and `--help` MUST print help information and exit with status `0`.

Example:

```bash
depmesh --help
```

### `-V`, `--version`

`-V` and `--version` MUST print the tool version and exit with status `0`.

Version output MUST be a single line containing only the version number.

Example output:

```text
0.1.0
```

### `-p`, `--protocol PROTOCOL`

`-p` and `--protocol PROTOCOL` MUST select output protocol.

The default protocol MUST be `human`, except for `depmesh --skill`, whose default protocol MUST be `llm`.

Allowed values MUST be:

- `human`
- `llm`
- `automation`

### `--config PATH`

`--config PATH` MUST use a specific `depmesh.toml` file instead of discovering it from the current working directory.

`PATH` MAY be relative to the current working directory or absolute.

## Dependency query command

The root command MUST query dependencies for one or more artifacts.

```bash
depmesh [OPTIONS] ARTIFACT...
```

### Argument `ARTIFACT...`

`ARTIFACT...` MUST accept one or more artifact identifiers.

The CLI MUST preserve the user-provided artifact spelling in output where that helps identify the original request.

The CLI MAY also include normalized or resolved artifact identifiers when useful.

### Option `-r`, `--relation RELATION_ID`

`-r RELATION_ID` and `--relation RELATION_ID` MUST limit output to the specified relation type.

When a relation has different names in different directions, the CLI MUST apply the filter to the underlying relation type and MUST still display the relation name for the current query direction.

This option MAY be repeated to include multiple relation types.

When this option is repeated, output MUST include dependencies whose relation type matches any specified `RELATION_ID`.

Example:

```bash
depmesh -r imports -r tests ./src/do_smth.py
```

If omitted, all configured relation types MUST be included.

### Option `--reverse`

`--reverse` MUST show reverse dependencies: artifacts that depend on the specified artifacts.

Reverse dependency output MUST use reverse relation names.

This option MUST change the direction of the dependency query but MUST NOT change the output protocol contract.

### Example: default human output

Command:

```bash
depmesh ./src/do_smth.py
```

Example output:

```text
imports:
  ./src/another_module.py
  ./src/some_module.py

specs:
  ./specs/architecture.md
  ./specs/top_level_behavior.md
  ./specs/types.md

tests:
  ./src/tests/test_do_smth.py
```

### Example: multiple artifacts

Command:

```bash
depmesh ./src/do_smth.py ./src/another_module.py
```

Example output:

```text
imports:
  ./src/another_module.py
  ./src/some_module.py
  ./src/types.py

tests:
  ./src/tests/test_another_module.py
  ./src/tests/test_do_smth.py
```

### Example: relation filter

Command:

```bash
depmesh --relation tests ./src/do_smth.py
```

Example output:

```text
tests:
  ./src/tests/test_do_smth.py
```

### Example: reverse dependencies

Command:

```bash
depmesh --reverse ./src/some_module.py
```

Example output:

```text
imported_by:
  ./src/do_smth.py
  ./src/feature.py
```

### Example: LLM output

Command:

```bash
depmesh --protocol llm ./src/do_smth.py
```

Example output:

```text
## imports

Files imported by the input artifacts.

- ./src/another_module.py
- ./src/some_module.py

## specs

Specifications related to the input artifacts.

- ./specs/architecture.md
- ./specs/top_level_behavior.md
- ./specs/types.md

## tests

Tests related to the input artifacts.

- ./src/tests/test_do_smth.py
```

### Example: automation output

Command:

```bash
depmesh --protocol automation ./src/do_smth.py
```

Example output:

```jsonl
{"type":"dependency","relation":"imports","dependency":"./src/another_module.py"}
{"type":"dependency","relation":"imports","dependency":"./src/some_module.py"}
{"type":"dependency","relation":"specs","dependency":"./specs/architecture.md"}
{"type":"dependency","relation":"specs","dependency":"./specs/top_level_behavior.md"}
{"type":"dependency","relation":"specs","dependency":"./specs/types.md"}
{"type":"dependency","relation":"tests","dependency":"./src/tests/test_do_smth.py"}
```

## Skill command form

The `depmesh --skill` command form MUST print extensive instructions for coding agents that want to use `depmesh` effectively.

```bash
depmesh --skill
```

The command output SHOULD be suitable for coding agents that receive the output as a tool result.

The default output protocol for this command MUST be `llm`.

The `depmesh --skill` command form MAY be combined with `--protocol PROTOCOL` and `--config PATH`.

The `depmesh --skill` command form MUST NOT be combined with artifact arguments or dependency query options.

For `depmesh --skill`, `PROTOCOL` MAY be `llm`, `human`, or `automation`, but `llm` MUST be the canonical protocol.

### Example: LLM output

Command:

```bash
depmesh --skill
```

Example output:

```text
The exact content emitted by `depmesh --skill` is not part of this specification.
```

### Example: automation output

Command:

```bash
depmesh --skill --protocol automation
```

Example output:

```jsonl
{"type":"skill","text":"The exact content emitted by `depmesh --skill` is not part of this specification."}
```

## Help and version examples

### Help

Command:

```bash
depmesh --help
```

Help output SHOULD be autogenerated from command, argument, and option definitions.

### Version

Command:

```bash
depmesh --version
```

Example output:

```text
0.1.0
```

## Errors and exit codes

The CLI SHOULD use these exit codes:

- `0` — command completed successfully.
- `1` — invalid command line arguments.
- `2` — configuration could not be loaded or parsed.
- `3` — dependency query failed.

Human and LLM error messages SHOULD be written to stderr.

For automation output, fatal errors SHOULD be written to stdout as an `error` record when possible and the process SHOULD still exit with a non-zero code.

Example automation fatal error:

```jsonl
{"type":"error","code":"config_not_found","message":"depmesh.toml was not found","path":"./depmesh.toml"}
```

## Compatibility rules

The CLI SHOULD preserve backward compatibility for:

- Command names.
- Option names.
- Output protocol names.
- JSONL record `type` values.
- JSONL field meanings.

Backward-compatible additions MAY include new options, new JSONL fields, and new JSONL record types.

Backward-incompatible changes MUST be documented in this specification before implementation.
