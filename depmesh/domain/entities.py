from __future__ import annotations

from typing import NewType

from depmesh.core.entities import BaseEntity

ArtifactId = NewType("ArtifactId", str)
RelationDescription = NewType("RelationDescription", str)
RelationId = NewType("RelationId", str)


class Relation(BaseEntity):
    forward_id: RelationId
    backward_id: RelationId
    forward_description: RelationDescription | None = None
    backward_description: RelationDescription | None = None


class Dependency(BaseEntity):
    relation: RelationId
    dependency: ArtifactId
