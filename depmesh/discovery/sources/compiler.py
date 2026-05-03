from __future__ import annotations

from typing import assert_never

from depmesh.discovery.predicates.compiler import compile_predicate
from depmesh.discovery.sources.base import ArtifactSourceBase
from depmesh.discovery.sources.command import CommandSource
from depmesh.discovery.sources.difference import DifferenceSource
from depmesh.discovery.sources.entities import ArtifactSourceConfig
from depmesh.discovery.sources.files import FilesSource
from depmesh.discovery.sources.filter import FilterSource
from depmesh.discovery.sources.intersection import IntersectionSource
from depmesh.discovery.sources.list import ListSource
from depmesh.discovery.sources.union import UnionSource


def compile_source(config: ArtifactSourceConfig) -> ArtifactSourceBase:
    match config.type:
        case "files":
            return FilesSource(config)
        case "command":
            return CommandSource(config)
        case "list":
            return ListSource(config)
        case "union":
            return UnionSource(config, tuple(compile_source(item) for item in config.items))
        case "intersection":
            return IntersectionSource(config, tuple(compile_source(item) for item in config.items))
        case "difference":
            return DifferenceSource(
                config,
                include=compile_source(config.include),
                exclude=compile_source(config.exclude),
            )
        case "filter":
            return FilterSource(config, compile_source(config.source), compile_predicate(config.predicate))

    assert_never(config)


__all__ = ["compile_source"]
