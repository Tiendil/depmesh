from __future__ import annotations

import re
from collections.abc import Mapping
from functools import cached_property
from typing import NewType

import pydantic

from depmesh.domain.entities import ProjectRootPath, RelationId, UntrustedPath

CaptureName = NewType("CaptureName", str)

TEMPLATE_RE = re.compile(r"\{([A-Za-z_][A-Za-z0-9_]*)\}")


class TemplateText(pydantic.RootModel[str]):
    model_config = pydantic.ConfigDict(
        str_strip_whitespace=True,
        validate_default=True,
        frozen=True,
    )

    root: str

    @property
    def value(self) -> str:
        return self.root

    def __str__(self) -> str:
        return self.value

    @cached_property
    def variables(self) -> frozenset[CaptureName]:
        return frozenset(CaptureName(name) for name in TEMPLATE_RE.findall(self.value))

    def substitute(self, captures: Mapping[str, str]) -> str:
        return TEMPLATE_RE.sub(lambda match: captures[match.group(1)], self.value)


class EvaluationContext:
    __slots__ = ("captures", "cwd", "relation_id", "root")

    def __init__(
        self,
        *,
        root: ProjectRootPath,
        relation_id: RelationId,
        captures: dict[str, str],
        cwd: UntrustedPath | None = None,
    ) -> None:
        self.root = root
        self.relation_id = relation_id
        self.captures = captures
        self.cwd = cwd
