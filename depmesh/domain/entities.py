from __future__ import annotations

from pathlib import Path
from typing import NewType

from depmesh.core.entities import BaseEntity

ArtifactId = NewType("ArtifactId", str)
ProjectRootPath = NewType("ProjectRootPath", Path)
ProjectPathId = NewType("ProjectPathId", str)
RelationDescription = NewType("RelationDescription", str)
RelationId = NewType("RelationId", str)
ResolvedProjectPath = NewType("ResolvedProjectPath", Path)
UntrustedPath = NewType("UntrustedPath", Path)
PathInput = UntrustedPath | ProjectRootPath


class Relation(BaseEntity):
    id: RelationId
    description: RelationDescription | None = None


class Dependency(BaseEntity):
    relation: RelationId
    dependency: ArtifactId
