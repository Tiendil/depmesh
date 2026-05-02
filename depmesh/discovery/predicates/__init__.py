from __future__ import annotations

from typing import Annotated

import pydantic

from depmesh.discovery.artifacts import CaptureName
from depmesh.discovery.predicates.all import AllPredicate
from depmesh.discovery.predicates.any import AnyPredicate
from depmesh.discovery.predicates.glob import GlobPattern, GlobPredicate
from depmesh.discovery.predicates.not_ import NotPredicate
from depmesh.discovery.predicates.one_of import OneOfPredicate, OneOfPredicateValue
from depmesh.discovery.predicates.regex import RegexPattern, RegexPredicate

ArtifactPredicate = Annotated[
    OneOfPredicate | GlobPredicate | RegexPredicate | AnyPredicate | AllPredicate | NotPredicate,
    pydantic.Field(discriminator="type"),
]

AnyPredicate.model_rebuild(_types_namespace={"ArtifactPredicate": ArtifactPredicate})
AllPredicate.model_rebuild(_types_namespace={"ArtifactPredicate": ArtifactPredicate})
NotPredicate.model_rebuild(_types_namespace={"ArtifactPredicate": ArtifactPredicate})

__all__ = [
    "AllPredicate",
    "AnyPredicate",
    "ArtifactPredicate",
    "CaptureName",
    "GlobPattern",
    "GlobPredicate",
    "NotPredicate",
    "OneOfPredicate",
    "OneOfPredicateValue",
    "RegexPattern",
    "RegexPredicate",
]
