from __future__ import annotations

import re
from typing import Annotated, Literal, NewType

import pydantic

from depmesh.discovery.artifacts import CaptureName, TemplateText
from depmesh.discovery.predicates.base import ArtifactPredicateConfigBase

GlobPattern = NewType("GlobPattern", str)
OneOfPredicateValue = NewType("OneOfPredicateValue", str)
RegexPattern = NewType("RegexPattern", str)

CAPTURE_NAME_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
CAPTURE_RE = re.compile(r"\{([^{}]+)\}")


class OneOfPredicateConfig(ArtifactPredicateConfigBase):
    type: Literal["one_of"]
    artifacts: tuple[TemplateText, ...] = pydantic.Field(min_length=1)

    def variables(self) -> set[CaptureName]:
        return set().union(*(artifact.variables for artifact in self.artifacts))


class GlobPredicateConfig(ArtifactPredicateConfigBase):
    type: Literal["glob"]
    pattern: TemplateText

    def variables(self) -> set[CaptureName]:
        return set(self.pattern.variables)

    def captures(self) -> set[CaptureName]:
        return {
            CaptureName(parse_glob_capture(token)[1])
            for token in CAPTURE_RE.findall(self.pattern.value)
            if token.startswith("*")
        }


class RegexPredicateConfig(ArtifactPredicateConfigBase):
    type: Literal["regex"]
    pattern: TemplateText

    def variables(self) -> set[CaptureName]:
        return set(self.pattern.variables)

    def captures(self) -> set[CaptureName]:
        try:
            return {CaptureName(name) for name in re.compile(self.pattern.value).groupindex}
        except re.error as error:
            raise ValueError(f"invalid regex predicate: {error}") from error


class AnyPredicateConfig(ArtifactPredicateConfigBase):
    type: Literal["any"]
    items: tuple[ArtifactPredicateConfig, ...] = pydantic.Field(min_length=1)

    def variables(self) -> set[CaptureName]:
        return set().union(*(item.variables() for item in self.items))

    def captures(self) -> set[CaptureName]:
        captures = [item.captures() for item in self.items]
        return set.intersection(*captures) if captures else set()


class AllPredicateConfig(ArtifactPredicateConfigBase):
    type: Literal["all"]
    items: tuple[ArtifactPredicateConfig, ...] = pydantic.Field(min_length=1)

    def variables(self) -> set[CaptureName]:
        return set().union(*(item.variables() for item in self.items))

    def captures(self) -> set[CaptureName]:
        return set().union(*(item.captures() for item in self.items))


class NotPredicateConfig(ArtifactPredicateConfigBase):
    type: Literal["not"]
    item: ArtifactPredicateConfig

    def variables(self) -> set[CaptureName]:
        return self.item.variables()


ArtifactPredicateConfig = Annotated[
    OneOfPredicateConfig
    | GlobPredicateConfig
    | RegexPredicateConfig
    | AnyPredicateConfig
    | AllPredicateConfig
    | NotPredicateConfig,
    pydantic.Field(discriminator="type"),
]

AnyPredicateConfig.model_rebuild(_types_namespace={"ArtifactPredicateConfig": ArtifactPredicateConfig})
AllPredicateConfig.model_rebuild(_types_namespace={"ArtifactPredicateConfig": ArtifactPredicateConfig})
NotPredicateConfig.model_rebuild(_types_namespace={"ArtifactPredicateConfig": ArtifactPredicateConfig})


def parse_glob_capture(token: str) -> tuple[str, str]:
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


__all__ = [
    "AllPredicateConfig",
    "AnyPredicateConfig",
    "ArtifactPredicateConfig",
    "ArtifactPredicateConfigBase",
    "GlobPattern",
    "GlobPredicateConfig",
    "NotPredicateConfig",
    "OneOfPredicateConfig",
    "OneOfPredicateValue",
    "RegexPattern",
    "RegexPredicateConfig",
    "parse_glob_capture",
]
