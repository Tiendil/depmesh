
### Migration

- Failed commands with multiple diagnostics now exit with the highest declared error code instead of the first error's category. Python integrations must replace `EXIT_CONFIG`, `EXIT_QUERY`, and `EXIT_PROJECT_ERROR` from `depmesh.cli.application` with `llm_tool_cli.core.entities.ExitCode.configuration_error` or `ExitCode.environment_error` as appropriate.

- Replace the removed `depmesh.workspace.init.initialize_config` with `llm_tool_cli.config.initialize_config`, passing `"depmesh.toml"`, `package="depmesh.workspace"`, `template="base_config.toml"`, a `PathInput` working directory, and an optional keyword-only `ProjectConfigPath` target.

- Import `InvalidArguments` from `llm_tool_cli.cli.errors` instead of the removed `depmesh.cli.errors` module. Use the shared concrete type when classifying invalid arguments; the local CLI environment-error root is removed.

- Python integrations must register version commands through `llm_tool_cli.cli.commands.version.register_version_command` instead of calling the removed `depmesh.cli.application.version`.

- Python integrations must register skill commands through `llm_tool_cli.cli.commands.skills.register_skill_command` instead of calling the removed `depmesh.cli.application.skill`. Import `ExitCode` from `llm_tool_cli.cli.entities` and use `ExitCode.invalid_arguments` instead of `EXIT_INVALID_ARGUMENTS`.

- Python integrations that bypass CLI `main()` must initialize `llm_tool_cli.core.settings` with `ToolLabel("DEPMESH")` before cell output or argument parsing. Tests can request `isolated_settings` from `llm_tool_cli.core.tests.fixtures` before initializing the label; pytest-mock restores prior settings afterward. Remove `tool_label` arguments from shared sequence rendering and writing.

- Pass `llm_tool_cli.paths.ProjectConfigPath` to `initialize_config` in Python integrations.

- Import `GlobalOptions` from `llm_tool_cli.cli.entities`, rename its `config` field to `config_path`, and supply `ProjectConfigPath`. Use `protocol_for(command_name)` for protocol selection; command contexts no longer accept `default_protocol`.

- Malformed result-unwrapping payloads now propagate as the original `UnwrapError` without rendering partial diagnostics or failing later during rendering. Recover diagnostics through the shared `UnwrapError.errors` accessor.

- Import `llm_tool_cli.config.errors.TemplateUnreadable` instead of the removed `depmesh.workspace.errors.ConfigTemplateUnreadable`. The unused local workspace error module is removed. Template-read diagnostics gain the target `path`, retaining their code, message, template, reason, exit status, and stream routing.

- Replace `depmesh.skills.fixtures.load_skill_text(document)` with `llm_tool_cli.skills.load_skill_text(package="depmesh.skills", document=document.value)`. Import `SkillUnreadable` from `llm_tool_cli.skills.errors`; its `document` field is the document name string. The local loader and error modules are removed.

- `depmesh version` now emits a version cell in the selected protocol instead of a bare version line. Scripts should use `depmesh -p automation version` and read the JSON record's `version` field; `id` is generated and `content` is null.

- Shared error shortcuts now retain the structured error in `EnvironmentErrorCell` until projection. Error content includes corrective guidance when supplied; codes, context, stream routing, ordering, and exit categories retain their shared contracts.

- Fatal errors now use ordinary cell framing in human and LLM output. Automation gains a generated `id` and moves the formatted error message from `message` to `content`, retaining native codes and diagnostic context through shared cell metadata conversion. Stream routing and exit categories remain unchanged; argument failures before command initialization use human error cells on stderr.

- Python integrations using `query_cells` must construct `DependenciesCell(result=..., relations=..., warnings=...)` and pass it to shared `render_cells` with `protocol` after initializing shared application settings. `relation_cells` returns shared content logic cells and no longer accepts `cell_type`.
- Replace `depmesh.protocol.cells.skill_cell(document)` with application-owned document loading followed by `llm_tool_cli.protocol.cell_shortcuts.skill(document.value, content)`.
- Import `ContentCell` from `llm_tool_cli.protocol.logic_cells` and `LogicCell` from `llm_tool_cli.protocol.logic_cells.base`; the shared `protocol.cells` module is removed.
- Command results now use shared cells with `DEPMESH` text framing and random identifiers. Automation cells include `id` and `content`; relation names move from `id` to `relation`, and skill text moves from `text` to `content`. Initialization now honors the selected protocol and emits an `operation_succeeded` cell with `path`. Ignore cell identifiers when comparing repeated results; payloads and ordering remain deterministic. Exit codes, help, and version retain their existing contracts.
- Python integrations must replace the removed `depmesh.protocol.renderers` family and `depmesh.protocol.utils.renderer` with Depmesh logic-cell construction and `llm_tool_cli.protocol.rendering.render_cells(cells, protocol=...)`. `CommandContext.write_cells` accepts logic cells; the separate `write_logic_cell` method and `cell_type` property are removed.

- Import `Protocol` from `llm_tool_cli.protocol` instead of `depmesh.protocol.OutputProtocol`, and import `to_jsonl` from the shared protocol package. Automation JSON now uses compact separators without optional whitespace; generic serialization is owned by the shared library.
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

- Use the shared command error context manager and explicit reporter for command failures and early argument validation; preserve diagnostic payloads, ordering, stream routing, exit statuses, and unexpected exception propagation.

- Delegate environment-error exit-code declarations and aggregation to `llm_tool_cli`, preserving diagnostic order, cell payloads, and streams while making exit status independent of error order.

- Use the shared configuration-creation success cell for `init`, preserving its message, path metadata, output protocols, and exit behavior.

- Call shared configuration-file initialization directly from `init`, preserving the packaged starter, created-path success metadata, diagnostics, and exit behavior; remove the local initializer module.

- Use the shared invalid-argument diagnostic for artifact validation and preserve existing error messages, cell fields, streams, and exit categories.

- Delegate the complete version command to `llm_tool_cli`, preserving installed package lookup, output protocols, configuration independence, and exit behavior. Use common version help text and correct the usage documentation to describe existing version-cell output.

- Use shared application construction and help aliases, and enable `--show-completion` and `--install-completion`. Delegate the entire skill command to `llm_tool_cli`, preserving Depmesh's documents, output protocols, and read-failure behavior.
- Use the shared `ExitCode` enum for success and explicit invalid arguments. Reset invocation warnings in the root callback so shared commands retain warning isolation.

- Use the shared `core.tests.fixtures.isolated_settings` pytest fixture for test isolation; production settings no longer provide a scoped override.

- Initialize the shared `DEPMESH` tool label once at CLI startup and use it for all cell output, including early argument diagnostics. Use the shared `ProtocolOption` annotation without repeating labels.

- Delegate protocol option parsing and help to `llm_tool_cli`. Unsupported values now emit an LLM error cell on stderr instead of a human cell, preserving `invalid_arguments` and exit status `1`.

- Use shared `--config` parsing from `llm_tool_cli`, with a semantic configuration path and common option help; filesystem validation remains deferred to configuration operations.

- Obtain Typer and its version constraint through `llm_tool_cli`, retaining the locked 0.25.1 version.

- Delegate Typer context storage and retrieval of global options to `llm_tool_cli`, preserving CLI behavior and invocation isolation.

- Delegate initialization target selection and resolution to `llm_tool_cli`, preserving explicit paths, current-directory defaults, and the rule against upward discovery.

- Delegate global CLI options and protocol-default selection to `llm_tool_cli`, preserving LLM output for `skill`, human output for other commands, and explicit protocol overrides.

- Delegate result-unwrapping payload recovery to the shared library, preserving valid error lists, ordering, stream routing, and exit categories.

- Delegate starter-template reading and exclusive configuration creation to the shared library, preserving templates, target selection, and successful output.

- Load skill documents directly through the shared library, preserving document selection, content, native diagnostics, stream routing, and exit codes.

- Use the shared version-cell shortcut for every output protocol, preserving configuration-free execution and exit status zero on success.

- Delegate command and early argument-error cell emission to the shared writer, preserving protocol output, stream routing, and exit codes.

- Use the shared successful-operation record type default for initialization output, preserving the existing payload and configuration path.

- Construct skill cells directly through the shared shortcut, preserving document selection, output payloads, protocol defaults, and loading-error handling.

- Adopt shared typed environment-error cells with deferred metadata and guidance rendering, and verify their CLI integration in every protocol.

- Emit dependencies, relations, skills, messages, and errors through one shared logic-cell projection and rendering path. Keep existing cell payloads, ordering, stream routing, and exit behavior.

- Separate dependency-result data and protocol projections through the shared `LogicCell` base; preserve existing payloads, ordering, and shared formatting through `OutputCell`.
- Return protocol-specific shared output cells from dependency projections and render complete sequences with shared position and total context. Construct environment errors as ordinary shared cells with native codes and diagnostic metadata. Keep dependency content grouped by relation for human/LLM output, individual dependency records for automation, and domain-specific cell construction in Depmesh.

- Use shared output modes, compact Unicode JSON Lines serialization, and direct text writing while preserving command defaults, warning behavior, and exit policies.
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
