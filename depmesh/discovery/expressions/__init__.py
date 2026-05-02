from __future__ import annotations

from typing import Annotated

import pydantic

from depmesh.discovery.expressions.command import CommandExpression
from depmesh.discovery.expressions.entities import EvaluationContext, TemplateText
from depmesh.discovery.expressions.glob import GlobExpression
from depmesh.discovery.expressions.intersection import IntersectionExpression
from depmesh.discovery.expressions.path import PathExpression
from depmesh.discovery.expressions.regex import RegexExpression
from depmesh.discovery.expressions.union import UnionExpression

DependencyExpression = Annotated[
    PathExpression | GlobExpression | RegexExpression | CommandExpression | UnionExpression | IntersectionExpression,
    pydantic.Field(discriminator="type"),
]

UnionExpression.model_rebuild(_types_namespace={"DependencyExpression": DependencyExpression})
IntersectionExpression.model_rebuild(_types_namespace={"DependencyExpression": DependencyExpression})

__all__ = [
    "CommandExpression",
    "DependencyExpression",
    "EvaluationContext",
    "GlobExpression",
    "IntersectionExpression",
    "PathExpression",
    "RegexExpression",
    "TemplateText",
    "UnionExpression",
]
