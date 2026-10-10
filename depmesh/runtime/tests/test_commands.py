from pathlib import Path

import pytest
from llm_tool_cli.cli.errors import InvalidArguments
from llm_tool_cli.config import errors as config_errors
from llm_tool_cli.core.result import Err
from llm_tool_cli.paths import PathInput, ProjectConfigPath
from llm_tool_cli.paths.errors import InvalidProjectPath, PathResolutionFailed
from llm_tool_cli.protocol import Protocol
from pytest_mock import MockerFixture

from depmesh.core import warnings
from depmesh.discovery.errors import UnknownRelationFilter
from depmesh.domain.entities import ArtifactId, Dependency, RelationId
from depmesh.runtime import commands


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


class TestDependencies:
    def test_merges_inputs_into_complete_cell_without_cli(
        self, project: PathInput, capsys: pytest.CaptureFixture[str]
    ) -> None:
        cwd = project / "src"
        cwd.mkdir()

        cell = commands.dependencies(
            [ArtifactId("b.py"), ArtifactId("@/src/a.py"), ArtifactId("./a.py")], [], cwd=PathInput(cwd)
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

    def test_filters_relations(self, project: PathInput) -> None:
        cell = commands.dependencies(
            [ArtifactId("@/src/a.py")], [RelationId("docs"), RelationId("docs")], cwd=project
        ).unwrap()

        assert cell.result.dependencies == (
            Dependency(relation=RelationId("docs"), dependency=ArtifactId("@/README.md")),
        )

    @pytest.mark.parametrize("artifacts", [[], [ArtifactId("@/unmatched")]])
    def test_empty_result(self, project: PathInput, artifacts: list[ArtifactId]) -> None:
        cell = commands.dependencies(artifacts, [], cwd=project).unwrap()

        assert cell.result.dependencies == ()
        assert cell.warnings == []
        assert cell.render(Protocol.automation) == []

    def test_snapshots_warnings_after_query(self, project: PathInput) -> None:
        with (project / "depmesh.toml").open("a", encoding="utf-8") as config:
            config.write(
                '\n[[rules]]\nrelation = "tests"\n'
                'input = { type = "glob", pattern = "@/src/*.py" }\n'
                'output = { type = "files", pattern = "@/../outside" }\n'
            )
        warnings.add("earlier warning")

        cell = commands.dependencies([ArtifactId("@/src/a.py")], [], cwd=project).unwrap()

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

    def test_config_failure_precedes_query_validation(self, tmp_path: Path) -> None:
        failures = commands.dependencies(
            [ArtifactId("@/../outside")],
            [RelationId("unknown")],
            cwd=PathInput(tmp_path),
            config_path=ProjectConfigPath(tmp_path / "missing.toml"),
        ).unwrap_err()

        assert len(failures) == 1
        assert isinstance(failures[0], config_errors.Unreadable)

    def test_unknown_relation_precedes_input_validation(self, project: PathInput) -> None:
        assert commands.dependencies(
            [ArtifactId("@/../outside")], [RelationId("unknown")], cwd=project
        ).unwrap_err() == [UnknownRelationFilter(relation=RelationId("unknown"))]

    def test_invalid_input_becomes_argument_error(self, project: PathInput) -> None:
        failures = commands.dependencies([ArtifactId("@/../outside")], [], cwd=project).unwrap_err()

        assert len(failures) == 1
        assert isinstance(failures[0], InvalidArguments)

    def test_resolution_failure_is_preserved(self, project: PathInput, mocker: MockerFixture) -> None:
        error = PathResolutionFailed(path=str(project), reason="denied")
        mocker.patch.object(commands, "resolve_project_root", return_value=Err([error]))

        assert commands.dependencies([ArtifactId("@/a")], [], cwd=project).unwrap_err() == [error]

    def test_input_resolution_failure_is_preserved(self, project: PathInput, mocker: MockerFixture) -> None:
        error = PathResolutionFailed(path="~/a.py", reason="home unavailable")
        mocker.patch.object(commands, "normalize_input_artifacts", return_value=Err([error]))

        assert commands.dependencies([ArtifactId("~/a.py")], [], cwd=project).unwrap_err() == [error]

    def test_query_failure_is_not_an_argument_error(self, project: PathInput, mocker: MockerFixture) -> None:
        error = InvalidProjectPath(path="@/../dependency")
        mocker.patch.object(commands, "query_dependencies", return_value=Err([error]))

        assert commands.dependencies([ArtifactId("@/src/a.py")], [], cwd=project).unwrap_err() == [error]


class TestRelations:
    def test_returns_ordered_cells(self, project: PathInput, capsys: pytest.CaptureFixture[str]) -> None:
        cells = commands.relations(cwd=project).unwrap()

        assert [cell.meta for cell in cells] == [
            {"type": "relation", "relation": "docs"},
            {"type": "relation", "relation": "tests", "description": "Related tests."},
        ]
        assert capsys.readouterr() == ("", "")

    def test_empty_configuration(self, tmp_path: Path) -> None:
        (tmp_path / "depmesh.toml").write_text("", encoding="utf-8")

        assert commands.relations(cwd=PathInput(tmp_path)).unwrap() == []

    def test_config_failure(self, tmp_path: Path) -> None:
        failures = commands.relations(cwd=PathInput(tmp_path)).unwrap_err()

        assert len(failures) == 1
        assert isinstance(failures[0], config_errors.NotFound)


class TestInitialize:
    @pytest.mark.parametrize("filename", [None, "custom.toml"])
    def test_returns_success_cell(
        self, tmp_path: Path, filename: str | None, capsys: pytest.CaptureFixture[str]
    ) -> None:
        path = ProjectConfigPath(Path(filename)) if filename is not None else None

        cell = commands.initialize(cwd=PathInput(tmp_path), config_path=path).unwrap()

        created = tmp_path / (filename or "depmesh.toml")
        assert cell.content == "Configuration created."
        assert cell.meta == {"type": "operation_succeeded", "path": str(created)}
        assert created.is_file()
        assert commands.relations(cwd=PathInput(tmp_path), config_path=ProjectConfigPath(created)).is_ok()
        assert capsys.readouterr() == ("", "")

    def test_existing_configuration_is_preserved(self, project: PathInput) -> None:
        path = project / "depmesh.toml"
        original = path.read_bytes()

        failures = commands.initialize(cwd=project).unwrap_err()

        assert len(failures) == 1
        assert isinstance(failures[0], config_errors.AlreadyExists)
        assert path.read_bytes() == original


class TestLoadWorkspace:
    def test_discovers_parent_configuration(self, project: PathInput) -> None:
        cwd = project / "nested"
        cwd.mkdir()

        workspace = commands._load_workspace(cwd=PathInput(cwd), config_path=None).unwrap()

        assert workspace.root == project
        assert set(workspace.relations_by_id) == {RelationId("tests"), RelationId("docs")}
        assert len(workspace.rules) == 2

    def test_explicit_configuration_sets_root(self, project: PathInput) -> None:
        config = project / "nested/custom.toml"
        config.parent.mkdir()
        config.write_text('[[relations]]\nid = "custom"\n', encoding="utf-8")

        workspace = commands._load_workspace(
            cwd=project, config_path=ProjectConfigPath(Path("nested/custom.toml"))
        ).unwrap()

        assert workspace.root == config.parent
        assert set(workspace.relations_by_id) == {RelationId("custom")}

    @pytest.mark.parametrize("content", [None, "not valid TOML", "version = 2"])
    def test_configuration_errors(self, tmp_path: Path, content: str | None) -> None:
        if content is not None:
            (tmp_path / "depmesh.toml").write_text(content, encoding="utf-8")

        failures = commands._load_workspace(cwd=PathInput(tmp_path), config_path=None).unwrap_err()

        expected = {
            None: config_errors.NotFound,
            "not valid TOML": config_errors.InvalidToml,
            "version = 2": config_errors.ValidationFailed,
        }[content]
        assert len(failures) == 1
        assert isinstance(failures[0], expected)
