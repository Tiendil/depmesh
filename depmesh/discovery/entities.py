from __future__ import annotations

import pydantic

from depmesh.core.entities import BaseEntity
from depmesh.discovery.predicates import ArtifactPredicate
from depmesh.discovery.sources import ArtifactSource
from depmesh.domain.entities import ArtifactId, Dependency, RelationId


class DependencyRule(BaseEntity):
    relation: RelationId
    input_predicate: ArtifactPredicate = pydantic.Field(
        validation_alias=pydantic.AliasChoices("input", "input_predicate"),
        serialization_alias="input",
    )
    output_source: ArtifactSource = pydantic.Field(
        validation_alias=pydantic.AliasChoices("output", "output_source"),
        serialization_alias="output",
    )

    @pydantic.model_validator(mode="after")
    def validate_templates(self) -> "DependencyRule":
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


class QueryResult(BaseEntity):
    dependencies: tuple[Dependency, ...]

    def grouped(self) -> dict[RelationId, list[ArtifactId]]:
        grouped: dict[RelationId, set[ArtifactId]] = {}

        for dependency in self.dependencies:
            grouped.setdefault(dependency.relation, set()).add(dependency.dependency)

        return {relation: sorted(dependencies) for relation, dependencies in sorted(grouped.items())}
