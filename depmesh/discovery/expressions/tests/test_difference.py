from __future__ import annotations

from pathlib import Path

from depmesh.discovery.expressions.difference import DifferenceExpression
from depmesh.discovery.expressions.entities import EvaluationContext
from depmesh.discovery.matchers import CaptureName
from depmesh.domain.entities import ArtifactId, RelationId


def touch(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("", encoding="utf-8")


class TestDifferenceExpression:
    def test_variables__combines_child_variables(self) -> None:
        expression = DifferenceExpression.model_validate(
            {
                "type": "difference",
                "include": {"type": "glob", "pattern": "./specs/{kind}/*.md"},
                "exclude": {"type": "path", "path": "./specs/{kind}/{name}.md"},
            }
        )

        assert expression.variables() == {CaptureName("kind"), CaptureName("name")}

    def test_evaluate__removes_excluded_dependencies(self, tmp_path: Path) -> None:
        touch(tmp_path / "specs/a.md")
        touch(tmp_path / "specs/b.md")
        touch(tmp_path / "specs/c.py")
        expression = DifferenceExpression.model_validate(
            {
                "type": "difference",
                "include": {"type": "glob", "pattern": "./specs/*"},
                "exclude": {"type": "path", "path": "./specs/b.md"},
            }
        )
        context = EvaluationContext(root=tmp_path, relation_id=RelationId("specs"), captures={})

        assert expression.evaluate(context) == [ArtifactId("./specs/a.md"), ArtifactId("./specs/c.py")]

    def test_evaluate__supports_nested_expressions_and_templates(self, tmp_path: Path) -> None:
        touch(tmp_path / "specs/a.md")
        touch(tmp_path / "specs/b.md")
        touch(tmp_path / "docs/a.md")
        expression = DifferenceExpression.model_validate(
            {
                "type": "difference",
                "include": {
                    "type": "union",
                    "items": [
                        {"type": "glob", "pattern": "./specs/*.md"},
                        {"type": "glob", "pattern": "./docs/*.md"},
                    ],
                },
                "exclude": {"type": "regex", "pattern": r"^\./specs/{name}\.md$"},
            }
        )
        context = EvaluationContext(
            root=tmp_path,
            relation_id=RelationId("specs"),
            captures={CaptureName("name"): "a"},
        )

        assert expression.evaluate(context) == [ArtifactId("./docs/a.md"), ArtifactId("./specs/b.md")]
