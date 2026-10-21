from __future__ import annotations

from typing import Annotated

import typer

from depmesh.domain.entities import ArtifactId, RelationId


def _parse_artifact(value: str) -> ArtifactId:
    return ArtifactId(value)


def _parse_relation(value: str) -> RelationId:
    return RelationId(value)


ArtifactsArgument = Annotated[
    list[ArtifactId],
    typer.Argument(
        metavar="ARTIFACT",
        parser=_parse_artifact,
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
