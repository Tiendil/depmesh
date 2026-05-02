from __future__ import annotations

from pathlib import Path

from depmesh.discovery.artifacts import CaptureName, EvaluationContext
from depmesh.discovery.sources.list import ListSource
from depmesh.domain.entities import ArtifactId, RelationId


class TestListSource:
    def test_variables__extracts_template_variables(self) -> None:
        source = ListSource(type="list", artifacts=("./tests/test_{module}.py",))

        assert source.variables() == {CaptureName("module")}

    def test_evaluate__normalizes_and_substitutes_artifacts(self, tmp_path: Path) -> None:
        source = ListSource(type="list", artifacts=("tests/test_{module}.py",))
        context = EvaluationContext(root=tmp_path, relation_id=RelationId("tests"), captures={"module": "a"})

        assert source.evaluate(context) == [ArtifactId("./tests/test_a.py")]
