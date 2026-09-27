from __future__ import annotations

from pathlib import Path
from typing import NewType

from llm_tool_cli.core.entities import BaseEntity
from llm_tool_cli.paths import ProjectRootPath

ArtifactId = NewType("ArtifactId", str)
RelationDescription = NewType("RelationDescription", str)
RelationId = NewType("RelationId", str)
UntrustedPath = NewType("UntrustedPath", Path)
PathInput = UntrustedPath | ProjectRootPath


class Relation(BaseEntity):
    id: RelationId
    description: RelationDescription | None = None


class Dependency(BaseEntity):
    relation: RelationId
    dependency: ArtifactId
