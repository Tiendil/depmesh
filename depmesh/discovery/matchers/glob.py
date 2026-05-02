from __future__ import annotations

import re
from pathlib import Path
from typing import Literal, NewType

from depmesh.core.entities import BaseEntity
from depmesh.discovery.matchers.entities import CaptureName
from depmesh.domain.entities import ArtifactId

GlobPattern = NewType("GlobPattern", str)

CAPTURE_NAME_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
CAPTURE_RE = re.compile(r"\{([^{}]+)\}")


class GlobMatcher(BaseEntity):
    type: Literal["glob"]
    pattern: GlobPattern

    def captures(self) -> set[CaptureName]:
        return {CaptureName(_parse_capture(token)[1]) for token in CAPTURE_RE.findall(self.pattern)}

    def match(self, artifact: ArtifactId, root: Path) -> dict[str, str] | None:
        match = _compile_glob(self.pattern).fullmatch(artifact)
        return {name: value or "" for name, value in match.groupdict().items()} if match else None


def _parse_capture(token: str) -> tuple[str, str]:
    if token.startswith("**"):
        wildcard = "**"
        name = token[2:]
    elif token.startswith("*"):
        wildcard = "*"
        name = token[1:]
    else:
        raise ValueError(f"invalid glob capture `{token}`")

    if not CAPTURE_NAME_RE.fullmatch(name):
        raise ValueError(f"invalid glob capture name `{name}`")

    return wildcard, name


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

            wildcard, name = _parse_capture(pattern[index + 1 : end])

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
