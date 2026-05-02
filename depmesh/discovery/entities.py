from __future__ import annotations

import pydantic

from depmesh.core.entities import BaseEntity
from depmesh.discovery.expressions import DependencyExpression
from depmesh.discovery.matchers import ArtifactMatcher
from depmesh.domain.entities import ArtifactId, Dependency, RelationId


class DependencyRule(BaseEntity):
    relation: RelationId
    artifact: ArtifactMatcher
    dependency: DependencyExpression

    @pydantic.model_validator(mode="after")
    def validate_templates(self) -> "DependencyRule":
        dependency_variables = self.dependency.variables()

        missing = dependency_variables - self.artifact.captures()
        if missing:
            raise ValueError(
                f"dependency expression references capture `{sorted(missing)[0]}` "
                "that is not provided by every artifact matcher"
            )

        return self


class QueryResult(BaseEntity):
    dependencies: tuple[Dependency, ...]

    def grouped(self) -> dict[RelationId, list[ArtifactId]]:
        grouped: dict[RelationId, set[ArtifactId]] = {}

        for dependency in self.dependencies:
            grouped.setdefault(dependency.relation, set()).add(dependency.dependency)

        return {relation: sorted(dependencies) for relation, dependencies in sorted(grouped.items())}
