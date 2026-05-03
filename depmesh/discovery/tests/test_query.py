from __future__ import annotations

from pathlib import Path

import pytest

from depmesh.core import warnings
from depmesh.discovery import errors
from depmesh.discovery.entities import DependencyRule, DependencyRuleConfig, compile_dependency_rule
from depmesh.discovery.paths import resolve_project_root
from depmesh.discovery.query import query_dependencies, selected_relation_ids
from depmesh.domain.entities import ArtifactId, ProjectRootPath, Relation, RelationId, UntrustedPath


def touch(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("", encoding="utf-8")


def project_root(path: Path) -> ProjectRootPath:
    return resolve_project_root(UntrustedPath(path))


def make_relation(relation_id: str) -> Relation:
    return Relation(id=RelationId(relation_id))


def make_relation_index(*relations: Relation) -> dict[RelationId, Relation]:
    return {relation.id: relation for relation in relations}


def make_relation_ids(*relations: Relation) -> set[RelationId]:
    return set(make_relation_index(*relations))


def make_rules(*raw_rules: dict[str, object]) -> tuple[DependencyRule, ...]:
    return tuple(compile_dependency_rule(DependencyRuleConfig.model_validate(rule)) for rule in raw_rules)


class TestQueryDependencies:
    def test_deduplicates_and_orders_dependencies_from_one_artifact(self, tmp_path: Path) -> None:
        touch(tmp_path / "src/a.py")
        touch(tmp_path / "tests/test_a.py")
        touch(tmp_path / "tests/test_b.py")
        relations = (make_relation("tests"),)
        rules = make_rules(
            {
                "relation": "tests",
                "input": {"type": "glob", "pattern": "@/src/{*module}.py"},
                "output": {
                    "type": "union",
                    "items": [
                        {"type": "list", "artifacts": ["@/tests/test_{module}.py"]},
                        {"type": "files", "pattern": "@/tests/test_*.py"},
                    ],
                },
            }
        )

        result = query_dependencies(
            project_root(tmp_path),
            make_relation_index(*relations),
            rules,
            ArtifactId("@/src/a.py"),
            relation_ids=make_relation_ids(*relations),
            cwd=UntrustedPath(tmp_path),
        )

        assert result.grouped() == {"tests": ["@/tests/test_a.py", "@/tests/test_b.py"]}

    def test_uses_filter_source_with_regex_predicate(self, tmp_path: Path) -> None:
        touch(tmp_path / "src/a.py")
        touch(tmp_path / "specs/a.md")
        touch(tmp_path / "specs/b.md")
        relations = (make_relation("specs"),)
        rules = make_rules(
            {
                "relation": "specs",
                "input": {"type": "regex", "pattern": r"^@/src/(?P<module>[a-z]+)\.py$"},
                "output": {
                    "type": "filter",
                    "source": {"type": "files", "pattern": "@/specs/*.md"},
                    "predicate": {"type": "regex", "pattern": r"^@/specs/{module}\.md$"},
                },
            }
        )

        result = query_dependencies(
            project_root(tmp_path),
            make_relation_index(*relations),
            rules,
            ArtifactId("@/src/a.py"),
            relation_ids=make_relation_ids(*relations),
            cwd=UntrustedPath(tmp_path),
        )

        assert result.grouped() == {"specs": ["@/specs/a.md"]}

    def test_uses_command_source(self, tmp_path: Path) -> None:
        touch(tmp_path / "src/a.py")
        touch(tmp_path / "tests/test_a.py")
        relations = (make_relation("tests"),)
        rules = make_rules(
            {
                "relation": "tests",
                "input": {"type": "glob", "pattern": "@/src/{*module}.py"},
                "output": {"type": "command", "command": "printf '@/tests/test_{module}.py\\n'"},
            }
        )

        result = query_dependencies(
            project_root(tmp_path),
            make_relation_index(*relations),
            rules,
            ArtifactId("@/src/a.py"),
            relation_ids=make_relation_ids(*relations),
            cwd=UntrustedPath(tmp_path),
        )

        assert result.grouped() == {"tests": ["@/tests/test_a.py"]}

    def test_files_source_missing_file_returns_empty_result(self, tmp_path: Path) -> None:
        warnings.clear()
        touch(tmp_path / "src/a.py")
        relations = (make_relation("tests"),)
        rules = make_rules(
            {
                "relation": "tests",
                "input": {"type": "glob", "pattern": "@/src/{*module}.py"},
                "output": {"type": "files", "pattern": "@/tests/test_{module}.py"},
            }
        )

        result = query_dependencies(
            project_root(tmp_path),
            make_relation_index(*relations),
            rules,
            ArtifactId("@/src/a.py"),
            relation_ids=make_relation_ids(*relations),
            cwd=UntrustedPath(tmp_path),
        )

        assert result.grouped() == {}
        assert warnings.read() == []
        warnings.clear()

    def test_relation_filter_uses_explicit_relation_id(self, tmp_path: Path) -> None:
        touch(tmp_path / "src/a.py")
        touch(tmp_path / "tests/test_a.py")
        touch(tmp_path / "specs/a.md")
        relations = (make_relation("tests"), make_relation("specs"))
        rules = make_rules(
            {
                "relation": "tests",
                "input": {"type": "glob", "pattern": "@/src/{*module}.py"},
                "output": {"type": "list", "artifacts": ["@/tests/test_{module}.py"]},
            },
            {
                "relation": "specs",
                "input": {"type": "glob", "pattern": "@/src/{*module}.py"},
                "output": {"type": "list", "artifacts": ["@/specs/{module}.md"]},
            },
        )

        result = query_dependencies(
            project_root(tmp_path),
            make_relation_index(*relations),
            rules,
            ArtifactId("@/src/a.py"),
            relation_ids={RelationId("tests")},
            cwd=UntrustedPath(tmp_path),
        )

        assert result.grouped() == {"tests": ["@/tests/test_a.py"]}

    def test_all_selected_relations_can_contribute_for_one_artifact(self, tmp_path: Path) -> None:
        touch(tmp_path / "src/a.py")
        touch(tmp_path / "tests/test_a.py")
        touch(tmp_path / "specs/a.md")
        relations = (make_relation("tests"), make_relation("specs"))
        rules = make_rules(
            {
                "relation": "tests",
                "input": {"type": "glob", "pattern": "@/src/{*module}.py"},
                "output": {"type": "list", "artifacts": ["@/tests/test_{module}.py"]},
            },
            {
                "relation": "specs",
                "input": {"type": "glob", "pattern": "@/src/{*module}.py"},
                "output": {"type": "list", "artifacts": ["@/specs/{module}.md"]},
            },
        )

        result = query_dependencies(
            project_root(tmp_path),
            make_relation_index(*relations),
            rules,
            ArtifactId("@/src/a.py"),
            relation_ids=make_relation_ids(*relations),
            cwd=UntrustedPath(tmp_path),
        )

        assert result.grouped() == {
            "specs": ["@/specs/a.md"],
            "tests": ["@/tests/test_a.py"],
        }

    def test_reverse_lookup_requires_explicit_relation_and_rule(self, tmp_path: Path) -> None:
        touch(tmp_path / "src/a.py")
        touch(tmp_path / "tests/test_a.py")
        relations = (make_relation("tested_by"),)
        rules = make_rules(
            {
                "relation": "tested_by",
                "input": {"type": "glob", "pattern": "@/tests/test_{*module}.py"},
                "output": {"type": "list", "artifacts": ["@/src/{module}.py"]},
            }
        )

        result = query_dependencies(
            project_root(tmp_path),
            make_relation_index(*relations),
            rules,
            ArtifactId("@/tests/test_a.py"),
            relation_ids={RelationId("tested_by")},
            cwd=UntrustedPath(tmp_path),
        )

        assert result.grouped() == {"tested_by": ["@/src/a.py"]}

    def test_skips_rule_with_missing_relation(self, tmp_path: Path) -> None:
        touch(tmp_path / "src/a.py")
        touch(tmp_path / "tests/test_a.py")
        rules = make_rules(
            {
                "relation": "tests",
                "input": {"type": "glob", "pattern": "@/src/{*module}.py"},
                "output": {"type": "list", "artifacts": ["@/tests/test_{module}.py"]},
            }
        )

        result = query_dependencies(
            project_root(tmp_path),
            {},
            rules,
            ArtifactId("@/src/a.py"),
            relation_ids={RelationId("tests")},
            cwd=UntrustedPath(tmp_path),
        )

        assert result.grouped() == {}

    def test_unknown_relation_filter(self, tmp_path: Path) -> None:
        relations = (make_relation("tests"),)

        with pytest.raises(errors.UnknownRelationFilter):
            selected_relation_ids(make_relation_index(*relations), [RelationId("missing")])
