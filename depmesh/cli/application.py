from __future__ import annotations

import sys
from collections.abc import Iterator
from contextlib import contextmanager
from importlib import metadata
from pathlib import Path
from typing import Annotated

import typer

from depmesh.cli import errors as cli_errors
from depmesh.cli.entities import ArtifactsArgument, ConfigOption, GlobalOptions, ProtocolOption, RelationOption
from depmesh.core import errors as core_errors
from depmesh.core import warnings
from depmesh.discovery import errors as discovery_errors
from depmesh.discovery.entities import QueryResult
from depmesh.discovery.paths import resolve_project_root
from depmesh.discovery.query import normalize_input_artifacts, query_dependencies, selected_relation_ids
from depmesh.domain.entities import Dependency, UntrustedPath
from depmesh.protocol import OutputProtocol, renderer
from depmesh.protocol.renderers import Rendered
from depmesh.skills.entities import SkillDocument
from depmesh.workspace import errors as workspace_errors
from depmesh.workspace.config import load_config
from depmesh.workspace.entities import Workspace
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
        workspace = command.load_workspace()
        project_root = resolve_project_root(UntrustedPath(Path(workspace.root)))
        cwd = UntrustedPath(Path.cwd())
        relation_ids = selected_relation_ids(workspace.relations_by_id, relations)
        dependencies: set[Dependency] = set()

        try:
            input_artifacts = normalize_input_artifacts(project_root, artifacts, cwd=cwd)
        except discovery_errors.InvalidProjectPath as error:
            raise cli_errors.InvalidArguments(error.message) from error

        for artifact in input_artifacts:
            result = query_dependencies(
                project_root,
                workspace.relations_by_id,
                workspace.rules,
                artifact,
                relation_ids=relation_ids,
                cwd=cwd,
            )
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
        workspace = command.load_workspace()
        command.write(command.renderer.render_relations(workspace.relations))


@app.command("skill")
def skill(
    context: typer.Context,
    document: Annotated[SkillDocument, typer.Argument()] = SkillDocument.usage,
) -> None:
    with command_context(context, default_protocol=OutputProtocol.llm) as command:
        command.write(command.renderer.render_skill(document))


@app.command("init")
def init(context: typer.Context) -> None:
    with command_context(context, default_protocol=OutputProtocol.human) as command:
        config_path = initialize_config(command.global_options.config)
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

    def load_workspace(self) -> Workspace:
        return load_config(self.global_options.config)

    def write(self, text: str) -> None:
        sys.stdout.write(text)

    def render_fatal(self, error: core_errors.Error) -> None:
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
        raise typer.Exit(0)

    except cli_errors.Error as error:
        command_context.render_fatal(error)
        raise typer.Exit(EXIT_INVALID_ARGUMENTS) from error
    except workspace_errors.Error as error:
        command_context.render_fatal(error)
        raise typer.Exit(EXIT_CONFIG) from error
    except discovery_errors.Error as error:
        command_context.render_fatal(error)
        raise typer.Exit(EXIT_QUERY) from error
    except core_errors.Error as error:
        command_context.render_fatal(error)
        raise typer.Exit(EXIT_PROJECT_ERROR) from error


def _global_options(context: typer.Context) -> GlobalOptions:
    global_options = context.find_root().meta.get(GLOBAL_OPTIONS_CONTEXT_KEY)
    if isinstance(global_options, GlobalOptions):
        return global_options
    return GlobalOptions()
