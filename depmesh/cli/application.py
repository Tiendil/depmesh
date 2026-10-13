from __future__ import annotations

from pathlib import Path

import typer
from llm_tool_cli.cli.application import create_app
from llm_tool_cli.cli.commands.initialization import register_init_command
from llm_tool_cli.cli.commands.skills import register_skill_command
from llm_tool_cli.cli.commands.version import register_version_command
from llm_tool_cli.cli.context import command_context
from llm_tool_cli.config import load_project
from llm_tool_cli.core import settings
from llm_tool_cli.paths import PathInput

from depmesh.cli.entities import ArtifactsArgument, RelationOption
from depmesh.protocol import SkillDocument
from depmesh.runtime import commands
from depmesh.workspace import Config, construct_workspace

app = create_app(help="Inspect configured relations and dependencies.")
register_skill_command(app, package="depmesh.skills", documents=SkillDocument)
register_version_command(app, distribution="depmesh")
register_init_command(app, config_class=Config, package="depmesh.workspace", template="base_config.toml")


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
        commands.dependencies(
            artifacts or [],
            relation or [],
            workspace=workspace,
            cwd=cwd,
        ).unwrap()


@app.command("relations")
@app.command("rels")
def relations(context: typer.Context) -> None:
    with command_context(context) as command:
        config = context.with_resource(
            load_project(Config, cwd=PathInput(Path.cwd()), path=command.config_input)
        ).unwrap()
        workspace = construct_workspace(config)
        commands.relations(workspace=workspace).unwrap()
