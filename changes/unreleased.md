
### Migration

- Consumers of configuration diagnostics must accept native `llm-tool-cli` error codes and `path`/`reason` fields. Invalid TOML, UTF-8, and schema data now use `config_invalid_toml`, `config_invalid_encoding`, and `config_validation_failed`; validation details moved from `validation` to `reason`. Configuration failures still exit with status `2`.
- Missing discovered configuration now uses the shared `config_not_found` message and `reason` field, with the search directory in `path`.

### Changes

- Obtain the TOML 1.1 parser and Pydantic through `llm-tool-cli`, which owns these shared dependencies.
- Use the shared `BaseEntity` directly for project models, preserving validation defaults and deep copy-with-changes behavior.
- Use shared configuration discovery, path resolution, TOML reading, and exclusive starter-file creation directly while preserving Depmesh configuration rules.
- Handle invalid UTF-8 configuration as a configuration error and resolve initialization correctly when given a relative working directory.
- Reuse the shared `InternalError` exception base and render returned shared configuration errors with their native diagnostics at the CLI boundary.
- Load configuration directly through the shared loader at the CLI boundary and construct runtime workspaces from validated models with `construct_workspace`.
- Report packaged starter template read failures separately from target configuration write failures.
- Select configuration through the shared locator before workspace construction, and expand home-relative explicit paths consistently for loading and initialization.
- Return expected operational failures through shared `Result`, `EnvironmentError`, and `EnvironmentErrors` across configuration, discovery, and CLI boundaries; preserve native diagnostics and warning recovery while keeping internal exceptions distinct. Predicate matching retains ordinary capture-or-`None` returns and exception propagation.
