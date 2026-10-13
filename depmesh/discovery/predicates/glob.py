from __future__ import annotations

from llm_tool_cli.paths import FileGlobPattern, ProjectPathId, ProjectRootPath, match_glob
from llm_tool_cli.paths.errors import InvalidProjectPath

from depmesh.discovery.predicates.base import ArtifactPredicateBase
from depmesh.discovery.predicates.entities import GlobPredicateConfig
from depmesh.domain.entities import ArtifactId


class GlobPredicate(ArtifactPredicateBase):
    __slots__ = ("config",)

    def __init__(self, config: GlobPredicateConfig) -> None:
        self.config = config

    def match(
        self,
        artifact: ArtifactId,
        root: ProjectRootPath,
        captures: dict[str, str] | None = None,
    ) -> dict[str, str] | None:
        pattern = FileGlobPattern(self.config.pattern.substitute(captures or {}))
        result = match_glob(ProjectPathId(artifact), pattern, root)
        if result.is_err(InvalidProjectPath):
            return None
        return result.unwrap()


__all__ = ["GlobPredicate", "GlobPredicateConfig"]
