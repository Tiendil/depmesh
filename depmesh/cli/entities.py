from __future__ import annotations

from typing import Annotated

import typer
from llm_tool_cli.cli import errors as cli_errors
from llm_tool_cli.cli.handling import report_errors_and_exit
from llm_tool_cli.protocol import Protocol

from depmesh.domain.entities import ArtifactId, RelationId


def _parse_artifact(value: str) -> ArtifactId:
    return ArtifactId(value)


def _validate_artifacts(values: list[ArtifactId] | None) -> list[ArtifactId]:
    if not values:
        report_errors_and_exit(
            [cli_errors.InvalidArguments(reason="at least one artifact is required")], protocol=Protocol.human
        )
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
