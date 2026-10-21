# CLI Interface

## Goal of the document

This document describes Depmesh's command-line interface.

## Scope

This specification covers CLI behavior.
The following are out of scope:

- discovery rules.
- relation properties/semantics.
- configuration semantics.
- exact skill prose.

The following concepts appear only to specify input/output boundaries:

- relations.
- ids.
- descriptions.
- configuration paths.

## General behavior

Depmesh exposes configured artifact dependencies through one CLI, independent of discovery mechanisms.
Its primary workflows query dependencies and list relations.
The root MUST expose a command group, never a direct query.
Global options MUST precede subcommands:
`depmesh [GLOBAL_OPTIONS] COMMAND [COMMAND_OPTIONS]`.

Artifacts initially represent file paths, but CLI syntax MUST NOT prevent future use of:

- directories.
- URLs.
- DOIs.
- ISBNs.
- other identifiers.

All cells MUST use stdout in every protocol, with environment-error delivery following the Command error handling contract in `specs/behavior/cli.md` in `llm-tool-cli`.
Automation cell/error stdout MUST contain only JSON Lines; help remains plain text.
Framework parsing MAY use ordinary non-JSON stderr diagnostics even under automation.

Payloads and order MUST be deterministic for the same:

- input.
- configuration.
- cwd.
- state.

Cell ids MUST follow `specs/behavior/protocol.md` in `llm-tool-cli` and MAY vary per invocation.
Configuration-dependent commands MUST select configuration before command behavior.
Skill, init, and version MUST NOT require existing configuration.

## Commands

These forms MUST be supported, with optional global options before commands:

- `dependencies [OPTIONS] ARTIFACT...`, `deps [OPTIONS] ARTIFACT...` — Query one or more artifacts.
- `relations`, `rels` — List relations.
- `skill [DOCUMENT]` — Built-in documentation.
- `init` — Starter configuration.
- `version` — Tool version.
- `--help` — Root help.

## Application identity

LLM cell framing MUST use `DEPMESH`, including error cells produced during argument parsing.
The default configuration filename MUST be `depmesh.toml`.

## Output behavior

Depmesh output MUST follow the cell formatting and delivery contracts in `specs/behavior/protocol.md` in `llm-tool-cli`.
Environment errors MUST follow that specification's Environment-error cells contract.
Output MUST NOT contain color, styling, or control sequences.
Expected output-delivery failures MUST be reported as command failures; unexpected failures MUST propagate.

Queries MUST treat input artifacts as relation left sides and return right-side artifacts.
Reverse queries MUST use separately configured relations/rules.
Results MUST merge all inputs, group by producing relation, and deduplicate within each relation.
Groups and their dependencies MUST each sort alphabetically.
Results MUST NOT group by input; callers needing that SHOULD query separately.
Relation lists MUST sort alphabetically.

Ordinary output MUST appear only after successful command completion; failure MUST suppress pending ordinary results.
Collected non-fatal problems MUST follow results or fatal diagnostics and SHOULD be warnings.
Dependency-result cells MUST remain ordinary output and MUST NOT be forwarded as journal events.

## Output protocols

Depmesh MUST support the `human`, `llm`, and `automation` protocols defined in `specs/behavior/protocol.md` in `llm-tool-cli`.
Human text SHOULD be compact/scannable; LLM text SHOULD be explicit, stable, and self-contained.

### Output cells

Equivalent data MUST produce equivalent payloads independent of ids.
The following projections MUST apply:

- Dependency group, human/LLM:

  - Kind: `dependencies`.
  - Metadata: `type = dependencies`, `relation`.
  - Content: one Markdown cell per nonempty group, with optional description then dependency list.

- Dependency, automation:

  - Kind: `dependency`.
  - Metadata: `type = dependency`, `relation`, `dependency`.
  - Content: metadata-only, one per merged entry.

- Warning, all protocols:

  - Kind: `warning`.
  - Metadata: `type = warning`, `message`.
  - Content: metadata-only, after dependencies in insertion order.

- Relation, all protocols:

  - Kind: `relation`.
  - Metadata: `type = relation`, `relation`.
  - Content: the optional description, using Markdown when present.

Empty dependency results without warnings and empty relation lists MUST emit no cells.
Output records MUST follow these field meanings:

- `id` means generated cell id.
- relation names use `relation`.
- document text uses `content`.
- metadata-only automation retains the protocol contract's absent-content representation.

`type` metadata MUST preserve record type because the protocol contract does not add kind.
Example ids are placeholders.

### Human output

Human output SHOULD use concise labels and canonical root-anchored paths for project inputs/dependencies.
It MUST follow the Human cells contract in `specs/behavior/protocol.md` in `llm-tool-cli`, with Depmesh metadata and without cell borders or generated ids.

### LLM output

Agents invoking Depmesh as a tool MUST use `llm`.
LLM output MUST be plain Markdown-compatible text.
It SHOULD be concise, nonredundant, and prefer stable ids/explicit paths over compact formatting.
Human/LLM dependency cells MUST identify relations in metadata and put configured descriptions before lists.
Absent descriptions MUST NOT produce placeholders or blank description paragraphs.

### Automation output

Automation MUST follow the JSON Lines contract in `specs/behavior/protocol.md` in `llm-tool-cli`, with stable fields and deterministic record order.
Warnings/errors SHOULD appear as records when part of output.
Records MUST have `type` identifying their semantic role.
Dependency, relation, and warning records MUST follow the output-cell contract above; utility-command and error records MUST follow the referenced library protocol contract.

Future fields MAY be added; consumers MUST ignore unknown fields.

## Global options

Global options MUST follow the configuration-option and protocol-option contracts in `specs/behavior/cli.md` in `llm-tool-cli`.
Each command's output MUST honor its effective protocol and selected project without inheriting another command's pending output.
Queries MUST use successfully validated configuration consistently through execution and output.

### Help and completion

Help aliases and completion MUST follow the Application setup contract in `specs/behavior/cli.md` in `llm-tool-cli`.

### `-p`, `--protocol PROTOCOL`

Parsing, defaults, and invalid-value diagnostics MUST follow the Protocol option and Protocol selection contracts in `specs/behavior/cli.md` in `llm-tool-cli`.
Cells/journals MUST honor the selected protocol.

### `--config PATH`

Parsing MUST defer filesystem validation as specified by the Configuration option contract in `specs/behavior/cli.md` in `llm-tool-cli`.
Configuration-using commands MUST select configuration using the option; filename/schema/root rules are in `specs/behavior/config.md`.

## Dependencies Command

`dependencies` and alias `deps` MUST query one or more artifacts and accept `-r`/`--relation RELATION_ID`.

### Argument `ARTIFACT...`

The command MUST accept one or more artifact identifiers and require at least one.
Project-file inputs MUST follow the Mixed path normalization contract in `specs/behavior/paths.md` in `llm-tool-cli`, using configuration root and invocation cwd for relative inputs.
Normalization MUST precede matching/output; missing targets MAY be referenced.
Examples/output SHOULD prefer canonical root-anchored ids except when demonstrating other forms.
Original spelling MUST remain in output where it helps identify the request; normalized/resolved ids MAY also appear.

### Option `-r`, `--relation RELATION_ID`

Filters MUST name configured relations and use their configured rules.
The option MAY repeat; output MUST include matches for any selected relation, or all relations when omitted.
**Example:** `depmesh deps -r imports -r tests @/src/main.py` includes both relations.

## Relations Command

`relations` and alias `rels` MUST list all configured relations sorted by id, without artifact/query arguments.
Every protocol MUST emit one cell per relation under `specs/behavior/protocol.md` in `llm-tool-cli`, with the relation id in metadata and its optional description in content rather than a `description` field.
Absent descriptions MUST produce no content or media type; automation MUST represent absent or empty content as null.

```json
{"content":"Tests related to the input artifacts.","id":"<id-1>","relation":"tests","type":"relation"}
```

### Example: multiple artifacts

If two inputs both depend on `@/src/shared.py` through `imports`, querying them together emits it once under `imports`, not once per input.
A separately configured `imported_by` relation queries the reverse direction.

### Example: human output with warnings

For `depmesh --protocol human deps @/src/main.py`:

```text
relation: imports

- @/src/shared.py

Warning: skipped unresolved dependency

```

### Example: LLM output with warnings

For the same query with `--protocol llm` and a configured relation description:

```text
--DEPMESH-CELL <id-1> BEGIN--
kind=dependencies
media_type=text/markdown
relation=imports
type=dependencies

Files imported by the input artifacts.

- @/src/shared.py
--DEPMESH-CELL <id-1> END--
--DEPMESH-CELL <id-2> BEGIN--
kind=warning
message=skipped unresolved dependency
type=warning
--DEPMESH-CELL <id-2> END--
```

### Example: automation output with warnings

For the same query with `--protocol automation`:

```jsonl
{"content":null,"dependency":"@/src/shared.py","id":"<id-1>","relation":"imports","type":"dependency"}
{"content":null,"id":"<id-2>","message":"skipped unresolved dependency","type":"warning"}
```

## Skill Command

The command MUST follow the Skill command contract in `specs/behavior/cli.md` in `llm-tool-cli` and offer documents `usage`, `configuration`, and `initialization`.
Document content MUST follow Depmesh's `specs/behavior/skill_fixtures.md`.

## Init Command

Init MUST follow the Initialization command contract in `specs/behavior/cli.md` in `llm-tool-cli`, using invocation cwd, optional `--config`, and default filename `depmesh.toml`.
The created file MUST pass Depmesh configuration validation before success is reported.
Failed validation MUST leave the file and report the contract's diagnostics without reporting success.

Generated TOML MUST:

- be valid.
- use version `1`.
- define `governed_by` and `governs`.
- include commented rule examples.

Success MUST emit the contract's creation acknowledgement with the created configuration path to stdout under the selected protocol.
The following arguments MUST NOT be accepted:

- artifact arguments.
- relation arguments.
- query arguments.
- skill arguments.

**Example:** `depmesh --config ./path/to/depmesh.toml init` selects an explicit target.

## Version Command

The command MUST report the installed version of distribution `depmesh` under the Version command contract in `specs/behavior/cli.md` in `llm-tool-cli`.

## Errors and exit codes

Commands MUST follow the Command error handling and Exit statuses contracts in `specs/behavior/cli.md` in `llm-tool-cli`.
Configuration diagnostics MUST propagate without translation.
Protocol-option parsing MUST retain the distinct diagnostics and fallback protocol required by that CLI contract.

**Example:** An automation missing-configuration error retains native fields:

```jsonl
{"code":"<diagnostic-code>","content":"/project: depmesh.toml was not found in this directory or its parents","id":"<cell-id>","path":"/project","reason":"depmesh.toml was not found in this directory or its parents","type":"error"}
```

## Compatibility rules

Compatibility SHOULD preserve:

- command names.
- options.
- protocols.
- JSONL types.
- field meanings.

New options, JSONL fields, and record types MAY be compatible additions.
Breaking changes MUST be specified before implementation.
