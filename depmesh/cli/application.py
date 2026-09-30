from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

import typer
from llm_tool_cli.cli import errors as cli_errors
from llm_tool_cli.cli.application import create_app
from llm_tool_cli.cli.commands.skills import register_skill_command
from llm_tool_cli.cli.commands.version import register_version_command
from llm_tool_cli.cli.context import CommandContext as BaseCommandContext
from llm_tool_cli.cli.handling import handle_command_errors
from llm_tool_cli.config import initialize_config, load_config, locate_config
from llm_tool_cli.core import settings
from llm_tool_cli.core.result import Ok, Result, unwrap_to_error
from llm_tool_cli.paths import PathInput, UntrustedPath, resolve_project_root
from llm_tool_cli.paths.errors import InvalidProjectPath
from llm_tool_cli.protocol.cell_shortcuts import configuration_created

from depmesh.cli.entities import ArtifactsArgument, RelationOption
from depmesh.core import warnings
from depmesh.discovery.entities import QueryResult
from depmesh.discovery.query import normalize_input_artifacts, query_dependencies, selected_relation_ids
from depmesh.domain.entities import Dependency
from depmesh.protocol import SkillDocument
from depmesh.protocol.cells import DependenciesCell, relation_cells
from depmesh.workspace import Config, Workspace, construct_workspace
from depmesh.workspace.config import CONFIG_FILE_NAME

app = create_app(help="Inspect configured relations and dependencies.")
register_skill_command(app, package="depmesh.skills", documents=SkillDocument)
register_version_command(app, distribution="depmesh")


def main() -> None:
    settings.initialize(tool_label=settings.ToolLabel("DEPMESH"))
    app()


@app.command("dependencies")
@app.command("deps")
def dependencies(
    context: typer.Context,
    artifacts: ArtifactsArgument = None,
    relation: RelationOption = None,
) -> None:
    relations = relation or []

    with command_context(context) as command:
        workspace = command.load_workspace().unwrap()
        project_root = resolve_project_root(UntrustedPath(Path(workspace.root))).unwrap()
        cwd = UntrustedPath(Path.cwd())
        relation_ids = selected_relation_ids(workspace.relations_by_id, relations).unwrap()
        dependencies: set[Dependency] = set()

        input_artifacts = (
            normalize_input_artifacts(project_root, artifacts or [], cwd=cwd)
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

        result = QueryResult(
            dependencies=tuple(sorted(dependencies, key=lambda item: (item.relation, item.dependency)))
        )
        command.write_cells([DependenciesCell(result=result, warnings=warnings.read(), relations=workspace.relations)])


@app.command("relations")
@app.command("rels")
def relations(context: typer.Context) -> None:
    with command_context(context) as command:
        workspace = command.load_workspace().unwrap()
        command.write_cells(relation_cells(workspace.relations))


@app.command("init")
def init(context: typer.Context) -> None:
    with command_context(context) as command:
        config_path = initialize_config(
            CONFIG_FILE_NAME,
            package="depmesh.workspace",
            template="base_config.toml",
            cwd=PathInput(Path.cwd()),
            path=command.global_options.config_path,
        ).unwrap()
        command.write_cells([configuration_created(config_path)])


class CommandContext(BaseCommandContext):
    __slots__ = ()

    @unwrap_to_error
    def load_workspace(self) -> Result[Workspace]:
        config_path = locate_config(CONFIG_FILE_NAME, path=self.global_options.config_path, cwd=Path.cwd()).unwrap()
        config = load_config(config_path, Config).unwrap()
        return Ok(construct_workspace(config, root=config_path.parent))


@contextmanager
def command_context(context: typer.Context) -> Iterator[CommandContext]:
    command_context = CommandContext(context)

    with handle_command_errors(protocol=command_context.protocol):
        yield command_context
