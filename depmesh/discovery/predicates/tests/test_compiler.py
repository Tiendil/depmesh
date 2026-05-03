from __future__ import annotations

from pathlib import Path

from depmesh.discovery.predicates import compile_predicate
from depmesh.discovery.predicates.all import AllPredicate
from depmesh.discovery.predicates.any import AnyPredicate
from depmesh.discovery.predicates.entities import (
    AllPredicateConfig,
    AnyPredicateConfig,
    GlobPredicateConfig,
    NotPredicateConfig,
    OneOfPredicateConfig,
    RegexPredicateConfig,
)
from depmesh.discovery.predicates.glob import GlobPredicate
from depmesh.discovery.predicates.not_ import NotPredicate
from depmesh.discovery.predicates.one_of import OneOfPredicate
from depmesh.discovery.predicates.regex import RegexPredicate
from depmesh.domain.entities import ArtifactId, ProjectRootPath


class TestCompilePredicate:
    def test_one_of_predicate(self, tmp_path: Path) -> None:
        predicate = compile_predicate(OneOfPredicateConfig.model_validate({"type": "one_of", "artifacts": ["@/a.py"]}))

        assert isinstance(predicate, OneOfPredicate)
        assert predicate.match(ArtifactId("@/a.py"), ProjectRootPath(tmp_path)) == {}

    def test_glob_predicate(self, tmp_path: Path) -> None:
        predicate = compile_predicate(GlobPredicateConfig(type="glob", pattern="@/{*name}.py"))

        assert isinstance(predicate, GlobPredicate)
        assert predicate.match(ArtifactId("@/a.py"), ProjectRootPath(tmp_path)) == {"name": "a"}

    def test_regex_predicate(self, tmp_path: Path) -> None:
        predicate = compile_predicate(RegexPredicateConfig(type="regex", pattern=r"^@/(?P<name>[a-z]+)\.py$"))

        assert isinstance(predicate, RegexPredicate)
        assert predicate.match(ArtifactId("@/a.py"), ProjectRootPath(tmp_path)) == {"name": "a"}

    def test_any_predicate(self, tmp_path: Path) -> None:
        predicate = compile_predicate(
            AnyPredicateConfig.model_validate(
                {
                    "type": "any",
                    "items": [
                        {"type": "glob", "pattern": "@/src/{*module}.py"},
                        {"type": "glob", "pattern": "@/lib/{*module}.py"},
                    ],
                }
            )
        )

        assert isinstance(predicate, AnyPredicate)
        assert predicate.match(ArtifactId("@/lib/a.py"), ProjectRootPath(tmp_path)) == {"module": "a"}

    def test_all_predicate(self, tmp_path: Path) -> None:
        predicate = compile_predicate(
            AllPredicateConfig.model_validate(
                {
                    "type": "all",
                    "items": [
                        {"type": "glob", "pattern": "@/src/{*module}.py"},
                        {"type": "regex", "pattern": r"^@/src/(?P<module>[a-z]+)\.py$"},
                    ],
                }
            )
        )

        assert isinstance(predicate, AllPredicate)
        assert predicate.match(ArtifactId("@/src/a.py"), ProjectRootPath(tmp_path)) == {"module": "a"}

    def test_not_predicate(self, tmp_path: Path) -> None:
        predicate = compile_predicate(
            NotPredicateConfig.model_validate(
                {"type": "not", "item": {"type": "one_of", "artifacts": ["@/excluded.py"]}}
            )
        )

        assert isinstance(predicate, NotPredicate)
        assert predicate.match(ArtifactId("@/included.py"), ProjectRootPath(tmp_path)) == {}
