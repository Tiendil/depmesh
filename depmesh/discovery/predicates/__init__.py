from __future__ import annotations

from depmesh.discovery.predicates.all import AllPredicate
from depmesh.discovery.predicates.any import AnyPredicate
from depmesh.discovery.predicates.base import ArtifactPredicateBase, ArtifactPredicateConfigBase
from depmesh.discovery.predicates.compiler import compile_predicate
from depmesh.discovery.predicates.entities import (
    AllPredicateConfig,
    AnyPredicateConfig,
    ArtifactPredicateConfig,
    GlobPattern,
    GlobPredicateConfig,
    NotPredicateConfig,
    OneOfPredicateConfig,
    OneOfPredicateValue,
    RegexPattern,
    RegexPredicateConfig,
)
from depmesh.discovery.artifacts import CaptureName
from depmesh.discovery.predicates.glob import GlobPredicate
from depmesh.discovery.predicates.not_ import NotPredicate
from depmesh.discovery.predicates.one_of import OneOfPredicate
from depmesh.discovery.predicates.regex import RegexPredicate

__all__ = [
    "AllPredicate",
    "AllPredicateConfig",
    "AnyPredicate",
    "AnyPredicateConfig",
    "ArtifactPredicateBase",
    "ArtifactPredicateConfig",
    "ArtifactPredicateConfigBase",
    "CaptureName",
    "GlobPattern",
    "GlobPredicate",
    "GlobPredicateConfig",
    "NotPredicate",
    "NotPredicateConfig",
    "OneOfPredicate",
    "OneOfPredicateConfig",
    "OneOfPredicateValue",
    "RegexPattern",
    "RegexPredicate",
    "RegexPredicateConfig",
    "compile_predicate",
]
