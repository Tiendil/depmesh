from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

import typer
from llm_tool_cli.cli.application import create_app
from llm_tool_cli.cli.commands.skills import register_skill_command
from llm_tool_cli.cli.commands.version import register_version_command
from llm_tool_cli.cli.context import CommandContext
from llm_tool_cli.cli.handling import handle_command_errors
from llm_tool_cli.config import initialize_project, load_project
from llm_tool_cli.config.project import project_config
from llm_tool_cli.core import settings
from llm_tool_cli.paths import PathInput
from llm_tool_cli.protocol.cell_shortcuts import configuration_created

from depmesh.cli.entities import ArtifactsArgument, RelationOption
from depmesh.protocol import SkillDocument
from depmesh.runtime import commands
from depmesh.workspace import Config, construct_workspace

app = create_app(help="Inspect configured relations and dependencies.")
register_skill_command(app, package="depmesh.skills", documents=SkillDocument)
register_version_command(app, distribution="depmesh")


def main() -> None:
    settings.initialize(label=settings.ToolLabel("DEPMESH"), config_filename=settings.ConfigFilename("depmesh.toml"))
    app()


@app.command("dependencies")
@app.command("deps")
def dependencies(
    context: typer.Context,
    artifacts: ArtifactsArgument = None,
    relation: RelationOption = None,
) -> None:
    with command_context(context) as command:
        cwd = PathInput(Path.cwd())
        config = context.with_resource(load_project(Config, cwd=cwd, path=command.config_input)).unwrap()
        workspace = construct_workspace(config)
        cell = commands.dependencies(
            artifacts or [],
            relation or [],
            workspace=workspace,
            cwd=cwd,
        ).unwrap()
        command.write_cells([cell])


@app.command("relations")
@app.command("rels")
def relations(context: typer.Context) -> None:
    with command_context(context) as command:
        config = context.with_resource(
            load_project(Config, cwd=PathInput(Path.cwd()), path=command.config_input)
        ).unwrap()
        workspace = construct_workspace(config)
        cells = commands.relations(workspace=workspace)
        command.write_cells(cells)


@app.command("init")
def init(context: typer.Context) -> None:
    with command_context(context) as command:
        context.with_resource(
            initialize_project(
                Config,
                package="depmesh.workspace",
                template="base_config.toml",
                cwd=PathInput(Path.cwd()),
                path=command.config_input,
            )
        ).unwrap()
        command.write_cells([configuration_created(project_config.get().config_path)])


@contextmanager
def command_context(context: typer.Context) -> Iterator[CommandContext]:
    command_context = CommandContext(context)

    with handle_command_errors(protocol=command_context.protocol):
        yield command_context
