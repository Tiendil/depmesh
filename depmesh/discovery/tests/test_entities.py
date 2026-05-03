from __future__ import annotations

import pytest

from depmesh.discovery.entities import DependencyRuleConfig, QueryResult, compile_dependency_rule
from depmesh.discovery.predicates.glob import GlobPredicate
from depmesh.discovery.sources.list import ListSource
from depmesh.domain.entities import ArtifactId, Dependency, RelationId


class TestDependencyRuleConfig:
    def test_validate_templates__accepts_output_variables_from_input_predicate(self) -> None:
        rule = DependencyRuleConfig.model_validate(
            {
                "relation": "tests",
                "input": {"type": "glob", "pattern": "@/src/{*module}.py"},
                "output": {"type": "list", "artifacts": ["@/tests/test_{module}.py"]},
            }
        )

        assert rule.relation == RelationId("tests")

    def test_validate_templates__rejects_unknown_output_variable(self) -> None:
        with pytest.raises(ValueError, match="output source references capture `missing`"):
            DependencyRuleConfig.model_validate(
                {
                    "relation": "tests",
                    "input": {"type": "glob", "pattern": "@/src/{*module}.py"},
                    "output": {"type": "list", "artifacts": ["@/tests/test_{missing}.py"]},
                }
            )


class TestCompileDependencyRule:
    def test_compiles_runtime_predicate_and_output_source(self) -> None:
        config = DependencyRuleConfig.model_validate(
            {
                "relation": "tests",
                "input": {"type": "glob", "pattern": "@/src/{*module}.py"},
                "output": {"type": "list", "artifacts": ["@/tests/test_{module}.py"]},
            }
        )

        rule = compile_dependency_rule(config)

        assert rule.relation == RelationId("tests")
        assert isinstance(rule.input_predicate, GlobPredicate)
        assert isinstance(rule.output_source, ListSource)


class TestQueryResult:
    def test_grouped__deduplicates_and_orders_dependencies(self) -> None:
        result = QueryResult(
            dependencies=(
                Dependency(relation=RelationId("tests"), dependency=ArtifactId("@/tests/test_b.py")),
                Dependency(relation=RelationId("tests"), dependency=ArtifactId("@/tests/test_a.py")),
                Dependency(relation=RelationId("tests"), dependency=ArtifactId("@/tests/test_a.py")),
            )
        )

        assert result.grouped() == {
            RelationId("tests"): [ArtifactId("@/tests/test_a.py"), ArtifactId("@/tests/test_b.py")]
        }
