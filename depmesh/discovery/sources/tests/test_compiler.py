from __future__ import annotations

from pathlib import Path

from depmesh.discovery.artifacts import EvaluationContext
from depmesh.discovery.sources import compile_source
from depmesh.discovery.sources.command import CommandSource
from depmesh.discovery.sources.difference import DifferenceSource
from depmesh.discovery.sources.entities import (
    CommandSourceConfig,
    DifferenceSourceConfig,
    FilesSourceConfig,
    FilterSourceConfig,
    IntersectionSourceConfig,
    ListSourceConfig,
    UnionSourceConfig,
)
from depmesh.discovery.sources.files import FilesSource
from depmesh.discovery.sources.filter import FilterSource
from depmesh.discovery.sources.intersection import IntersectionSource
from depmesh.discovery.sources.list import ListSource
from depmesh.discovery.sources.union import UnionSource
from depmesh.domain.entities import ArtifactId, ProjectRootPath, RelationId


def context(root: Path) -> EvaluationContext:
    return EvaluationContext(root=ProjectRootPath(root), relation_id=RelationId("tests"), captures={})


def touch(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("", encoding="utf-8")


class TestCompileSource:
    def test_files_source(self, tmp_path: Path) -> None:
        touch(tmp_path / "a.py")

        source = compile_source(FilesSourceConfig.model_validate({"type": "files", "pattern": "@/*.py"}))

        assert isinstance(source, FilesSource)
        assert source.evaluate(context(tmp_path)) == [ArtifactId("@/a.py")]

    def test_command_source(self, tmp_path: Path) -> None:
        source = compile_source(CommandSourceConfig(type="command", command="printf '@/a.py\\n'"))

        assert isinstance(source, CommandSource)
        assert source.evaluate(context(tmp_path)) == [ArtifactId("@/a.py")]

    def test_list_source(self, tmp_path: Path) -> None:
        source = compile_source(ListSourceConfig.model_validate({"type": "list", "artifacts": ["@/a.py"]}))

        assert isinstance(source, ListSource)
        assert source.evaluate(context(tmp_path)) == [ArtifactId("@/a.py")]

    def test_union_source(self, tmp_path: Path) -> None:
        source = compile_source(
            UnionSourceConfig.model_validate(
                {
                    "type": "union",
                    "items": [
                        {"type": "list", "artifacts": ["@/a.py"]},
                        {"type": "list", "artifacts": ["@/b.py"]},
                    ],
                }
            )
        )

        assert isinstance(source, UnionSource)
        assert source.evaluate(context(tmp_path)) == [
            ArtifactId("@/a.py"),
            ArtifactId("@/b.py"),
        ]

    def test_intersection_source(self, tmp_path: Path) -> None:
        source = compile_source(
            IntersectionSourceConfig.model_validate(
                {
                    "type": "intersection",
                    "items": [
                        {"type": "list", "artifacts": ["@/a.py", "@/b.py"]},
                        {"type": "list", "artifacts": ["@/b.py"]},
                    ],
                }
            )
        )

        assert isinstance(source, IntersectionSource)
        assert source.evaluate(context(tmp_path)) == [ArtifactId("@/b.py")]

    def test_difference_source(self, tmp_path: Path) -> None:
        source = compile_source(
            DifferenceSourceConfig.model_validate(
                {
                    "type": "difference",
                    "include": {"type": "list", "artifacts": ["@/a.py", "@/b.py"]},
                    "exclude": {"type": "list", "artifacts": ["@/b.py"]},
                }
            )
        )

        assert isinstance(source, DifferenceSource)
        assert source.evaluate(context(tmp_path)) == [ArtifactId("@/a.py")]

    def test_filter_source(self, tmp_path: Path) -> None:
        source = compile_source(
            FilterSourceConfig.model_validate(
                {
                    "type": "filter",
                    "source": {"type": "list", "artifacts": ["@/src/a.py", "@/docs/a.md"]},
                    "predicate": {"type": "glob", "pattern": "@/src/{*module}.py"},
                }
            )
        )

        assert isinstance(source, FilterSource)
        assert source.evaluate(context(tmp_path)) == [ArtifactId("@/src/a.py")]
