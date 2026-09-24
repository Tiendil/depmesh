from __future__ import annotations

import sys
from collections.abc import Iterator
from contextlib import contextmanager
from importlib import metadata
from pathlib import Path
from typing import Annotated, cast

import typer
from llm_tool_cli.config import errors as config_errors
from llm_tool_cli.config import load_config, locate_config
from llm_tool_cli.core import errors as shared_errors
from llm_tool_cli.core.errors import EnvironmentErrors
from llm_tool_cli.core.result import Ok, Result, UnwrapError, unwrap_to_error

from depmesh.cli import errors as cli_errors
from depmesh.cli.entities import ArtifactsArgument, ConfigOption, GlobalOptions, ProtocolOption, RelationOption
from depmesh.core import warnings
from depmesh.discovery import errors as discovery_errors
from depmesh.discovery.entities import QueryResult
from depmesh.discovery.paths import resolve_project_root
from depmesh.discovery.query import normalize_input_artifacts, query_dependencies, selected_relation_ids
from depmesh.domain.entities import Dependency, UntrustedPath
from depmesh.protocol import OutputProtocol, SkillDocument, renderer
from depmesh.protocol.renderers import Rendered
from depmesh.workspace import Config, Workspace, construct_workspace
from depmesh.workspace import errors as workspace_errors
from depmesh.workspace.config import CONFIG_FILE_NAME
from depmesh.workspace.init import initialize_config

EXIT_INVALID_ARGUMENTS = 1
EXIT_CONFIG = 2
EXIT_QUERY = 3
EXIT_PROJECT_ERROR = 3
GLOBAL_OPTIONS_CONTEXT_KEY = "depmesh_global_options"

app = typer.Typer(
    add_completion=False,
    context_settings={"help_option_names": ["-h", "--help"]},
    help="Inspect configured relations and dependencies.",
    no_args_is_help=False,
)


def main() -> None:
    app()


@app.callback()
def root(
    context: typer.Context,
    protocol: ProtocolOption = None,
    config: ConfigOption = None,
) -> None:
    context.meta[GLOBAL_OPTIONS_CONTEXT_KEY] = GlobalOptions(protocol=protocol, config=config)


@app.command("dependencies")
@app.command("deps")
def dependencies(
    context: typer.Context,
    artifacts: ArtifactsArgument = None,
    relation: RelationOption = None,
) -> None:
    relations = relation or []

    with command_context(context, default_protocol=OutputProtocol.human) as command:
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
                        if isinstance(error, discovery_errors.InvalidProjectPath)
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
        command.write(
            command.renderer.render_query(
                result,
                warnings.read(),
                relations=workspace.relations,
            )
        )


@app.command("relations")
@app.command("rels")
def relations(context: typer.Context) -> None:
    with command_context(context, default_protocol=OutputProtocol.human) as command:
        workspace = command.load_workspace().unwrap()
        command.write(command.renderer.render_relations(workspace.relations))


@app.command("skill")
def skill(
    context: typer.Context,
    document: Annotated[SkillDocument, typer.Argument()] = SkillDocument.usage,
) -> None:
    with command_context(context, default_protocol=OutputProtocol.llm) as command:
        command.write(command.renderer.render_skill(document).unwrap())


@app.command("init")
def init(context: typer.Context) -> None:
    with command_context(context, default_protocol=OutputProtocol.human) as command:
        config_path = initialize_config(command.global_options.config).unwrap()
        command.write(f"created {config_path}\n")


@app.command("version")
def version(context: typer.Context) -> None:
    with command_context(context, default_protocol=OutputProtocol.human) as command:
        command.write(metadata.version("depmesh") + "\n")


class CommandContext:
    __slots__ = ("global_options", "protocol", "renderer")

    def __init__(self, context: typer.Context, *, default_protocol: OutputProtocol) -> None:
        self.global_options = _global_options(context)
        self.protocol = self.global_options.protocol or default_protocol
        self.renderer: Rendered = renderer(self.protocol)

    @unwrap_to_error
    def load_workspace(self) -> Result[Workspace, EnvironmentErrors]:
        config_path = locate_config(CONFIG_FILE_NAME, path=self.global_options.config, cwd=Path.cwd()).unwrap()
        config = load_config(config_path, Config).unwrap()
        return Ok(construct_workspace(config, root=config_path.parent))

    def write(self, text: str) -> None:
        sys.stdout.write(text)

    def render_fatal(self, error: shared_errors.EnvironmentError) -> None:
        rendered = self.renderer.render_error(error.as_record())

        if self.protocol is OutputProtocol.automation:
            sys.stdout.write(rendered)
        else:
            sys.stderr.write(rendered)


@contextmanager
def command_context(
    context: typer.Context,
    *,
    default_protocol: OutputProtocol,
) -> Iterator[CommandContext]:
    warnings.clear()
    command_context = CommandContext(context, default_protocol=default_protocol)

    try:
        yield command_context
    except UnwrapError as error:
        failures = cast(EnvironmentErrors, error.details["error"])
        for failure in failures:
            command_context.render_fatal(failure)
        first = failures[0]
        if isinstance(first, cli_errors.EnvironmentError):
            exit_code = EXIT_INVALID_ARGUMENTS
        elif isinstance(first, (workspace_errors.EnvironmentError, config_errors.EnvironmentError)):
            exit_code = EXIT_CONFIG
        else:
            exit_code = EXIT_PROJECT_ERROR
        raise typer.Exit(exit_code) from error
    raise typer.Exit(0)


def _global_options(context: typer.Context) -> GlobalOptions:
    global_options = context.find_root().meta.get(GLOBAL_OPTIONS_CONTEXT_KEY)
    if isinstance(global_options, GlobalOptions):
        return global_options
    return GlobalOptions()
