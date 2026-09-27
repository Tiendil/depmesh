from __future__ import annotations

from typing import NewType

from llm_tool_cli.core.entities import BaseEntity
from llm_tool_cli.paths import ProjectRootPath, UntrustedPath

ArtifactId = NewType("ArtifactId", str)
RelationDescription = NewType("RelationDescription", str)
RelationId = NewType("RelationId", str)
PathInput = UntrustedPath | ProjectRootPath


class Relation(BaseEntity):
    id: RelationId
    description: RelationDescription | None = None


class Dependency(BaseEntity):
    relation: RelationId
    dependency: ArtifactId
