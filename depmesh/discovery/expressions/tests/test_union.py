from __future__ import annotations

from pathlib import Path

import pytest

from depmesh.discovery.expressions.entities import EvaluationContext
from depmesh.discovery.expressions.union import UnionExpression
from depmesh.discovery.matchers import CaptureName
from depmesh.domain.entities import ArtifactId, RelationId


def touch(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("", encoding="utf-8")


class TestUnionExpression:
    def test_variables__combines_item_variables(self) -> None:
        expression = UnionExpression.model_validate(
            {
                "type": "union",
                "items": [
                    {"type": "path", "path": "./tests/test_{module}.py"},
                    {"type": "path", "path": "./specs/{name}.md"},
                ],
            }
        )

        assert expression.variables() == {CaptureName("module"), CaptureName("name")}

    def test_evaluate__returns_union_of_item_results(self, tmp_path: Path) -> None:
        touch(tmp_path / "tests/test_a.py")
        touch(tmp_path / "tests/test_b.py")
        expression = UnionExpression.model_validate(
            {
                "type": "union",
                "items": [
                    {"type": "path", "path": "./tests/test_a.py"},
                    {"type": "glob", "pattern": "./tests/test_*.py"},
                ],
            }
        )
        context = EvaluationContext(root=tmp_path, relation_id=RelationId("tests"), captures={})

        assert expression.evaluate(context) == [ArtifactId("./tests/test_a.py"), ArtifactId("./tests/test_b.py")]

    def test_evaluate__supports_nested_expressions_and_templates(self, tmp_path: Path) -> None:
        touch(tmp_path / "tests/test_a.py")
        touch(tmp_path / "tests/test_a_extra.py")
        touch(tmp_path / "specs/a.md")
        touch(tmp_path / "specs/b.md")
        expression = UnionExpression.model_validate(
            {
                "type": "union",
                "items": [
                    {"type": "path", "path": "./tests/test_{module}.py"},
                    {
                        "type": "intersection",
                        "items": [
                            {"type": "glob", "pattern": "./tests/test_{module}*.py"},
                            {"type": "regex", "pattern": r"^\./tests/test_{module}\.py$"},
                        ],
                    },
                    {"type": "path", "path": "./specs/{module}.md"},
                ],
            }
        )
        context = EvaluationContext(
            root=tmp_path,
            relation_id=RelationId("tests"),
            captures={CaptureName("module"): "a"},
        )

        assert expression.evaluate(context) == [ArtifactId("./specs/a.md"), ArtifactId("./tests/test_a.py")]

    def test_items__empty(self) -> None:
        with pytest.raises(ValueError):
            UnionExpression.model_validate({"type": "union", "items": []})
