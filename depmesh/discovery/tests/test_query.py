from __future__ import annotations

from pathlib import Path

import pytest

from depmesh.core import warnings
from depmesh.discovery import errors
from depmesh.discovery.entities import DependencyRule
from depmesh.discovery.query import query_dependencies
from depmesh.domain.entities import ArtifactId, Relation, RelationId


def touch(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("", encoding="utf-8")


def make_relation(relation_id: str) -> Relation:
    return Relation(id=RelationId(relation_id))


def make_relation_index(*relations: Relation) -> dict[RelationId, Relation]:
    return {relation.id: relation for relation in relations}


def make_rules(*raw_rules: dict[str, object]) -> tuple[DependencyRule, ...]:
    return tuple(DependencyRule.model_validate(rule) for rule in raw_rules)


class TestQueryDependencies:
    def test_merges_and_orders_dependencies(self, tmp_path: Path) -> None:
        touch(tmp_path / "src/a.py")
        touch(tmp_path / "src/b.py")
        touch(tmp_path / "tests/test_a.py")
        touch(tmp_path / "tests/test_b.py")
        relations = (make_relation("tests"),)
        rules = make_rules(
            {
                "relation": "tests",
                "artifact": {"type": "glob", "pattern": "./src/{*module}.py"},
                "dependency": {
                    "type": "union",
                    "items": [
                        {"type": "path", "path": "./tests/test_{module}.py"},
                        {"type": "glob", "pattern": "./tests/test_*.py"},
                    ],
                },
            }
        )

        result = query_dependencies(
            tmp_path,
            make_relation_index(*relations),
            rules,
            [ArtifactId("./src/a.py"), ArtifactId("./src/b.py")],
            cwd=tmp_path,
        )

        assert result.grouped() == {"tests": ["./tests/test_a.py", "./tests/test_b.py"]}

    def test_uses_regex_dependency_expression(self, tmp_path: Path) -> None:
        touch(tmp_path / "src/a.py")
        touch(tmp_path / "specs/a.md")
        touch(tmp_path / "specs/b.md")
        relations = (make_relation("specs"),)
        rules = make_rules(
            {
                "relation": "specs",
                "artifact": {"type": "regex", "pattern": r"^\./src/(?P<module>[a-z]+)\.py$"},
                "dependency": {"type": "regex", "pattern": r"^\./specs/{module}\.md$"},
            }
        )

        result = query_dependencies(
            tmp_path,
            make_relation_index(*relations),
            rules,
            [ArtifactId("src/a.py")],
            cwd=tmp_path,
        )

        assert result.grouped() == {"specs": ["./specs/a.md"]}

    def test_uses_command_expression(self, tmp_path: Path) -> None:
        touch(tmp_path / "src/a.py")
        touch(tmp_path / "tests/test_a.py")
        relations = (make_relation("tests"),)
        rules = make_rules(
            {
                "relation": "tests",
                "artifact": {"type": "glob", "pattern": "./src/{*module}.py"},
                "dependency": {"type": "command", "command": "printf './tests/test_{module}.py\\n'"},
            }
        )

        result = query_dependencies(
            tmp_path,
            make_relation_index(*relations),
            rules,
            [ArtifactId("./src/a.py")],
            cwd=tmp_path,
        )

        assert result.grouped() == {"tests": ["./tests/test_a.py"]}

    def test_path_expression_missing_file_adds_warning(self, tmp_path: Path) -> None:
        warnings.clear()
        touch(tmp_path / "src/a.py")
        relations = (make_relation("tests"),)
        rules = make_rules(
            {
                "relation": "tests",
                "artifact": {"type": "glob", "pattern": "./src/{*module}.py"},
                "dependency": {"type": "path", "path": "./tests/test_{module}.py"},
            }
        )

        result = query_dependencies(
            tmp_path,
            make_relation_index(*relations),
            rules,
            [ArtifactId("./src/a.py")],
            cwd=tmp_path,
        )

        assert result.grouped() == {}
        assert warnings.read() == ["relation `tests`: skipped missing dependency `./tests/test_a.py`"]
        warnings.clear()

    def test_relation_filter_uses_explicit_relation_id(self, tmp_path: Path) -> None:
        touch(tmp_path / "src/a.py")
        touch(tmp_path / "tests/test_a.py")
        touch(tmp_path / "specs/a.md")
        relations = (make_relation("tests"), make_relation("specs"))
        rules = make_rules(
            {
                "relation": "tests",
                "artifact": {"type": "glob", "pattern": "./src/{*module}.py"},
                "dependency": {"type": "path", "path": "./tests/test_{module}.py"},
            },
            {
                "relation": "specs",
                "artifact": {"type": "glob", "pattern": "./src/{*module}.py"},
                "dependency": {"type": "path", "path": "./specs/{module}.md"},
            },
        )

        result = query_dependencies(
            tmp_path,
            make_relation_index(*relations),
            rules,
            [ArtifactId("./src/a.py")],
            relation_filters=[RelationId("tests")],
            cwd=tmp_path,
        )

        assert result.grouped() == {"tests": ["./tests/test_a.py"]}

    def test_omitted_relation_filter_searches_all_explicit_relations(self, tmp_path: Path) -> None:
        touch(tmp_path / "src/a.py")
        touch(tmp_path / "tests/test_a.py")
        relations = (make_relation("tests"), make_relation("tested_by"))
        rules = make_rules(
            {
                "relation": "tests",
                "artifact": {"type": "glob", "pattern": "./src/{*module}.py"},
                "dependency": {"type": "path", "path": "./tests/test_{module}.py"},
            },
            {
                "relation": "tested_by",
                "artifact": {"type": "glob", "pattern": "./tests/test_{*module}.py"},
                "dependency": {"type": "path", "path": "./src/{module}.py"},
            },
        )

        result = query_dependencies(
            tmp_path,
            make_relation_index(*relations),
            rules,
            [ArtifactId("./src/a.py"), ArtifactId("./tests/test_a.py")],
            cwd=tmp_path,
        )

        assert result.grouped() == {
            "tested_by": ["./src/a.py"],
            "tests": ["./tests/test_a.py"],
        }

    def test_reverse_lookup_requires_explicit_relation_and_rule(self, tmp_path: Path) -> None:
        touch(tmp_path / "src/a.py")
        touch(tmp_path / "tests/test_a.py")
        relations = (make_relation("tested_by"),)
        rules = make_rules(
            {
                "relation": "tested_by",
                "artifact": {"type": "glob", "pattern": "./tests/test_{*module}.py"},
                "dependency": {"type": "path", "path": "./src/{module}.py"},
            }
        )

        result = query_dependencies(
            tmp_path,
            make_relation_index(*relations),
            rules,
            [ArtifactId("./tests/test_a.py")],
            relation_filters=[RelationId("tested_by")],
            cwd=tmp_path,
        )

        assert result.grouped() == {"tested_by": ["./src/a.py"]}

    def test_skips_rule_with_missing_relation(self, tmp_path: Path) -> None:
        touch(tmp_path / "src/a.py")
        touch(tmp_path / "tests/test_a.py")
        rules = make_rules(
            {
                "relation": "tests",
                "artifact": {"type": "glob", "pattern": "./src/{*module}.py"},
                "dependency": {"type": "path", "path": "./tests/test_{module}.py"},
            }
        )

        result = query_dependencies(
            tmp_path,
            {},
            rules,
            [ArtifactId("./src/a.py")],
            cwd=tmp_path,
        )

        assert result.grouped() == {}

    def test_unknown_relation_filter(self, tmp_path: Path) -> None:
        relations = (make_relation("tests"),)

        with pytest.raises(errors.UnknownRelationFilter):
            query_dependencies(
                tmp_path,
                make_relation_index(*relations),
                (),
                [ArtifactId("./src/a.py")],
                relation_filters=[RelationId("missing")],
                cwd=tmp_path,
            )
