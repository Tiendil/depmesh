# Skill Fixtures

## Goal of the document

This document describes the structure and content requirements for built-in skill documentation fixtures.

Built-in skill fixtures are Markdown files embedded in the package and printed by `depmesh skill`.

## Scope

The scope of this specification is limited to built-in skill documentation fixture files.

The following topics are out of scope:

- exact fixture prose.
- CLI option parsing.
- output protocol rendering.
- project configuration semantics beyond examples needed in documentation.
- external Codex or agent skill installation.

## Fixture location

Built-in skill documentation fixtures MUST live under:

```text
./depmesh/skills/fixtures/
```

Each fixture MUST be a UTF-8 Markdown file.

Each fixture SHOULD be loaded through `./depmesh/skills/fixtures.py` instead of direct filesystem reads from CLI or renderer code.

## Fixture set

The built-in fixture set MUST include one document per documentation area:

- `usage.md` - general `depmesh` command usage.
- `configuration.md` - `depmesh.toml` configuration syntax and examples.
- `initialization.md` - project initialization workflow and starter-rule heuristics.

Each fixture MUST start with a level-one heading that identifies the document:

```markdown
# `depmesh` Usage
# `depmesh` Configuration
# `depmesh` Initialization
```

## Usage fixture

The usage fixture MUST describe how to invoke `depmesh` commands and interpret their output.

It MUST describe how to access the other built-in skill documents.

It MUST NOT describe configuration syntax beyond command names that print configuration-related documentation.

It MUST NOT tell an agent when or why to use `depmesh`; that decision belongs to the user or surrounding workflow.

## Configuration fixture

The configuration fixture MUST describe `depmesh.toml` structure.

It SHOULD include examples for:

- relation definitions.
- dependency rules.
- supported artifact predicates.
- supported artifact sources.
- captures and template variables.
- directional reverse relations.

The configuration fixture MUST keep examples compatible with the implemented configuration schema.

## Initialization fixture

The initialization fixture MUST describe how to create a starter configuration.

It MUST mention the `depmesh init` command.

It MUST describe that initialization does not overwrite an existing configuration file.

It SHOULD include basic heuristics for filling configuration rules in a new project.

It SHOULD guide readers to write relation descriptions that describe the returned artifacts and clarify the queried artifact role.

It SHOULD include examples such as:

- governance relations between specifications and implementation artifacts.
- Python import relations based on static import analysis.
- predictable test mapping relations.

## Style

Fixtures MUST be written as tool documentation.

Fixtures SHOULD use concise Markdown sections, command examples, TOML examples, and representative output examples.

Fixtures SHOULD prefer stable command forms and implemented behavior over speculative features.

Fixtures MUST NOT require readers to inspect source code or specifications to understand documented command usage.
