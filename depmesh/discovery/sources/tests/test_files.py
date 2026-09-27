from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import pytest
from llm_tool_cli.paths import ProjectRootPath
from llm_tool_cli.paths.errors import InvalidProjectPath, PathResolutionFailed
from pytest_mock import MockerFixture

from depmesh.core import warnings
from depmesh.discovery import errors
from depmesh.discovery.artifacts import CaptureName, EvaluationContext
from depmesh.discovery.sources.files import FilesSource, FilesSourceConfig
from depmesh.domain.entities import ArtifactId, RelationId


def touch(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("", encoding="utf-8")


class TestFilesSource:
    @pytest.mark.parametrize("pattern", [None, "@/*.py"])
    def test_evaluate__rejects_symlink_outside_project(self, tmp_path: Path, pattern: str | None) -> None:
        project = tmp_path / "project"
        project.mkdir()
        outside = tmp_path / "outside.py"
        touch(outside)
        link = project / "link.py"
        link.symlink_to(outside)
        source = FilesSource(FilesSourceConfig.model_validate({"type": "files", "pattern": pattern}))
        context = EvaluationContext(root=ProjectRootPath(project), relation_id=RelationId("all"), captures={})

        assert source.evaluate(context).unwrap_err() == [InvalidProjectPath(path=str(link))]

    @pytest.mark.parametrize("pattern", [None, "@/*.py"])
    def test_evaluate__preserves_path_resolution_failure(
        self, tmp_path: Path, mocker: MockerFixture, pattern: str | None
    ) -> None:
        path = tmp_path / "file.py"
        touch(path)
        cause = PermissionError("permission denied")
        resolve = Path.resolve

        def fail_target(candidate: Path) -> Path:
            if candidate == path:
                raise cause
            return resolve(candidate)

        mocker.patch.object(Path, "resolve", autospec=True, side_effect=fail_target)
        source = FilesSource(FilesSourceConfig.model_validate({"type": "files", "pattern": pattern}))
        context = EvaluationContext(root=ProjectRootPath(tmp_path), relation_id=RelationId("all"), captures={})

        failures = source.evaluate(context).unwrap_err()

        assert len(failures) == 1
        failure = failures[0]
        assert isinstance(failure, PathResolutionFailed)
        assert failure.code == "path_resolution_failed"
        assert failure.path == str(path)
        assert failure.cause == cause

    def test_evaluate__filesystem_failure_returns_error(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        original = PermissionError("permission denied")

        def fail_glob(_path: Path, _pattern: str) -> Iterator[Path]:
            raise original

        monkeypatch.setattr(Path, "rglob", fail_glob)
        source = FilesSource(FilesSourceConfig(type="files"))
        context = EvaluationContext(root=ProjectRootPath(tmp_path), relation_id=RelationId("all"), captures={})

        failure = source.evaluate(context).unwrap_err()[0]

        assert isinstance(failure, errors.FilesUnreadable)
        assert failure.cause is original

    def test_variables__extracts_template_variables(self) -> None:
        source = FilesSourceConfig.model_validate({"type": "files", "pattern": "@/tests/test_{module}.py"})

        assert source.variables() == {CaptureName("module")}

    def test_evaluate__returns_all_files_without_pattern(self, tmp_path: Path) -> None:
        touch(tmp_path / "src/a.py")
        touch(tmp_path / "docs/a.md")
        source = FilesSource(FilesSourceConfig(type="files"))
        context = EvaluationContext(root=ProjectRootPath(tmp_path), relation_id=RelationId("all"), captures={})

        assert source.evaluate(context).unwrap() == [ArtifactId("@/docs/a.md"), ArtifactId("@/src/a.py")]

    def test_evaluate__returns_matching_files(self, tmp_path: Path) -> None:
        touch(tmp_path / "tests/test_a.py")
        touch(tmp_path / "tests/test_b.py")
        source = FilesSource(
            FilesSourceConfig.model_validate({"type": "files", "pattern": "@/tests/test_{module}.py"})
        )
        context = EvaluationContext(
            root=ProjectRootPath(tmp_path), relation_id=RelationId("tests"), captures={"module": "a"}
        )

        assert source.evaluate(context).unwrap() == [ArtifactId("@/tests/test_a.py")]

    @pytest.mark.parametrize("pattern", ["../tests/*.py", "@/../*.py", "@/a//b", "@/", "@file", "."])
    def test_evaluate__invalid_pattern_adds_warning(self, tmp_path: Path, pattern: str) -> None:
        warnings.clear()
        source = FilesSource(FilesSourceConfig.model_validate({"type": "files", "pattern": pattern}))
        context = EvaluationContext(root=ProjectRootPath(tmp_path), relation_id=RelationId("tests"), captures={})

        assert source.evaluate(context).unwrap() == []
        assert warnings.read() == [f"relation `tests`: skipped invalid files source pattern `{pattern}`"]
        warnings.clear()

    def test_evaluate__expands_home_in_pattern(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("HOME", str(tmp_path))
        project = tmp_path / "project"
        touch(project / "file.py")
        source = FilesSource(FilesSourceConfig.model_validate({"type": "files", "pattern": "~/project/*.py"}))
        context = EvaluationContext(root=ProjectRootPath(project), relation_id=RelationId("tests"), captures={})

        assert source.evaluate(context).unwrap() == [ArtifactId("@/file.py")]

    def test_evaluate__preserves_literal_home_segment(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("HOME", str(tmp_path.parent))
        touch(tmp_path / "~" / "file.py")
        source = FilesSource(FilesSourceConfig.model_validate({"type": "files", "pattern": "@/~/*.py"}))
        context = EvaluationContext(root=ProjectRootPath(tmp_path), relation_id=RelationId("tests"), captures={})

        assert source.evaluate(context).unwrap() == [ArtifactId("@/~/file.py")]

    def test_evaluate__home_outside_project_adds_warning(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        warnings.clear()
        monkeypatch.setenv("HOME", str(tmp_path))
        source = FilesSource(FilesSourceConfig.model_validate({"type": "files", "pattern": "~/*.py"}))
        context = EvaluationContext(
            root=ProjectRootPath(tmp_path / "project"), relation_id=RelationId("tests"), captures={}
        )

        assert source.evaluate(context).unwrap() == []
        assert warnings.read() == ["relation `tests`: skipped invalid files source pattern `~/*.py`"]
        warnings.clear()

    def test_evaluate__home_expansion_failure_is_fatal(self, tmp_path: Path, mocker: MockerFixture) -> None:
        warnings.clear()
        cause = RuntimeError("unknown home")
        mocker.patch.object(Path, "expanduser", side_effect=cause)
        source = FilesSource(FilesSourceConfig.model_validate({"type": "files", "pattern": "~/*.py"}))
        context = EvaluationContext(root=ProjectRootPath(tmp_path), relation_id=RelationId("tests"), captures={})

        failure = source.evaluate(context).unwrap_err()[0]

        assert isinstance(failure, PathResolutionFailed)
        assert failure.code == "path_resolution_failed"
        assert failure.path == "~/*.py"
        assert failure.cause == cause
        assert warnings.read() == []
        warnings.clear()

    def test_evaluate__pattern_resolution_failure_is_fatal(self, tmp_path: Path) -> None:
        warnings.clear()
        link = tmp_path / "loop"
        link.symlink_to(link)
        source = FilesSource(FilesSourceConfig.model_validate({"type": "files", "pattern": "@/loop/*.py"}))
        context = EvaluationContext(root=ProjectRootPath(tmp_path), relation_id=RelationId("tests"), captures={})

        failure = source.evaluate(context).unwrap_err()[0]

        assert isinstance(failure, PathResolutionFailed)
        assert failure.code == "path_resolution_failed"
        assert failure.path == str(link / "*.py")
        assert isinstance(failure.cause, (OSError, RuntimeError))
        assert warnings.read() == []
        warnings.clear()
