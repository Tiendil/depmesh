from __future__ import annotations

from pathlib import Path
from typing import Annotated, NoReturn

import typer

from depmesh.cli import errors as cli_errors
from depmesh.core.entities import BaseEntity
from depmesh.domain.entities import ArtifactId, RelationId
from depmesh.protocol import OutputProtocol, renderer


class GlobalOptions(BaseEntity):
    protocol: OutputProtocol | None = None
    config: Path | None = None


def _exit_with_invalid_arguments(message: str) -> NoReturn:
    rendered = renderer(OutputProtocol.human).render_error(cli_errors.InvalidArguments(message).as_record())
    typer.echo(rendered, err=True, nl=False)
    raise typer.Exit(1)


def _parse_artifact(value: str) -> ArtifactId:
    return ArtifactId(value)


def _validate_artifacts(values: list[ArtifactId] | None) -> list[ArtifactId]:
    if not values:
        _exit_with_invalid_arguments("at least one artifact is required")
    return values


def _parse_config(value: str) -> Path:
    return Path(value)


def _parse_protocol(value: str) -> OutputProtocol:
    try:
        return OutputProtocol(value)
    except ValueError:
        choices = ", ".join(protocol.value for protocol in OutputProtocol)
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
    OutputProtocol | None,
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
