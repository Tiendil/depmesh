from collections.abc import Iterator
from pathlib import Path

import pytest
from llm_tool_cli.cli.errors import InvalidArguments
from llm_tool_cli.config import load_config
from llm_tool_cli.config.project import ProjectConfig, project_config
from llm_tool_cli.core.result import Err
from llm_tool_cli.output import output
from llm_tool_cli.output.tests.helpers import CollectingEmitter, warning_messages
from llm_tool_cli.paths import PathInput, ProjectConfigPath
from llm_tool_cli.paths.errors import InvalidProjectPath, PathResolutionFailed
from llm_tool_cli.protocol import Protocol
from llm_tool_cli.protocol.logic_cells.warning import WarningCell
from pytest_mock import MockerFixture

from depmesh.discovery.errors import UnknownRelationFilter
from depmesh.domain.entities import ArtifactId, Dependency, RelationId
from depmesh.protocol.cells import DependenciesCell
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
        self,
        collected_output: CollectingEmitter,
        project: PathInput,
        workspace: Workspace,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        cwd = project / "src"
        cwd.mkdir()

        commands.dependencies(
            [ArtifactId("b.py"), ArtifactId("@/src/a.py"), ArtifactId("./a.py")],
            [],
            workspace=workspace,
            cwd=PathInput(cwd),
        ).unwrap()
        cell = collected_output.cells[-1]
        assert isinstance(cell, DependenciesCell)

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
        assert capsys.readouterr() == ("", "")

    def test_filters_relations(
        self, collected_output: CollectingEmitter, project: PathInput, workspace: Workspace
    ) -> None:
        commands.dependencies(
            [ArtifactId("@/src/a.py")], [RelationId("docs"), RelationId("docs")], workspace=workspace, cwd=project
        ).unwrap()
        cell = collected_output.cells[-1]
        assert isinstance(cell, DependenciesCell)

        assert cell.result.dependencies == (
            Dependency(relation=RelationId("docs"), dependency=ArtifactId("@/README.md")),
        )

    @pytest.mark.parametrize("artifacts", [[], [ArtifactId("@/unmatched")]])
    def test_empty_result(
        self,
        collected_output: CollectingEmitter,
        project: PathInput,
        workspace: Workspace,
        artifacts: list[ArtifactId],
    ) -> None:
        commands.dependencies(artifacts, [], workspace=workspace, cwd=project).unwrap()
        cell = collected_output.cells[-1]
        assert isinstance(cell, DependenciesCell)

        assert cell.result.dependencies == ()
        assert cell.render(Protocol.automation) == []

    def test_emits_warnings_during_query_and_results_afterwards(
        self, collected_output: CollectingEmitter, project: PathInput, workspace: Workspace
    ) -> None:
        with (project / "depmesh.toml").open("a", encoding="utf-8") as config:
            config.write(
                '\n[[rules]]\nrelation = "tests"\n'
                'input = { type = "glob", pattern = "@/src/*.py" }\n'
                'output = { type = "files", pattern = "@/../outside" }\n'
            )
        output.get().emit([WarningCell(message="earlier warning")]).unwrap()
        workspace = construct_workspace(load_config(project / "depmesh.toml", Config).unwrap())
        commands.dependencies([ArtifactId("@/src/a.py")], [], workspace=workspace, cwd=project).unwrap()
        assert warning_messages()[0] == "earlier warning"
        assert "outside" in warning_messages()[1]
        assert len(collected_output.cells) == 3
        assert isinstance(collected_output.cells[-1], DependenciesCell)

    def test_unknown_relation_precedes_input_validation(
        self, collected_output: CollectingEmitter, project: PathInput, workspace: Workspace
    ) -> None:
        assert commands.dependencies(
            [ArtifactId("@/../outside")], [RelationId("unknown")], workspace=workspace, cwd=project
        ).unwrap_err() == [UnknownRelationFilter(relation=RelationId("unknown"))]

    def test_invalid_input_becomes_argument_error(
        self, collected_output: CollectingEmitter, project: PathInput, workspace: Workspace
    ) -> None:
        failures = commands.dependencies(
            [ArtifactId("@/../outside")], [], workspace=workspace, cwd=project
        ).unwrap_err()

        assert len(failures) == 1
        assert isinstance(failures[0], InvalidArguments)

    def test_resolution_failure_is_preserved(
        self, collected_output: CollectingEmitter, project: PathInput, workspace: Workspace, mocker: MockerFixture
    ) -> None:
        error = PathResolutionFailed(path=str(project), reason="denied")
        mocker.patch.object(commands, "resolve_project_root", return_value=Err([error]))

        assert commands.dependencies([ArtifactId("@/a")], [], workspace=workspace, cwd=project).unwrap_err() == [error]

    def test_input_resolution_failure_is_preserved(
        self, collected_output: CollectingEmitter, project: PathInput, workspace: Workspace, mocker: MockerFixture
    ) -> None:
        error = PathResolutionFailed(path="~/a.py", reason="home unavailable")
        mocker.patch.object(commands, "normalize_input_artifacts", return_value=Err([error]))

        assert commands.dependencies([ArtifactId("~/a.py")], [], workspace=workspace, cwd=project).unwrap_err() == [
            error
        ]

    def test_query_failure_is_not_an_argument_error(
        self, collected_output: CollectingEmitter, project: PathInput, workspace: Workspace, mocker: MockerFixture
    ) -> None:
        error = InvalidProjectPath(path="@/../dependency")
        mocker.patch.object(commands, "query_dependencies", return_value=Err([error]))

        assert commands.dependencies(
            [ArtifactId("@/src/a.py")], [], workspace=workspace, cwd=project
        ).unwrap_err() == [error]


class TestRelations:
    def test_returns_ordered_cells(
        self, collected_output: CollectingEmitter, workspace: Workspace, capsys: pytest.CaptureFixture[str]
    ) -> None:
        commands.relations(workspace=workspace).unwrap()
        cells = collected_output.cells

        assert [cell.model_dump()["meta"] for cell in cells] == [
            {"type": "relation", "relation": "docs"},
            {"type": "relation", "relation": "tests", "description": "Related tests."},
        ]
        assert capsys.readouterr() == ("", "")

    def test_empty_configuration(self, collected_output: CollectingEmitter) -> None:
        commands.relations(workspace=Workspace()).unwrap()
        assert collected_output.cells == []
