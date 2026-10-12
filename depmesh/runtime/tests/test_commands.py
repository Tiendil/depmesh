from collections.abc import Iterator
from pathlib import Path

import pytest
from llm_tool_cli.cli.errors import InvalidArguments
from llm_tool_cli.config import load_config
from llm_tool_cli.config.project import ProjectConfig, project_config
from llm_tool_cli.core.result import Err
from llm_tool_cli.paths import PathInput, ProjectConfigPath
from llm_tool_cli.paths.errors import InvalidProjectPath, PathResolutionFailed
from llm_tool_cli.protocol import Protocol
from pytest_mock import MockerFixture

from depmesh.core import warnings
from depmesh.discovery.errors import UnknownRelationFilter
from depmesh.domain.entities import ArtifactId, Dependency, RelationId
from depmesh.runtime import commands
from depmesh.workspace import Config, Workspace, construct_workspace


@pytest.fixture
def project(tmp_path: Path) -> PathInput:
    (tmp_path / "depmesh.toml").write_text(
        """[[relations]]
id = "tests"
description = "Related tests."
[[relations]]
id = "docs"
[[rules]]
relation = "tests"
input = { type = "glob", pattern = "@/src/{*module}.py" }
output = { type = "list", artifacts = ["@/tests/{module}.py", "@/tests/shared.py"] }
[[rules]]
relation = "docs"
input = { type = "glob", pattern = "@/src/*.py" }
output = { type = "list", artifacts = ["@/README.md"] }
""",
        encoding="utf-8",
    )
    return PathInput(tmp_path)


@pytest.fixture
def workspace(project: PathInput) -> Iterator[Workspace]:
    path = ProjectConfigPath(project / "depmesh.toml")
    config = load_config(path, Config).unwrap()
    with project_config.scope(ProjectConfig(config_path=path)):
        yield construct_workspace(config)


class TestDependencies:
    def test_merges_inputs_into_complete_cell_without_cli(
        self, project: PathInput, workspace: Workspace, capsys: pytest.CaptureFixture[str]
    ) -> None:
        cwd = project / "src"
        cwd.mkdir()

        cell = commands.dependencies(
            [ArtifactId("b.py"), ArtifactId("@/src/a.py"), ArtifactId("./a.py")],
            [],
            workspace=workspace,
            cwd=PathInput(cwd),
        ).unwrap()

        assert cell.result.dependencies == (
            Dependency(relation=RelationId("docs"), dependency=ArtifactId("@/README.md")),
            Dependency(relation=RelationId("tests"), dependency=ArtifactId("@/tests/a.py")),
            Dependency(relation=RelationId("tests"), dependency=ArtifactId("@/tests/b.py")),
            Dependency(relation=RelationId("tests"), dependency=ArtifactId("@/tests/shared.py")),
        )
        assert [(relation.id, relation.description) for relation in cell.relations] == [
            ("tests", "Related tests."),
            ("docs", None),
        ]
        assert cell.warnings == []
        assert capsys.readouterr() == ("", "")

    def test_filters_relations(self, project: PathInput, workspace: Workspace) -> None:
        cell = commands.dependencies(
            [ArtifactId("@/src/a.py")], [RelationId("docs"), RelationId("docs")], workspace=workspace, cwd=project
        ).unwrap()

        assert cell.result.dependencies == (
            Dependency(relation=RelationId("docs"), dependency=ArtifactId("@/README.md")),
        )

    @pytest.mark.parametrize("artifacts", [[], [ArtifactId("@/unmatched")]])
    def test_empty_result(self, project: PathInput, workspace: Workspace, artifacts: list[ArtifactId]) -> None:
        cell = commands.dependencies(artifacts, [], workspace=workspace, cwd=project).unwrap()

        assert cell.result.dependencies == ()
        assert cell.warnings == []
        assert cell.render(Protocol.automation) == []

    def test_snapshots_warnings_after_query(self, project: PathInput, workspace: Workspace) -> None:
        with (project / "depmesh.toml").open("a", encoding="utf-8") as config:
            config.write(
                '\n[[rules]]\nrelation = "tests"\n'
                'input = { type = "glob", pattern = "@/src/*.py" }\n'
                'output = { type = "files", pattern = "@/../outside" }\n'
            )
        warnings.add("earlier warning")
        workspace = construct_workspace(load_config(project / "depmesh.toml", Config).unwrap())

        cell = commands.dependencies([ArtifactId("@/src/a.py")], [], workspace=workspace, cwd=project).unwrap()

        assert len(cell.result.dependencies) == 3
        assert len(cell.warnings) == 2
        assert cell.warnings[0] == "earlier warning"
        assert "outside" in cell.warnings[1]
        assert warnings.read() == cell.warnings
        snapshot = list(cell.warnings)
        warnings.clear()
        warnings.add("later warning")
        assert cell.warnings == snapshot
        assert [output.meta["type"] for output in cell.render(Protocol.automation)] == [
            "dependency",
            "dependency",
            "dependency",
            "warning",
            "warning",
        ]

    def test_unknown_relation_precedes_input_validation(self, project: PathInput, workspace: Workspace) -> None:
        assert commands.dependencies(
            [ArtifactId("@/../outside")], [RelationId("unknown")], workspace=workspace, cwd=project
        ).unwrap_err() == [UnknownRelationFilter(relation=RelationId("unknown"))]

    def test_invalid_input_becomes_argument_error(self, project: PathInput, workspace: Workspace) -> None:
        failures = commands.dependencies(
            [ArtifactId("@/../outside")], [], workspace=workspace, cwd=project
        ).unwrap_err()

        assert len(failures) == 1
        assert isinstance(failures[0], InvalidArguments)

    def test_resolution_failure_is_preserved(
        self, project: PathInput, workspace: Workspace, mocker: MockerFixture
    ) -> None:
        error = PathResolutionFailed(path=str(project), reason="denied")
        mocker.patch.object(commands, "resolve_project_root", return_value=Err([error]))

        assert commands.dependencies([ArtifactId("@/a")], [], workspace=workspace, cwd=project).unwrap_err() == [error]

    def test_input_resolution_failure_is_preserved(
        self, project: PathInput, workspace: Workspace, mocker: MockerFixture
    ) -> None:
        error = PathResolutionFailed(path="~/a.py", reason="home unavailable")
        mocker.patch.object(commands, "normalize_input_artifacts", return_value=Err([error]))

        assert commands.dependencies([ArtifactId("~/a.py")], [], workspace=workspace, cwd=project).unwrap_err() == [
            error
        ]

    def test_query_failure_is_not_an_argument_error(
        self, project: PathInput, workspace: Workspace, mocker: MockerFixture
    ) -> None:
        error = InvalidProjectPath(path="@/../dependency")
        mocker.patch.object(commands, "query_dependencies", return_value=Err([error]))

        assert commands.dependencies(
            [ArtifactId("@/src/a.py")], [], workspace=workspace, cwd=project
        ).unwrap_err() == [error]


class TestRelations:
    def test_returns_ordered_cells(self, workspace: Workspace, capsys: pytest.CaptureFixture[str]) -> None:
        cells = commands.relations(workspace=workspace)

        assert [cell.meta for cell in cells] == [
            {"type": "relation", "relation": "docs"},
            {"type": "relation", "relation": "tests", "description": "Related tests."},
        ]
        assert capsys.readouterr() == ("", "")

    def test_empty_configuration(self) -> None:
        assert commands.relations(workspace=Workspace()) == []
