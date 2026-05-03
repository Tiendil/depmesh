from __future__ import annotations

from typing import Annotated

import pydantic

from depmesh.discovery.artifacts import EvaluationContext, TemplateText
from depmesh.discovery.sources.base import ArtifactSourceBase
from depmesh.discovery.sources.command import CommandSource
from depmesh.discovery.sources.difference import DifferenceSource
from depmesh.discovery.sources.files import FilesSource
from depmesh.discovery.sources.filter import FilterSource
from depmesh.discovery.sources.intersection import IntersectionSource
from depmesh.discovery.sources.list import ListSource
from depmesh.discovery.sources.union import UnionSource

ArtifactSource = Annotated[
    FilesSource | CommandSource | ListSource | UnionSource | IntersectionSource | DifferenceSource | FilterSource,
    pydantic.Field(discriminator="type"),
]

UnionSource.model_rebuild(_types_namespace={"ArtifactSource": ArtifactSource})
IntersectionSource.model_rebuild(_types_namespace={"ArtifactSource": ArtifactSource})
DifferenceSource.model_rebuild(_types_namespace={"ArtifactSource": ArtifactSource})
FilterSource.model_rebuild(_types_namespace={"ArtifactSource": ArtifactSource})

__all__ = [
    "ArtifactSource",
    "ArtifactSourceBase",
    "CommandSource",
    "DifferenceSource",
    "EvaluationContext",
    "FilesSource",
    "FilterSource",
    "IntersectionSource",
    "ListSource",
    "TemplateText",
    "UnionSource",
]
