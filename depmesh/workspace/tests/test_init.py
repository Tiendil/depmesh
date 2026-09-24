from __future__ import annotations

import importlib.resources
from pathlib import Path

import pytest
from llm_tool_cli.config import errors as config_errors
from llm_tool_cli.config import load_config
from llm_tool_cli.core.errors import EnvironmentErrors
from llm_tool_cli.core.result import Err, Result

from depmesh.workspace import Config, construct_workspace, errors, init
from depmesh.workspace.init import BASE_CONFIG_FIXTURE, initialize_config


def read_base_config_fixture() -> str:
    return (
        importlib.resources.files("depmesh.workspace")
        .joinpath("fixtures", BASE_CONFIG_FIXTURE)
        .read_text(encoding="utf-8")
    )


class TestBaseConfigFixture:
    def test_content(self) -> None:
        text = read_base_config_fixture()

        assert text.startswith("version = 1\n")
        assert 'id = "governed_by"' in text
        assert 'id = "governs"' in text

    def test_valid_config(self, tmp_path: Path) -> None:
        config_path = tmp_path / "depmesh.toml"
        config_path.write_text(read_base_config_fixture(), encoding="utf-8")

        config = load_config(config_path, Config).unwrap()
        workspace = construct_workspace(config, root=config_path.parent)

        assert tuple(relation.id for relation in workspace.relations) == ("governed_by", "governs")


class TestInitializeConfig:
    def test_default_path(self, tmp_path: Path) -> None:
        config_path = initialize_config(cwd=tmp_path).unwrap()

        assert config_path == tmp_path / "depmesh.toml"
        assert config_path.read_text(encoding="utf-8") == read_base_config_fixture()

    def test_relative_explicit_path(self, tmp_path: Path) -> None:
        config_path = initialize_config(Path("custom.toml"), cwd=tmp_path).unwrap()

        assert config_path == tmp_path / "custom.toml"
        assert 'id = "governed_by"' in config_path.read_text(encoding="utf-8")

    def test_home_relative_path(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        home_dir = tmp_path / "home"
        home_dir.mkdir()
        monkeypatch.setenv("HOME", str(home_dir))

        config_path = initialize_config(Path("~/custom.toml"), cwd=tmp_path).unwrap()

        assert config_path == home_dir / "custom.toml"
        assert config_path.read_text(encoding="utf-8") == read_base_config_fixture()

    def test_relative_cwd(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.chdir(tmp_path)
        root = tmp_path / "project"
        root.mkdir()

        config_path = initialize_config(cwd=Path("project")).unwrap()

        assert config_path == root / "depmesh.toml"
        assert config_path.read_text(encoding="utf-8") == read_base_config_fixture()

    def test_parent_config_is_not_reused(self, tmp_path: Path) -> None:
        parent_config = tmp_path / "depmesh.toml"
        parent_config.write_text("version = 1\n", encoding="utf-8")
        root = tmp_path / "project"
        root.mkdir()

        config_path = initialize_config(cwd=root).unwrap()

        assert config_path == root / "depmesh.toml"
        assert config_path.read_text(encoding="utf-8") == read_base_config_fixture()
        assert parent_config.read_text(encoding="utf-8") == "version = 1\n"

    def test_existing_file(self, tmp_path: Path) -> None:
        config_path = tmp_path / "depmesh.toml"
        config_path.write_text("version = 1\n", encoding="utf-8")

        failures = initialize_config(cwd=tmp_path).unwrap_err()
        assert isinstance(failures[0], config_errors.AlreadyExists)

        assert config_path.read_text(encoding="utf-8") == "version = 1\n"

    def test_write_error(self, tmp_path: Path) -> None:
        failures = initialize_config(Path("missing/depmesh.toml"), cwd=tmp_path).unwrap_err()
        assert isinstance(failures[0], config_errors.Unwritable)

    def test_path_resolution_failure_propagates(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        original = config_errors.PathResolutionFailed(path=tmp_path / "depmesh.toml", reason="permission denied")

        def fail_resolution(_path: Path, _cwd: Path) -> Result[Path, EnvironmentErrors]:
            return Err([original])

        monkeypatch.setattr(init, "resolve_config_path", fail_resolution)

        failures = initialize_config(cwd=tmp_path).unwrap_err()
        assert failures[0] is original

    @pytest.mark.parametrize("content", [None, b"\xff"])
    def test_template_read_failure_preserves_cause(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, content: bytes | None
    ) -> None:
        fixtures = tmp_path / "fixtures"
        fixtures.mkdir()
        if content is not None:
            (fixtures / BASE_CONFIG_FIXTURE).write_bytes(content)
        monkeypatch.setattr(importlib.resources, "files", lambda _package: tmp_path)

        failure = initialize_config(cwd=tmp_path).unwrap_err()[0]
        assert isinstance(failure, errors.ConfigTemplateUnreadable)
        original = failure.cause
        expected_cause = FileNotFoundError if content is None else UnicodeDecodeError
        assert isinstance(original, expected_cause)
        assert failure.as_record() == {
            "type": "error",
            "code": "config_template_unreadable",
            "message": f"could not read configuration template `{BASE_CONFIG_FIXTURE}`: {original}",
            "template": BASE_CONFIG_FIXTURE,
            "reason": str(original),
        }
        assert not (tmp_path / "depmesh.toml").exists()
