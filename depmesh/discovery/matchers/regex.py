from __future__ import annotations

import re
from pathlib import Path
from typing import Literal, NewType

from depmesh.core.entities import BaseEntity
from depmesh.discovery.matchers.entities import CaptureName
from depmesh.domain.entities import ArtifactId

RegexPattern = NewType("RegexPattern", str)


class RegexMatcher(BaseEntity):
    type: Literal["regex"]
    pattern: RegexPattern

    def captures(self) -> set[CaptureName]:
        try:
            return {CaptureName(name) for name in re.compile(self.pattern).groupindex}
        except re.error as error:
            raise ValueError(f"invalid regex matcher: {error}") from error

    def match(self, artifact: ArtifactId, root: Path) -> dict[str, str] | None:
        match = re.compile(self.pattern).match(artifact)
        return match.groupdict() if match else None
