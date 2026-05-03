from __future__ import annotations

from typing import Annotated, Literal

import pydantic

from depmesh.discovery.artifacts import CaptureName, TemplateText
from depmesh.discovery.predicates.entities import ArtifactPredicateConfig
from depmesh.discovery.sources.base import ArtifactSourceConfigBase


class FilesSourceConfig(ArtifactSourceConfigBase):
    type: Literal["files"]
    pattern: TemplateText | None = None

    def variables(self) -> set[CaptureName]:
        return set(self.pattern.variables) if self.pattern is not None else set()


class CommandSourceConfig(ArtifactSourceConfigBase):
    type: Literal["command"]
    command: TemplateText

    def variables(self) -> set[CaptureName]:
        return set(self.command.variables)


class ListSourceConfig(ArtifactSourceConfigBase):
    type: Literal["list"]
    artifacts: tuple[TemplateText, ...] = pydantic.Field(min_length=1)

    def variables(self) -> set[CaptureName]:
        return set().union(*(artifact.variables for artifact in self.artifacts))


class UnionSourceConfig(ArtifactSourceConfigBase):
    type: Literal["union"]
    items: tuple[ArtifactSourceConfig, ...] = pydantic.Field(min_length=1)

    def variables(self) -> set[CaptureName]:
        return set().union(*(item.variables() for item in self.items))


class IntersectionSourceConfig(ArtifactSourceConfigBase):
    type: Literal["intersection"]
    items: tuple[ArtifactSourceConfig, ...] = pydantic.Field(min_length=1)

    def variables(self) -> set[CaptureName]:
        return set().union(*(item.variables() for item in self.items))


class DifferenceSourceConfig(ArtifactSourceConfigBase):
    type: Literal["difference"]
    include: ArtifactSourceConfig
    exclude: ArtifactSourceConfig

    def variables(self) -> set[CaptureName]:
        return self.include.variables() | self.exclude.variables()


class FilterSourceConfig(ArtifactSourceConfigBase):
    type: Literal["filter"]
    source: ArtifactSourceConfig
    predicate: ArtifactPredicateConfig

    def variables(self) -> set[CaptureName]:
        return self.source.variables() | self.predicate.variables()


ArtifactSourceConfig = Annotated[
    FilesSourceConfig
    | CommandSourceConfig
    | ListSourceConfig
    | UnionSourceConfig
    | IntersectionSourceConfig
    | DifferenceSourceConfig
    | FilterSourceConfig,
    pydantic.Field(discriminator="type"),
]

UnionSourceConfig.model_rebuild(_types_namespace={"ArtifactSourceConfig": ArtifactSourceConfig})
IntersectionSourceConfig.model_rebuild(_types_namespace={"ArtifactSourceConfig": ArtifactSourceConfig})
DifferenceSourceConfig.model_rebuild(_types_namespace={"ArtifactSourceConfig": ArtifactSourceConfig})
FilterSourceConfig.model_rebuild(_types_namespace={"ArtifactSourceConfig": ArtifactSourceConfig})


__all__ = [
    "ArtifactSourceConfig",
    "ArtifactSourceConfigBase",
    "CommandSourceConfig",
    "DifferenceSourceConfig",
    "FilesSourceConfig",
    "FilterSourceConfig",
    "IntersectionSourceConfig",
    "ListSourceConfig",
    "UnionSourceConfig",
]
