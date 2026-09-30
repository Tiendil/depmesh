# CLI Interface

## Goal of the document

This document describes how `depmesh` behaves as a command line interface, including:

- how users and tools invoke it.
- which commands and arguments are accepted.
- which output protocols are supported.
- what output shape each relation list and dependency query produces.

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
- relation descriptions.
- configuration paths.

The exact Markdown text emitted by `depmesh skill` is out of scope.

## General behavior

`depmesh` is a command line tool that provides a generalized interface for discovering dependencies between files in a project. It supports multiple dependency discovery mechanisms, from glob pattern templates to third-party commands, so agents and developers can use one interface without needing to know exactly how each dependency relation is discovered.

The CLI has two primary workflows:

- `depmesh dependencies ...` — query dependencies for one or more artifacts.
- `depmesh relations` — list available relation types and their descriptions.

The root command MUST be a command group constructed through the application setup managed by `llm_tool_cli`.

Dependency queries MUST use the `dependencies` command or its `deps` alias:

```bash
depmesh dependencies [OPTIONS] ARTIFACT...
depmesh deps [OPTIONS] ARTIFACT...
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

For commands that emit cells or fatal errors, `automation` stdout MUST contain only valid JSON Lines records. Help retains its plain-text contract.

Diagnostics written to stderr MAY be plain text and MAY be non-JSONL, including when `--protocol automation` was requested.

Cell content, metadata, and output ordering MUST be deterministic for the same:

- input.
- configuration.
- working directory.
- project state.

Cell identifiers MAY vary between invocations and MUST use the shared library's generated identifiers.

## Commands

The CLI MUST support these commands and command forms:

- `depmesh [GLOBAL_OPTIONS] dependencies [OPTIONS] ARTIFACT...` — query dependencies for one or more artifacts.
- `depmesh [GLOBAL_OPTIONS] deps [OPTIONS] ARTIFACT...` — alias for `dependencies`.
- `depmesh [GLOBAL_OPTIONS] relations` — list configured relations.
- `depmesh [GLOBAL_OPTIONS] rels` — alias for `relations`.
- `depmesh [GLOBAL_OPTIONS] skill [DOCUMENT]` — print built-in agent-oriented documentation for using `depmesh`.
- `depmesh [GLOBAL_OPTIONS] init` — create a starter configuration file.
- `depmesh [GLOBAL_OPTIONS] version` — print the tool version.
- `depmesh --help` — print root help information.

The root command MUST NOT perform a dependency query directly.

## Application identity

The CLI MUST initialize the tool label `DEPMESH` through `llm_tool_cli` at application startup before command-line parsing.
Label storage, initialization checks, and label selection for cell rendering MUST be managed by `llm_tool_cli`.

## Output behavior

The CLI MUST use the cell model, cell and environment-error construction and rendering, and text writing provided by `llm_tool_cli.protocol`. Text cell framing MUST use the label `DEPMESH`.

Depmesh MUST own its logic-cell payloads and domain-specific projections, including dependency grouping, relation descriptions, and record metadata. Shared logic-cell projection and rendering MUST manage generic cell framing, sequence rendering contexts, identifier generation, and serialization.

Output MUST NOT contain:

- terminal color.
- styling.
- other control sequences.

Dependency query output MUST group dependencies by relation id.

Dependency query output MUST order relation groups alphabetically by relation id.

Dependency query output MUST order dependencies alphabetically inside each relation group.

The `dependencies` command MUST always treat each input artifact as the left side of selected relations and MUST output artifacts found on the right side of those relations.

Relations are single-directional. Reverse lookups MUST be represented by separate configured relations and rules.

Dependency query output MUST group dependencies under the selected relation id that produced them.

When multiple artifact identifiers are provided, dependency query output MUST contain merged dependencies for all input artifacts.

When multiple input artifacts have the same dependency for the same relation, dependency query output MUST contain that dependency once.

Dependency query output MUST NOT group dependencies by input artifact. Users and agents that need per-artifact dependencies SHOULD call `depmesh` separately for each artifact.

Output SHOULD include non-fatal problems discovered while processing the request.

Non-fatal problems SHOULD be represented as warnings.

Relation list output MUST order relations alphabetically by relation id.

## Output protocols

The CLI MUST support the output modes defined by `llm_tool_cli.protocol`.

Depmesh interprets these modes as follows:

- `human` — text protocol for terminal users.
- `llm` — text protocol optimized for coding agents that invoke `depmesh` as a tool.
- `automation` — protocol optimized for programs; output is serialized as JSON Lines.

Human output SHOULD be compact and easy to scan.

LLM output SHOULD be:

- explicit.
- stable.
- self-contained for coding agents that receive the output as a tool result.

### Output cells

For a given protocol, the same domain data MUST produce equivalent cell payloads regardless of generated identifiers.

- Human and LLM dependency output MUST contain one Markdown cell of kind `dependencies` per nonempty relation group, with `type = dependencies` and `relation` metadata. Its content MUST contain the optional description followed by a Markdown list of dependencies.
- Automation dependency output MUST contain one metadata-only cell of kind `dependency` per merged dependency, with `type = dependency`, `relation`, and `dependency` metadata.
- Each warning MUST be a metadata-only cell of kind `warning`, with `type = warning` and `message` metadata. Warning cells MUST follow dependency cells in warning insertion order.
- Each relation MUST be a metadata-only cell of kind `relation`, with `type = relation`, `relation`, and optional `description` metadata.
- Successful initialization MUST emit a shared `operation_succeeded` cell, with `type = operation_succeeded` and the created configuration `path` in metadata.

Empty dependency results without warnings and empty relation lists MUST emit no cells.

Cell `id` MUST refer to the generated cell identifier. Relation names MUST use `relation`, never `id`. Document text MUST use cell `content`, never a separate `text` field. Metadata-only automation cells MUST retain the shared absent-content representation.

The `type` metadata MUST preserve the machine-readable record type because shared cell serialization does not automatically include the cell kind.

Cell identifiers in examples are placeholders; actual identifiers MAY differ on each invocation.

### Human output

Human output SHOULD use concise labels.

Human output SHOULD prefer canonical root-anchored paths when the input and dependency are inside the project.

Human output MUST use shared human cell formatting with Depmesh-owned metadata.

### LLM output

The `llm` protocol MUST be used only when a coding agent invokes `depmesh` as a tool.

LLM output MUST use plain Markdown-compatible text.

LLM output SHOULD be concise and SHOULD avoid redundant information.

LLM output SHOULD prefer stable identifiers and explicit paths over compact visual formatting.

Human and LLM dependency cells MUST identify the relation in metadata and include its configured description before the dependency list when the description is not `None`.

A dependency cell MUST NOT display a description, placeholder, or blank description paragraph when the relation description is `None`.

### Automation output

Automation JSON Lines serialization MUST be provided by `llm_tool_cli.protocol`.

Automation output MUST use stable field names.

Automation output MUST emit records in deterministic order.

Automation output SHOULD represent warnings and errors as records when they are part of command output.

The common JSONL record fields MUST be:

```json
{"type":"record type"}
```

Known record types MUST include:

- `dependency` — one merged dependency entry.
- `relation` — one configured relation entry.
- `warning` — non-fatal problem.
- `skill` — record emitted by `depmesh --protocol automation skill`; record content is outside this specification.
- `version` — record emitted by the version command managed by `llm_tool_cli`.
- `operation_succeeded` — successful initialization.
- `error` — fatal problem, emitted as an ordinary shared error cell before a non-zero exit when possible, with the formatted message in `content`, native `code`, and diagnostic context in metadata.

Additional fields MAY be added in future versions. Consumers MUST ignore unknown fields.

## Global options

The CLI MUST use the parsed global options, invocation-context storage and retrieval, and command protocol selection provided by `llm_tool_cli`.
The library owns option availability across subcommands, invocation isolation, and protocol selection.
Depmesh MUST combine shared and Depmesh-owned option parsing, pass the parsed options to shared context storage, and supply the invoked command name to shared protocol selection.

### Help and completion

The CLI MUST use help aliases and shell completion options managed by `llm_tool_cli`.

### `-p`, `--protocol PROTOCOL`

The CLI MUST use protocol-option parsing and invalid-value diagnostics managed by `llm_tool_cli`.

Subcommands that render protocol-specific output MUST use the selected protocol.

Subcommands that do not render protocol-specific output MAY ignore this option.

### `--config PATH`

The CLI MUST use the configuration-option parsing managed by `llm_tool_cli`, including its deferred filesystem validation.

Subcommands that load configuration MUST pass this option to the configuration selection managed by `llm_tool_cli`.
Depmesh's configuration filename, schema, and configuration-root rules are defined in `specs/behavior/config.md`.

## Dependencies Command

The `dependencies` command MUST query dependencies for one or more artifacts.

```bash
depmesh dependencies [OPTIONS] ARTIFACT...
depmesh deps [OPTIONS] ARTIFACT...
```

The `deps` command MUST be an alias for `dependencies`.

The `dependencies` command MUST accept:

- `-r`, `--relation RELATION_ID`.

### Argument `ARTIFACT...`

`ARTIFACT...` MUST accept one or more artifact identifiers.

Filesystem artifact inputs MUST expand home markers before normalization and project-root containment checks.
Root-anchored inputs MUST preserve literal home-marker segments.
An inability to expand a home marker MUST report `path_resolution_failed` and exit with status `3`.

The CLI MUST preserve the user-provided artifact spelling in output where that helps identify the original request.

The CLI MAY also include normalized or resolved artifact identifiers when useful.

### Option `-r`, `--relation RELATION_ID`

`-r RELATION_ID` and `--relation RELATION_ID` MUST limit output to the specified relation.

`RELATION_ID` MUST match a configured relation id.

When `RELATION_ID` matches a configured relation id, the command MUST use configured dependency rules for that relation.

This option MAY be repeated to include multiple relations.

When this option is repeated, output MUST include dependencies whose relation matches any specified `RELATION_ID`.

Example:

```bash
depmesh dependencies -r imports -r tests @/src/do_smth.py
```

If omitted, all configured relation ids MUST be included.

## Relations Command

The `relations` command MUST list configured relations.

```bash
depmesh relations
depmesh rels
```

The `rels` command MUST be an alias for `relations`.

The command MUST NOT accept artifact arguments or dependency query options.

The command MUST render all configured relations in deterministic order by relation id.

For human and LLM output, each relation MUST use the shared cell formatting with its relation name and optional description in metadata.

For automation output, each relation MUST be rendered as one cell record:

```json
{"content":null,"description":"Tests related to the input artifacts.","id":"<id-1>","relation":"tests","type":"relation"}
```

The `description` field MUST be omitted when the relation has no description.

### Example: relations human output

Command:

```bash
depmesh --protocol human relations
```

Example output:

```text
----- DEPMESH CELL <id-1> -----
kind = relation
description = Python files imported by the input Python file.
relation = imports
type = relation

----- DEPMESH CELL <id-2> -----
kind = relation
description = Tests related to the input artifacts.
relation = tests
type = relation

```

### Example: human output

Command:

```bash
depmesh --protocol human dependencies @/src/do_smth.py
```

Example output:

```text
----- DEPMESH CELL <id-1> -----
kind = dependencies
media_type = text/markdown
relation = imports
type = dependencies

- @/src/another_module.py
- @/src/some_module.py

----- DEPMESH CELL <id-2> -----
kind = dependencies
media_type = text/markdown
relation = specs
type = dependencies

- @/specs/architecture.md
- @/specs/top_level_behavior.md
- @/specs/types.md

----- DEPMESH CELL <id-3> -----
kind = dependencies
media_type = text/markdown
relation = tests
type = dependencies

- @/src/tests/test_do_smth.py

```

### Example: multiple artifacts

Command:

```bash
depmesh --protocol human dependencies @/src/do_smth.py @/src/another_module.py
```

Example output:

```text
----- DEPMESH CELL <id-1> -----
kind = dependencies
media_type = text/markdown
relation = imports
type = dependencies

- @/src/another_module.py
- @/src/some_module.py
- @/src/types.py

----- DEPMESH CELL <id-2> -----
kind = dependencies
media_type = text/markdown
relation = tests
type = dependencies

- @/src/tests/test_another_module.py
- @/src/tests/test_do_smth.py

```

### Example: relation filter

Command:

```bash
depmesh --protocol human dependencies --relation tests @/src/do_smth.py
```

Example output:

```text
----- DEPMESH CELL <id-1> -----
kind = dependencies
media_type = text/markdown
relation = tests
type = dependencies

- @/src/tests/test_do_smth.py

```

### Example: reverse relation

Command:

```bash
depmesh --protocol human dependencies --relation imported_by @/src/some_module.py
```

Example output:

```text
----- DEPMESH CELL <id-1> -----
kind = dependencies
media_type = text/markdown
relation = imported_by
type = dependencies

- @/src/do_smth.py
- @/src/feature.py

```

### Example: LLM output

Command:

```bash
depmesh --protocol llm dependencies @/src/do_smth.py
```

Example output:

```text
--DEPMESH-CELL <id-1> BEGIN--
kind=dependencies
media_type=text/markdown
relation=imports
type=dependencies

Files imported by the input artifacts.

- @/src/another_module.py
- @/src/some_module.py
--DEPMESH-CELL <id-1> END--
--DEPMESH-CELL <id-2> BEGIN--
kind=dependencies
media_type=text/markdown
relation=specs
type=dependencies

Specifications related to the input artifacts.

- @/specs/architecture.md
- @/specs/top_level_behavior.md
- @/specs/types.md
--DEPMESH-CELL <id-2> END--
--DEPMESH-CELL <id-3> BEGIN--
kind=dependencies
media_type=text/markdown
relation=tests
type=dependencies

Tests related to the input artifacts.

- @/src/tests/test_do_smth.py
--DEPMESH-CELL <id-3> END--
```

### Example: automation output

Command:

```bash
depmesh --protocol automation dependencies @/src/do_smth.py
```

Example output:

```jsonl
{"content":null,"dependency":"@/src/another_module.py","id":"<id-1>","relation":"imports","type":"dependency"}
{"content":null,"dependency":"@/src/some_module.py","id":"<id-2>","relation":"imports","type":"dependency"}
{"content":null,"dependency":"@/specs/architecture.md","id":"<id-3>","relation":"specs","type":"dependency"}
{"content":null,"dependency":"@/specs/top_level_behavior.md","id":"<id-4>","relation":"specs","type":"dependency"}
{"content":null,"dependency":"@/specs/types.md","id":"<id-5>","relation":"specs","type":"dependency"}
{"content":null,"dependency":"@/src/tests/test_do_smth.py","id":"<id-6>","relation":"tests","type":"dependency"}
```

### Example: human output with warnings

Command:

```bash
depmesh --protocol human dependencies @/src/do_smth.py
```

Example output:

```text
----- DEPMESH CELL <id-1> -----
kind = dependencies
media_type = text/markdown
relation = imports
type = dependencies

- @/src/another_module.py
- @/src/some_module.py

----- DEPMESH CELL <id-2> -----
kind = warning
message = relation `imports`: skipped unresolved dependency `third_party_package`
type = warning

```

### Example: LLM output with warnings

Command:

```bash
depmesh --protocol llm dependencies @/src/do_smth.py
```

Example output:

```text
--DEPMESH-CELL <id-1> BEGIN--
kind=dependencies
media_type=text/markdown
relation=imports
type=dependencies

Files imported by the input artifacts.

- @/src/another_module.py
- @/src/some_module.py
--DEPMESH-CELL <id-1> END--
--DEPMESH-CELL <id-2> BEGIN--
kind=warning
message=relation `imports`: skipped unresolved dependency `third_party_package`
type=warning
--DEPMESH-CELL <id-2> END--
```

### Example: automation output with warnings

Command:

```bash
depmesh --protocol automation dependencies @/src/do_smth.py
```

Example output:

```jsonl
{"content":null,"dependency":"@/src/another_module.py","id":"<id-1>","relation":"imports","type":"dependency"}
{"content":null,"dependency":"@/src/some_module.py","id":"<id-2>","relation":"imports","type":"dependency"}
{"content":null,"id":"<id-3>","message":"relation `imports`: skipped unresolved dependency `third_party_package`","type":"warning"}
```

## Skill Command

The CLI MUST register the skill command managed by `llm_tool_cli`, supplying the `depmesh.skills` resource package and Depmesh's document definitions.
The library owns argument selection and validation, defaults, help and completion, configuration independence, cell output, and failure streams and exit statuses.

Depmesh MUST provide these documents:

- `usage` — general command usage documentation.
- `configuration` — configuration documentation.
- `initialization` — project initialization documentation.

## Init Command

The `init` command MUST create a starter configuration file.

```bash
depmesh init
depmesh --config ./path/to/depmesh.toml init
```

The command MUST use the initialization behavior managed by `llm_tool_cli`, supplying Depmesh's default configuration filename, the invocation's working directory, and the optional `--config` path.
The library owns target selection and resolution, template reading, exclusive creation, and their diagnostics.
Depmesh owns the starter contents described below.

The generated configuration MUST:

- be valid TOML.
- use schema version `1`.
- include the `governed_by` relation.
- include the `governs` relation.
- include commented examples of relation rules.

The command MUST emit a shared success cell to stdout with the created configuration path in `path` metadata and a success message as content.
It MUST honor the selected output protocol.

The command MUST NOT accept artifact arguments, relation options, dependency query options, or skill document arguments.

## Version Command

The CLI MUST register the version command managed by `llm_tool_cli`, supplying the distribution name `depmesh`.
The library owns installed version lookup, help, configuration independence, protocol selection, version-cell output, and exit and failure behavior.

## Errors and exit codes

Skill- and version-command failure handling MUST be managed by `llm_tool_cli`.
The remaining execution policies apply to tool-owned commands.

The CLI SHOULD use these exit codes:

- `0` — command completed successfully.
- `1` — invalid command line arguments.
- `2` — configuration could not be discovered, resolved, loaded, parsed, validated, or created.
- `3` — dependency query failed.

Human and LLM error messages SHOULD be written to stderr.

The CLI MUST delegate typed environment-error cell construction and rendering to `llm_tool_cli`, including its common content, corrective guidance, and metadata contract.
Error content MUST now include corrective guidance when the error supplies it; native codes and diagnostic context retain their shared representation.
Depmesh MUST own stream selection and exit categories.

Shared configuration errors MUST exit with status `2`. Unmapped environment errors MUST exit with status `3`.

A failed result containing multiple environment errors MUST render every error in list order and use the first error's exit category. Technical exceptions MUST NOT be treated as expected failures.

Configuration selection, loading, and creation MUST propagate the diagnostics provided by `llm_tool_cli` without local translation.

For automation output, fatal errors SHOULD be written to stdout as an `error` record when possible and the process SHOULD still exit with a non-zero code.

If automation output cannot be initialized, fatal diagnostics MAY be written to stderr as human error cells. Depmesh-owned argument validation before command initialization MUST use this fallback.
Protocol-option parsing MUST use the diagnostics managed by `llm_tool_cli`.

Example automation fatal error:

```jsonl
{"code":"config_not_found","content":"/project: depmesh.toml was not found in this directory or its parents","id":"<cell-id>","path":"/project","reason":"depmesh.toml was not found in this directory or its parents","type":"error"}
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
