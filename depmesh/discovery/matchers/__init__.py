from __future__ import annotations

from typing import Annotated

import pydantic

from depmesh.discovery.matchers.all import AllMatcher
from depmesh.discovery.matchers.any import AnyMatcher
from depmesh.discovery.matchers.glob import GlobMatcher, GlobPattern
from depmesh.discovery.matchers.not_ import NotMatcher
from depmesh.discovery.matchers.paths import PathsMatcher, PathsMatcherValue
from depmesh.discovery.matchers.regex import RegexMatcher, RegexPattern
from depmesh.discovery.matchers.entities import CaptureName

ArtifactMatcher = Annotated[
    PathsMatcher | GlobMatcher | RegexMatcher | AnyMatcher | AllMatcher | NotMatcher,
    pydantic.Field(discriminator="type"),
]

AnyMatcher.model_rebuild(_types_namespace={"ArtifactMatcher": ArtifactMatcher})
AllMatcher.model_rebuild(_types_namespace={"ArtifactMatcher": ArtifactMatcher})
NotMatcher.model_rebuild(_types_namespace={"ArtifactMatcher": ArtifactMatcher})

__all__ = [
    "AllMatcher",
    "ArtifactMatcher",
    "AnyMatcher",
    "CaptureName",
    "GlobMatcher",
    "GlobPattern",
    "NotMatcher",
    "PathsMatcher",
    "PathsMatcherValue",
    "RegexMatcher",
    "RegexPattern",
]
