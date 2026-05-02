from __future__ import annotations

from typing import NewType

from depmesh.core.entities import BaseEntity

ArtifactId = NewType("ArtifactId", str)
RelationDescription = NewType("RelationDescription", str)
RelationId = NewType("RelationId", str)


class Relation(BaseEntity):
    id: RelationId
    description: RelationDescription | None = None


class Dependency(BaseEntity):
    relation: RelationId
    dependency: ArtifactId
