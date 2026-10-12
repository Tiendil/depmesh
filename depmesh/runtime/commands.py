from __future__ import annotations

from llm_tool_cli.cli import errors as cli_errors
from llm_tool_cli.config.project import project_config
from llm_tool_cli.core.result import Ok, Result, unwrap_to_error
from llm_tool_cli.paths import PathInput, resolve_project_root
from llm_tool_cli.paths.errors import InvalidProjectPath
from llm_tool_cli.protocol.logic_cells import ContentCell

from depmesh.core import warnings
from depmesh.discovery.entities import QueryResult
from depmesh.discovery.query import normalize_input_artifacts, query_dependencies, selected_relation_ids
from depmesh.domain.entities import ArtifactId, Dependency, RelationId
from depmesh.protocol.cells import DependenciesCell, relation_cells
from depmesh.workspace import Workspace


@unwrap_to_error
def dependencies(
    artifacts: list[ArtifactId],
    relation_filters: list[RelationId],
    *,
    workspace: Workspace,
    cwd: PathInput,
) -> Result[DependenciesCell]:
    project_dir = project_config.get().project_dir
    project_root = resolve_project_root(PathInput(project_dir)).unwrap()
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


def relations(*, workspace: Workspace) -> list[ContentCell]:
    return relation_cells(workspace.relations)
