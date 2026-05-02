from __future__ import annotations

from typing import Annotated

import pydantic

from depmesh.discovery.matchers.all import AllMatcher
from depmesh.discovery.matchers.any import AnyMatcher
from depmesh.discovery.matchers.glob import GlobMatcher, GlobPattern
from depmesh.discovery.matchers.path import PathMatcher, PathMatcherValue
from depmesh.discovery.matchers.regex import RegexMatcher, RegexPattern
from depmesh.discovery.matchers.entities import CaptureName

ArtifactMatcher = Annotated[
    PathMatcher | GlobMatcher | RegexMatcher | AnyMatcher | AllMatcher,
    pydantic.Field(discriminator="type"),
]

AnyMatcher.model_rebuild(_types_namespace={"ArtifactMatcher": ArtifactMatcher})
AllMatcher.model_rebuild(_types_namespace={"ArtifactMatcher": ArtifactMatcher})

__all__ = [
    "AllMatcher",
    "ArtifactMatcher",
    "AnyMatcher",
    "CaptureName",
    "GlobMatcher",
    "GlobPattern",
    "PathMatcher",
    "PathMatcherValue",
    "RegexMatcher",
    "RegexPattern",
]
