from __future__ import annotations

import re

from depmesh.discovery.predicates.base import ArtifactPredicateBase
from depmesh.discovery.predicates.entities import GlobPattern, GlobPredicateConfig, parse_glob_capture
from depmesh.discovery.paths import normalize_path_pattern
from depmesh.domain.entities import ArtifactId, ProjectRootPath


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
        pattern = self.config.pattern.substitute(captures or {})
        normalized_pattern = normalize_path_pattern(pattern, root)
        if normalized_pattern is None:
            return None
        match = _compile_glob(normalized_pattern).fullmatch(artifact)
        return {name: value or "" for name, value in match.groupdict().items()} if match else None


def _compile_glob(pattern: str) -> re.Pattern[str]:
    regex = ["^"]
    index = 0

    while index < len(pattern):
        character = pattern[index]

        if character == "*":
            if index + 1 < len(pattern) and pattern[index + 1] == "*":
                if index + 2 < len(pattern) and pattern[index + 2] == "/":
                    regex.append("(?:.*/)?")
                    index += 3
                else:
                    regex.append(".*")
                    index += 2
            else:
                regex.append("[^/]*")
                index += 1
            continue

        if character == "?":
            regex.append("[^/]")
            index += 1
            continue

        if character == "{":
            end = pattern.find("}", index)
            if end == -1:
                regex.append(re.escape(character))
                index += 1
                continue

            token = pattern[index + 1 : end]
            if not token.startswith("*"):
                regex.append(re.escape(pattern[index : end + 1]))
                index = end + 1
                continue

            wildcard, name = parse_glob_capture(token)

            if wildcard == "**":
                if end + 1 < len(pattern) and pattern[end + 1] == "/":
                    regex.append(f"(?:(?P<{name}>.*)/)?")
                    index = end + 2
                else:
                    regex.append(f"(?P<{name}>.*)")
                    index = end + 1
                continue

            regex.append(f"(?P<{name}>[^/]*)")
            index = end + 1
            continue

        regex.append(re.escape(character))
        index += 1

    regex.append("$")
    return re.compile("".join(regex))


__all__ = ["GlobPattern", "GlobPredicate", "GlobPredicateConfig"]
