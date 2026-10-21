Part of Depmesh functionality moved to the shared `llm_tool_cli` library to unify behavior among a family of LLM-oriented CLI tools (currently `donna` and `depmesh`). As a result, we introduced some behavior changes.

No changes are required in configuration files.

### Migration

Due to massive refactoring, it is difficult to list all changes that may affect existing scripts and integrations. The following list highlights the most important directions for migration:

- Some exit codes for errors have changed. You may need to validate scripts that check exit codes.
- Some error ids have changed. You may need to validate scripts that check error ids.
- Human output now uses readable text blocks without cell framing; LLM output retains explicit cell framing. Use `automation` protocol if you need to parse output programmatically.
- In `relations`/`rels` output, read relation descriptions from `content` instead of `description`. Automation content is no longer always null for relation records.
- Review configured glob predicates and file sources, their grammar where updated. See changes for details.

### Changes

- `llm_tool_cli` added as a dependency, part of Depmesh's functionality moved to this library. As the result, a lot of small behavior changes were introduced.
- Exit codes for expected command failures now: `1` for invalid arguments, `2` for configuration errors, and `3` for other environment errors.
- Human output uses readable metadata and content blocks, with dedicated error and warning presentations; LLM output retains cell framing.
- Relation listings put descriptions in content in every protocol, displaying relation ids before their descriptions in human output.
- All output now goes to stdout.
- Updated grammar of glob predicates and file sources:

  - Predicates interpret bracket character classes such as `[ab]`; use `[[]` when a literal `[` is intended.
  - File-source wildcards include hidden files and directories. Add an explicit filter if those entries should be excluded.
  - Embedded `**` in file-source patterns can span directories: `@/src/a**.py` can match `@/src/a/nested.py`. Use `*` when matching must stay within one path segment.

- Filesystem home markers are now expanded consistently in query inputs and configured path expressions; use `@/~/...` for a literal project directory named `~`. Empty project-path inputs are rejected rather than interpreted as a directory base.
