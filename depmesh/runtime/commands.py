from __future__ import annotations

from llm_tool_cli.cli import errors as cli_errors
from llm_tool_cli.config import initialize_config, load_config, locate_config
from llm_tool_cli.core.result import Ok, Result, unwrap_to_error
from llm_tool_cli.paths import PathInput, ProjectConfigPath, resolve_project_root
from llm_tool_cli.paths.errors import InvalidProjectPath
from llm_tool_cli.protocol.cell_shortcuts import configuration_created
from llm_tool_cli.protocol.logic_cells import ContentCell

from depmesh.core import warnings
from depmesh.discovery.entities import QueryResult
from depmesh.discovery.query import normalize_input_artifacts, query_dependencies, selected_relation_ids
from depmesh.domain.entities import ArtifactId, Dependency, RelationId
from depmesh.protocol.cells import DependenciesCell, relation_cells
from depmesh.workspace import Config, Workspace, construct_workspace
from depmesh.workspace.config import CONFIG_FILE_NAME


@unwrap_to_error
def dependencies(
    artifacts: list[ArtifactId],
    relation_filters: list[RelationId],
    *,
    cwd: PathInput,
    config_path: ProjectConfigPath | None = None,
) -> Result[DependenciesCell]:
    workspace = _load_workspace(cwd=cwd, config_path=config_path).unwrap()
    project_root = resolve_project_root(PathInput(workspace.root)).unwrap()
    relation_ids = selected_relation_ids(workspace.relations_by_id, relation_filters).unwrap()
    dependencies: set[Dependency] = set()

    input_artifacts = (
        normalize_input_artifacts(project_root, artifacts, cwd=cwd)
        .map_err(
            lambda failures: [
                (
                    cli_errors.InvalidArguments(reason=error.format_message())
                    if isinstance(error, InvalidProjectPath)
                    else error
                )
                for error in failures
            ]
        )
        .unwrap()
    )

    for artifact in input_artifacts:
        result = query_dependencies(
            project_root,
            workspace.relations_by_id,
            workspace.rules,
            artifact,
            relation_ids=relation_ids,
            cwd=cwd,
        ).unwrap()
        dependencies.update(result.dependencies)

    result = QueryResult(dependencies=tuple(sorted(dependencies, key=lambda item: (item.relation, item.dependency))))
    return Ok(DependenciesCell(result=result, warnings=warnings.read(), relations=workspace.relations))


@unwrap_to_error
def relations(*, cwd: PathInput, config_path: ProjectConfigPath | None = None) -> Result[list[ContentCell]]:
    workspace = _load_workspace(cwd=cwd, config_path=config_path).unwrap()
    return Ok(relation_cells(workspace.relations))


@unwrap_to_error
def initialize(*, cwd: PathInput, config_path: ProjectConfigPath | None = None) -> Result[ContentCell]:
    path = initialize_config(
        CONFIG_FILE_NAME,
        package="depmesh.workspace",
        template="base_config.toml",
        cwd=cwd,
        path=config_path,
    ).unwrap()
    return Ok(configuration_created(path))


@unwrap_to_error
def _load_workspace(*, cwd: PathInput, config_path: ProjectConfigPath | None) -> Result[Workspace]:
    path = locate_config(CONFIG_FILE_NAME, path=config_path, cwd=cwd).unwrap()
    config = load_config(path, Config).unwrap()
    return Ok(construct_workspace(config, root=path.parent))
