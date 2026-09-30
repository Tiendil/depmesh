from __future__ import annotations

from pathlib import Path
from typing import Annotated, NoReturn

import typer
from llm_tool_cli.protocol import Protocol
from llm_tool_cli.protocol.cell_shortcuts import environment_error
from llm_tool_cli.protocol.rendering import write_cells

from depmesh.cli import errors as cli_errors
from depmesh.domain.entities import ArtifactId, RelationId


def _exit_with_invalid_arguments(message: str) -> NoReturn:
    cell = environment_error(cli_errors.InvalidArguments(reason=message))
    write_cells([cell], protocol=Protocol.human, tool_label="DEPMESH", stderr=True)
    raise typer.Exit(1)


def _parse_artifact(value: str) -> ArtifactId:
    return ArtifactId(value)


def _validate_artifacts(values: list[ArtifactId] | None) -> list[ArtifactId]:
    if not values:
        _exit_with_invalid_arguments("at least one artifact is required")
    return values


def _parse_config(value: str) -> Path:
    return Path(value)


def _parse_protocol(value: str) -> Protocol:
    try:
        return Protocol(value)
    except ValueError:
        choices = ", ".join(protocol.value for protocol in Protocol)
        _exit_with_invalid_arguments(f"invalid protocol `{value}`; expected one of: {choices}")


def _parse_relation(value: str) -> RelationId:
    return RelationId(value)


ArtifactsArgument = Annotated[
    list[ArtifactId] | None,
    typer.Argument(
        metavar="ARTIFACT",
        parser=_parse_artifact,
        callback=_validate_artifacts,
    ),
]

ConfigOption = Annotated[
    Path | None,
    typer.Option(
        "--config",
        parser=_parse_config,
    ),
]

ProtocolOption = Annotated[
    Protocol | None,
    typer.Option(
        "-p",
        "--protocol",
        parser=_parse_protocol,
    ),
]

RelationOption = Annotated[
    list[RelationId] | None,
    typer.Option(
        "-r",
        "--relation",
        parser=_parse_relation,
    ),
]
