from __future__ import annotations

from depmesh.discovery.artifacts import EvaluationContext, TemplateText
from depmesh.discovery.sources.base import ArtifactSourceBase, ArtifactSourceConfigBase
from depmesh.discovery.sources.command import CommandSource
from depmesh.discovery.sources.compiler import compile_source
from depmesh.discovery.sources.difference import DifferenceSource
from depmesh.discovery.sources.entities import (
    ArtifactSourceConfig,
    CommandSourceConfig,
    DifferenceSourceConfig,
    FilesSourceConfig,
    FilterSourceConfig,
    IntersectionSourceConfig,
    ListSourceConfig,
    UnionSourceConfig,
)
from depmesh.discovery.sources.files import FilesSource
from depmesh.discovery.sources.filter import FilterSource
from depmesh.discovery.sources.intersection import IntersectionSource
from depmesh.discovery.sources.list import ListSource
from depmesh.discovery.sources.union import UnionSource

__all__ = [
    "ArtifactSourceBase",
    "ArtifactSourceConfig",
    "ArtifactSourceConfigBase",
    "CommandSource",
    "CommandSourceConfig",
    "DifferenceSource",
    "DifferenceSourceConfig",
    "EvaluationContext",
    "FilesSource",
    "FilesSourceConfig",
    "FilterSource",
    "FilterSourceConfig",
    "IntersectionSource",
    "IntersectionSourceConfig",
    "ListSource",
    "ListSourceConfig",
    "TemplateText",
    "UnionSource",
    "UnionSourceConfig",
    "compile_source",
]
