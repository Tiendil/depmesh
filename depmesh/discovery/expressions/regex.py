from __future__ import annotations

import re
from typing import Literal

from depmesh.core.entities import BaseEntity
from depmesh.discovery.expressions.entities import EvaluationContext, TemplateText
from depmesh.discovery.matchers import CaptureName
from depmesh.discovery.paths import normalize_existing_path
from depmesh.domain.entities import ArtifactId


class RegexExpression(BaseEntity):
    type: Literal["regex"]
    pattern: TemplateText

    def variables(self) -> set[CaptureName]:
        return set(self.pattern.variables)

    def evaluate(self, context: EvaluationContext) -> list[ArtifactId]:
        pattern = self.pattern.substitute(context.captures)
        regex = re.compile(pattern)

        return [
            ArtifactId(normalize_existing_path(path, context.root))
            for path in sorted(context.root.rglob("*"))
            if path.is_file() and regex.search(normalize_existing_path(path, context.root))
        ]
