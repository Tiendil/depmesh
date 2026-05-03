from __future__ import annotations

import pydantic

from depmesh.core.entities import BaseEntity
from depmesh.discovery.predicates.base import ArtifactPredicateBase
from depmesh.discovery.predicates.compiler import compile_predicate
from depmesh.discovery.predicates.entities import ArtifactPredicateConfig
from depmesh.discovery.sources.base import ArtifactSourceBase
from depmesh.discovery.sources.compiler import compile_source
from depmesh.discovery.sources.entities import ArtifactSourceConfig
from depmesh.domain.entities import ArtifactId, Dependency, RelationId


class DependencyRuleConfig(BaseEntity):
    relation: RelationId
    input_predicate: ArtifactPredicateConfig = pydantic.Field(  # type: ignore[pydantic-alias]
        validation_alias=pydantic.AliasChoices("input", "input_predicate"),
        serialization_alias="input",
    )
    output_source: ArtifactSourceConfig = pydantic.Field(  # type: ignore[pydantic-alias]
        validation_alias=pydantic.AliasChoices("output", "output_source"),
        serialization_alias="output",
    )

    @pydantic.model_validator(mode="after")
    def validate_templates(self) -> "DependencyRuleConfig":
        input_variables = self.input_predicate.variables()
        if input_variables:
            raise ValueError(f"input predicate references unknown capture `{sorted(input_variables)[0]}`")

        output_variables = self.output_source.variables()

        missing = output_variables - self.input_predicate.captures()
        if missing:
            raise ValueError(
                f"output source references capture `{sorted(missing)[0]}` "
                "that is not provided by every input predicate"
            )

        return self


class DependencyRule(BaseEntity):
    model_config = pydantic.ConfigDict(arbitrary_types_allowed=True)

    relation: RelationId
    input_predicate: ArtifactPredicateBase
    output_source: ArtifactSourceBase


def compile_dependency_rule(config: DependencyRuleConfig) -> DependencyRule:
    return DependencyRule(
        relation=config.relation,
        input_predicate=compile_predicate(config.input_predicate),
        output_source=compile_source(config.output_source),
    )


class QueryResult(BaseEntity):
    dependencies: tuple[Dependency, ...]

    def grouped(self) -> dict[RelationId, list[ArtifactId]]:
        grouped: dict[RelationId, set[ArtifactId]] = {}

        for dependency in self.dependencies:
            grouped.setdefault(dependency.relation, set()).add(dependency.dependency)

        return {relation: sorted(dependencies) for relation, dependencies in sorted(grouped.items())}
