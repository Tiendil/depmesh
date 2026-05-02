from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Literal

from depmesh.core.entities import BaseEntity
from depmesh.discovery.artifacts import CaptureName
from depmesh.domain.entities import ArtifactId

if TYPE_CHECKING:
    from depmesh.discovery.predicates import ArtifactPredicate


class NotPredicate(BaseEntity):
    type: Literal["not"]
    item: ArtifactPredicate

    def variables(self) -> set[CaptureName]:
        return self.item.variables()

    def captures(self) -> set[CaptureName]:
        return set()

    def match(self, artifact: ArtifactId, root: Path, captures: dict[str, str] | None = None) -> dict[str, str] | None:
        return {} if self.item.match(artifact, root, captures) is None else None
