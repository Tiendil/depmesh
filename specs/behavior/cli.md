# CLI Interface

## Goal of the document

This document describes how `depmesh` behaves as a command line interface, including:

- how users and tools invoke it.
- which commands and arguments are accepted.
- which output protocols are supported.
- what output shape each dependency query produces.

## Scope

The scope of this specification is limited to CLI behavior.

The following topics are out of scope:

- dependency discovery rules.
- relation properties.
- relation semantics.
- configuration file semantics.

This specification may refer to the following concepts only to describe how the CLI accepts arguments and renders output:

- configured relations.
- relation ids.
- reverse relation ids.
- relation descriptions.
- configuration paths.

The exact Markdown text emitted by `depmesh skill` is out of scope.

## General behavior

`depmesh` is a command line tool with explicit subcommands for dependency queries, skill text, and version output.

The root command MUST be a command group.

Dependency queries MUST use the `show` command:

```bash
depmesh show [OPTIONS] ARTIFACT...
```

Global options, when present, MUST be provided before the subcommand:

```bash
depmesh [GLOBAL_OPTIONS] COMMAND [COMMAND_OPTIONS]
```

`ARTIFACT` is an artifact identifier accepted by the configured dependency rules.

In the initial implementation this is expected to be a file path, but the CLI MUST NOT reserve syntax that would prevent later support for:

- directories.
- URLs.
- DOI values.
- ISBN values.
- other identifiers.

The CLI MUST write requested command output to stdout.

Diagnostics that are not part of the requested output MUST be written to stderr.

For `automation` output, stdout MUST contain only valid JSON Lines records.

Diagnostics written to stderr MAY be plain text and MAY be non-JSONL, including when `--protocol automation` was requested.

The CLI MUST produce deterministic output for the same:

- input.
- configuration.
- working directory.
- project state.

## Commands

The CLI MUST support these commands and command forms:

- `depmesh [GLOBAL_OPTIONS] show [OPTIONS] ARTIFACT...` — query dependencies for one or more artifacts.
- `depmesh [GLOBAL_OPTIONS] skill` — print extensive agent-oriented instructions for using `depmesh`.
- `depmesh [GLOBAL_OPTIONS] version` — print the tool version.
- `depmesh --help` — print root help information.

The root command MUST NOT perform a dependency query directly.

## Output behavior

All output MUST use UTF-8.

Output MUST NOT contain:

- terminal color.
- styling.
- other control sequences.

Dependency query output MUST group dependencies by directional relation id.

Dependency query output MUST order relation groups alphabetically by directional relation id.

Dependency query output MUST order dependencies alphabetically inside each relation group.

The `show` command MUST always treat each input artifact as the left side of selected directional relations and MUST output artifacts found on the right side of those directional relations.

If a configured relation from `x` to `y` has relation id `relation_id` and reverse relation id `reverse_relation_id`:

- selecting `relation_id` for input `x` MUST return `y`.
- selecting `reverse_relation_id` for input `y` MUST return `x`.

Dependency query output MUST group dependencies under the selected directional relation id that produced them.

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

`human` and `llm` MUST be separate protocols.

Human output SHOULD be compact and easy to scan.

LLM output SHOULD be:

- explicit.
- stable.
- self-contained for coding agents that receive the output as a tool result.

For commands that support multiple output protocols, the output protocol MUST be selected with:

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

LLM output SHOULD prefer stable identifiers and explicit paths over compact visual formatting.

LLM output MUST include the configured directional relation description between a relation `h2` heading and the dependency list for that relation when the directional relation description is not `None`.

LLM output MUST NOT display a relation description, placeholder, or blank description paragraph when the directional relation description is `None`.

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
- `skill` — record emitted by `depmesh --protocol automation skill`; record content is outside this specification.
- `error` — fatal problem, emitted before a non-zero exit when possible.

Additional fields MAY be added in future versions. Consumers MUST ignore unknown fields.

## Global options

### `-h`, `--help`

`-h` and `--help` MUST print help information and exit with status `0`.

Example:

```bash
depmesh --help
```

### `-p`, `--protocol PROTOCOL`

`-p` and `--protocol PROTOCOL` MUST be global options accepted before the subcommand.

The selected protocol MUST be available to every subcommand.

Subcommands that render protocol-specific output MUST use the selected protocol.

For `depmesh show`, the default protocol MUST be `human`.

For `depmesh skill`, the default protocol MUST be `llm`.

Subcommands that do not render protocol-specific output MAY ignore this option.

Allowed values MUST be:

- `human`
- `llm`
- `automation`

### `--config PATH`

`--config PATH` MUST be a global option accepted before the subcommand.

The resolved configuration path MUST be available to every subcommand.

Subcommands that load configuration MUST use this path instead of discovering `depmesh.toml` from the current working directory.

Subcommands that do not load workspace configuration MAY ignore this option.

`PATH` MAY be relative to the current working directory or absolute.

## Show Command

The `show` command MUST query dependencies for one or more artifacts.

```bash
depmesh show [OPTIONS] ARTIFACT...
```

The `show` command MUST accept:

- `-r`, `--relation RELATION_ID`.

### Argument `ARTIFACT...`

`ARTIFACT...` MUST accept one or more artifact identifiers.

The CLI MUST preserve the user-provided artifact spelling in output where that helps identify the original request.

The CLI MAY also include normalized or resolved artifact identifiers when useful.

### Option `-r`, `--relation RELATION_ID`

`-r RELATION_ID` and `--relation RELATION_ID` MUST limit output to the specified relation.

`RELATION_ID` MUST match either a configured relation id or a configured reverse relation id.

`RELATION_ID` MUST be interpreted as a directional relation id.

When `RELATION_ID` matches a configured relation id, the command MUST use configured forward dependency rules for that relation.

When `RELATION_ID` matches a configured reverse relation id, the command MUST derive dependencies in the reverse direction from configured forward dependency rules for the corresponding relation.

This option MAY be repeated to include multiple relations.

When this option is repeated, output MUST include dependencies whose relation matches any specified `RELATION_ID`.

Example:

```bash
depmesh show -r imports -r tests ./src/do_smth.py
```

If omitted, all configured directional relation ids MUST be included.

### Example: default human output

Command:

```bash
depmesh show ./src/do_smth.py
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
depmesh show ./src/do_smth.py ./src/another_module.py
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
depmesh show --relation tests ./src/do_smth.py
```

Example output:

```text
tests:
  ./src/tests/test_do_smth.py
```

### Example: reverse relation id

Command:

```bash
depmesh show --relation imported_by ./src/some_module.py
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
depmesh --protocol llm show ./src/do_smth.py
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
depmesh --protocol automation show ./src/do_smth.py
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

### Example: human output with warnings

Command:

```bash
depmesh show ./src/do_smth.py
```

Example output:

```text
imports:
  ./src/another_module.py
  ./src/some_module.py

warnings:
  relation `imports`: skipped unresolved dependency `third_party_package`
```

### Example: LLM output with warnings

Command:

```bash
depmesh --protocol llm show ./src/do_smth.py
```

Example output:

```text
## imports

Files imported by the input artifacts.

- ./src/another_module.py
- ./src/some_module.py

## warnings

- relation `imports`: skipped unresolved dependency `third_party_package`
```

### Example: automation output with warnings

Command:

```bash
depmesh --protocol automation show ./src/do_smth.py
```

Example output:

```jsonl
{"type":"dependency","relation":"imports","dependency":"./src/another_module.py"}
{"type":"dependency","relation":"imports","dependency":"./src/some_module.py"}
{"type":"warning","relation":"imports","message":"skipped unresolved dependency `third_party_package`"}
```

## Skill Command

The `skill` command MUST print extensive instructions for coding agents that want to use `depmesh` effectively.

```bash
depmesh skill
```

For the `llm` protocol, `depmesh skill` output MUST be Markdown-compatible text.

The command output SHOULD be suitable for coding agents that receive the output as a tool result.

The default output protocol for this command MUST be `llm` when no global protocol is selected.

The `skill` command MUST NOT accept artifact arguments or dependency query options.

For `depmesh skill`, `PROTOCOL` MAY be:

- `llm`.
- `human`.
- `automation`.

The `llm` protocol MUST be the canonical protocol for `depmesh skill`.

### Example: LLM output

Command:

```bash
depmesh skill
```

Example output:

```text
The exact Markdown text emitted by `depmesh skill` is not part of this specification.
```

### Example: automation output

Command:

```bash
depmesh --protocol automation skill
```

Example output:

```jsonl
{"type":"skill","text":"The exact content emitted by `depmesh skill` is not part of this specification."}
```

## Version Command

The `version` command MUST print the tool version and exit with status `0`.

Version output MUST be a single line containing only the version number.

```bash
depmesh [GLOBAL_OPTIONS] version
```

Example output:

```text
0.1.0
```

The `version` command MUST NOT accept dependency query options, skill options, or artifact arguments.

The `version` command MAY ignore global options that do not affect version output.

## Help Examples

### Help

Command:

```bash
depmesh --help
```

Help output SHOULD be autogenerated from:

- command definitions.
- argument definitions.
- option definitions.

## Errors and exit codes

The CLI SHOULD use these exit codes:

- `0` — command completed successfully.
- `1` — invalid command line arguments.
- `2` — configuration could not be loaded or parsed.
- `3` — dependency query failed.

Human and LLM error messages SHOULD be written to stderr.

For automation output, fatal errors SHOULD be written to stdout as an `error` record when possible and the process SHOULD still exit with a non-zero code.

If automation output cannot be initialized, fatal diagnostics MAY be written to stderr as plain text instead of stdout as JSON Lines.

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

Backward-compatible additions MAY include:

- new options.
- new JSONL fields.
- new JSONL record types.

Backward-incompatible changes MUST be documented in this specification before implementation.
