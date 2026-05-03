from __future__ import annotations

from typing import assert_never

from depmesh.discovery.predicates.all import AllPredicate
from depmesh.discovery.predicates.any import AnyPredicate
from depmesh.discovery.predicates.base import ArtifactPredicateBase
from depmesh.discovery.predicates.entities import ArtifactPredicateConfig
from depmesh.discovery.predicates.glob import GlobPredicate
from depmesh.discovery.predicates.not_ import NotPredicate
from depmesh.discovery.predicates.one_of import OneOfPredicate
from depmesh.discovery.predicates.regex import RegexPredicate


def compile_predicate(config: ArtifactPredicateConfig) -> ArtifactPredicateBase:
    match config.type:
        case "one_of":
            return OneOfPredicate(config)
        case "glob":
            return GlobPredicate(config)
        case "regex":
            return RegexPredicate(config)
        case "any":
            return AnyPredicate(config, tuple(compile_predicate(item) for item in config.items))
        case "all":
            return AllPredicate(config, tuple(compile_predicate(item) for item in config.items))
        case "not":
            return NotPredicate(config, compile_predicate(config.item))

    assert_never(config)


__all__ = ["compile_predicate"]
