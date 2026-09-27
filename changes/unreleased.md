
### Migration

- Import `Protocol` from `llm_tool_cli.protocol` instead of `depmesh.protocol.OutputProtocol`, and import `to_jsonl` from the shared protocol package. Automation JSON now uses compact separators without optional whitespace; record fields and meanings are unchanged.
- Use `.` instead of an empty project-path input to refer to a directory base below the project root; empty inputs now report `invalid_project_path`.
- Import `UntrustedPath` directly from `llm_tool_cli.paths` instead of `depmesh.domain.entities`.
- Import `normalize_path` directly from `llm_tool_cli.paths` in Python integrations. Query inputs, list sources, command output, one-of predicates, glob predicates, and file-source patterns now expand filesystem home markers; use `@/~/...` for a literal project directory named `~`.
- Import `resolve_project_path` from `llm_tool_cli.paths` instead of `depmesh.discovery.paths`; invalid paths now return `InvalidProjectPath` errors rather than `Ok(None)`. Home-expansion failures return `PathResolutionFailed` errors.
- Replace `depmesh.discovery.paths.normalize_existing_path` with `llm_tool_cli.paths.project_path_id_from_filesystem` in Python integrations.
- Import `ProjectRootPath` and `resolve_project_root` from `llm_tool_cli.paths`, and project-path `PathResolutionFailed` from `llm_tool_cli.paths.errors` instead of local modules.
- Python integrations must use `Result[T]` instead of `Result[T, EnvironmentErrors]`; the shared result always carries `EnvironmentErrors` on failure.
- Consumers of configuration diagnostics must accept native `llm-tool-cli` error codes and `path`/`reason` fields. Invalid TOML, UTF-8, and schema data now use `config_invalid_toml`, `config_invalid_encoding`, and `config_validation_failed`; validation details moved from `validation` to `reason`. Configuration failures still exit with status `2`.
- Missing discovered configuration now uses the shared `config_not_found` message and `reason` field, with the search directory in `path`.

### Changes

- Use shared output modes, compact Unicode JSON Lines serialization, and direct text writing while preserving native records, command defaults, warning behavior, and exit policies.
- Reject empty project-path inputs through the shared normalizer instead of interpreting them as an explicit directory base; invalid glob patterns retain no-match handling.
- Use the shared `UntrustedPath` semantic type for filesystem inputs, preserving runtime path behavior.
- Use the shared project-path resolver directly for file-source patterns, preserving warning-and-skip handling of invalid patterns and propagating resolution failures.
- Use shared mixed path normalization directly, with home expansion and `path_resolution_failed` diagnostics when expansion fails. Relative roots without an explicit base now produce absolute filesystem candidate paths in containment diagnostics.
- Share filesystem-to-identifier conversion through `llm-tool-cli`, preserving file discovery results and resolution diagnostics.
- Convert resolved filesystem paths to canonical identifiers through `llm-tool-cli` directly, preserving public path results and diagnostics.
- Resolve root-anchored identifiers through `llm-tool-cli` directly, preserving invalid-candidate recovery and filesystem failure diagnostics.
- Use shared filesystem containment and resolved-path types directly, preserving invalid-path recovery and resolution-failure propagation; containment diagnostics now use the filesystem candidate path.
- Use shared filesystem project-root resolution and resolution errors directly, preserving diagnostic records, private causes, and CLI exit categories.
- Use shared lexical `@/` path normalization, canonical identifier types, and invalid-path errors directly from `llm-tool-cli`, preserving filesystem resolution and CLI diagnostics.
- Use shared result error matching for invalid-path recovery while preserving filesystem failure propagation.
- Adopt the shared result interface with one type parameter across discovery, configuration, CLI, and rendering code.
- Obtain the TOML 1.1 parser and Pydantic through `llm-tool-cli`, which owns these shared dependencies.
- Use the shared `BaseEntity` directly for project models, preserving validation defaults and deep copy-with-changes behavior.
- Use shared configuration discovery, path resolution, TOML reading, and exclusive starter-file creation directly while preserving Depmesh configuration rules.
- Handle invalid UTF-8 configuration as a configuration error and resolve initialization correctly when given a relative working directory.
- Reuse the shared `InternalError` exception base and render returned shared configuration errors with their native diagnostics at the CLI boundary.
- Load configuration directly through the shared loader at the CLI boundary and construct runtime workspaces from validated models with `construct_workspace`.
- Report packaged starter template read failures separately from target configuration write failures.
- Select configuration through the shared locator before workspace construction, and expand home-relative explicit paths consistently for loading and initialization.
- Return expected operational failures through shared `Result`, `EnvironmentError`, and `EnvironmentErrors` across configuration, discovery, and CLI boundaries; preserve native diagnostics and warning recovery while keeping internal exceptions distinct. Predicate matching retains ordinary capture-or-`None` returns and exception propagation.
