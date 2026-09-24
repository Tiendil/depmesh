from __future__ import annotations

from pathlib import Path

import pytest
from llm_tool_cli.core.result import UnwrapError

from depmesh.discovery import errors
from depmesh.discovery.artifacts import CaptureName
from depmesh.discovery.predicates import (
    AllPredicateConfig,
    AnyPredicateConfig,
    NotPredicateConfig,
    compile_predicate,
)
from depmesh.domain.entities import ArtifactId, ProjectRootPath


class TestAnyPredicate:
    def test_match__propagates_child_error(self, tmp_path: Path) -> None:
        predicate = compile_predicate(
            AnyPredicateConfig.model_validate(
                {"type": "any", "items": [{"type": "one_of", "artifacts": ["../outside.py"]}]}
            )
        )

        with pytest.raises(UnwrapError) as caught:
            predicate.match(ArtifactId("@/a.py"), ProjectRootPath(tmp_path))

        assert caught.value.details["error"] == [errors.InvalidProjectPath(path="../outside.py")]

    def test_match__returns_first_matching_item_captures(self, tmp_path: Path) -> None:
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

        assert predicate.match(ArtifactId("@/lib/a.py"), ProjectRootPath(tmp_path)) == {"module": "a"}


class TestAllPredicate:
    def test_match__propagates_child_error(self, tmp_path: Path) -> None:
        predicate = compile_predicate(
            AllPredicateConfig.model_validate(
                {"type": "all", "items": [{"type": "one_of", "artifacts": ["../outside.py"]}]}
            )
        )

        with pytest.raises(UnwrapError) as caught:
            predicate.match(ArtifactId("@/a.py"), ProjectRootPath(tmp_path))

        assert caught.value.details["error"] == [errors.InvalidProjectPath(path="../outside.py")]

    def test_match__combines_captures_when_all_items_match(self, tmp_path: Path) -> None:
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

        assert predicate.match(ArtifactId("@/src/a.py"), ProjectRootPath(tmp_path)) == {"module": "a"}


class TestNotPredicate:
    def test_match__does_not_turn_child_error_into_match(self, tmp_path: Path) -> None:
        predicate = compile_predicate(
            NotPredicateConfig.model_validate(
                {"type": "not", "item": {"type": "one_of", "artifacts": ["../outside.py"]}}
            )
        )

        with pytest.raises(UnwrapError) as caught:
            predicate.match(ArtifactId("@/a.py"), ProjectRootPath(tmp_path))

        assert caught.value.details["error"] == [errors.InvalidProjectPath(path="../outside.py")]

    def test_variables__exposes_child_template_variables(self) -> None:
        predicate = NotPredicateConfig.model_validate(
            {"type": "not", "item": {"type": "glob", "pattern": "@/src/{package}/{*module}.py"}}
        )

        assert predicate.variables() == {CaptureName("package")}

    def test_match__success_when_item_does_not_match(self, tmp_path: Path) -> None:
        predicate = compile_predicate(
            NotPredicateConfig.model_validate(
                {"type": "not", "item": {"type": "one_of", "artifacts": ["@/src/excluded.py"]}}
            )
        )

        assert predicate.match(ArtifactId("@/src/included.py"), ProjectRootPath(tmp_path)) == {}
