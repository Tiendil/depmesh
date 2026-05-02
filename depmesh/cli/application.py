from __future__ import annotations

import sys
from importlib import metadata
from pathlib import Path

import typer

from depmesh.cli import errors as cli_errors
from depmesh.cli.entities import ArtifactsArgument, ConfigOption, GlobalOptions, ProtocolOption, RelationOption
from depmesh.core import errors as core_errors
from depmesh.core import warnings
from depmesh.discovery import errors as discovery_errors
from depmesh.discovery.query import query_dependencies
from depmesh.protocol import OutputProtocol, renderer
from depmesh.workspace import errors as workspace_errors
from depmesh.workspace.config import load_config

EXIT_INVALID_ARGUMENTS = 1
EXIT_CONFIG = 2
EXIT_QUERY = 3
EXIT_PROJECT_ERROR = 3
GLOBAL_OPTIONS_CONTEXT_KEY = "depmesh_global_options"

app = typer.Typer(
    add_completion=False,
    context_settings={"help_option_names": ["-h", "--help"]},
    help="Print configured dependencies for one or more artifacts.",
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


@app.command("show")
def show(
    context: typer.Context,
    artifacts: ArtifactsArgument = None,
    relation: RelationOption = None,
) -> None:
    warnings.clear()

    global_options = _global_options(context)
    relations = relation or []
    selected_protocol = global_options.protocol or OutputProtocol.human
    selected_renderer = renderer(selected_protocol)

    try:
        workspace = load_config(global_options.config)
        result = query_dependencies(
            Path(workspace.root),
            workspace.relations_by_forward_id,
            workspace.relations_by_backward_id,
            workspace.rules,
            artifacts,
            relation_filters=relations,
            cwd=Path.cwd(),
        )
        sys.stdout.write(
            selected_renderer.render_query(
                result,
                warnings.read(),
                relations=workspace.relations,
            )
        )
        raise typer.Exit(0)

    except cli_errors.Error as error:
        _render_fatal(error, protocol=selected_protocol)
        raise typer.Exit(EXIT_INVALID_ARGUMENTS) from error
    except workspace_errors.Error as error:
        _render_fatal(error, protocol=selected_protocol)
        raise typer.Exit(EXIT_CONFIG) from error
    except discovery_errors.Error as error:
        _render_fatal(error, protocol=selected_protocol)
        raise typer.Exit(EXIT_QUERY) from error
    except core_errors.Error as error:
        _render_fatal(error, protocol=selected_protocol)
        raise typer.Exit(EXIT_PROJECT_ERROR) from error


@app.command("skill")
def skill(context: typer.Context) -> None:
    warnings.clear()

    global_options = _global_options(context)
    selected_protocol = global_options.protocol or OutputProtocol.llm

    sys.stdout.write(renderer(selected_protocol).render_skill())
    raise typer.Exit(0)


@app.command("version")
def version(context: typer.Context) -> None:
    warnings.clear()
    _global_options(context)

    sys.stdout.write(metadata.version("depmesh") + "\n")
    raise typer.Exit(0)


def _global_options(context: typer.Context) -> GlobalOptions:
    global_options = context.find_root().meta.get(GLOBAL_OPTIONS_CONTEXT_KEY)
    if isinstance(global_options, GlobalOptions):
        return global_options
    return GlobalOptions()


def _render_fatal(error: core_errors.Error, *, protocol: OutputProtocol) -> None:
    rendered = renderer(protocol).render_error(error.as_record())

    if protocol is OutputProtocol.automation:
        sys.stdout.write(rendered)
    else:
        sys.stderr.write(rendered)
