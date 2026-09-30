from __future__ import annotations

from typing import Annotated, NoReturn

import typer
from llm_tool_cli.cli import errors as cli_errors
from llm_tool_cli.cli.entities import ExitCode
from llm_tool_cli.protocol import Protocol
from llm_tool_cli.protocol.cell_shortcuts import environment_error
from llm_tool_cli.protocol.rendering import write_cells

from depmesh.domain.entities import ArtifactId, RelationId


def _exit_with_invalid_arguments(message: str) -> NoReturn:
    cell = environment_error(cli_errors.InvalidArguments(reason=message))
    write_cells([cell], protocol=Protocol.human, stderr=True)
    raise typer.Exit(ExitCode.invalid_arguments)


def _parse_artifact(value: str) -> ArtifactId:
    return ArtifactId(value)


def _validate_artifacts(values: list[ArtifactId] | None) -> list[ArtifactId]:
    if not values:
        _exit_with_invalid_arguments("at least one artifact is required")
    return values


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

RelationOption = Annotated[
    list[RelationId] | None,
    typer.Option(
        "-r",
        "--relation",
        parser=_parse_relation,
    ),
]
