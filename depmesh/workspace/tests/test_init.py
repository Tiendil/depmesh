from __future__ import annotations

import importlib.resources
from pathlib import Path

import pytest
import tomli

from depmesh.workspace import errors
from depmesh.workspace.config import parse_config
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
        parse_config(tomli.loads(read_base_config_fixture()), config_path=tmp_path / "depmesh.toml")


class TestInitializeConfig:
    def test_default_path(self, tmp_path: Path) -> None:
        config_path = initialize_config(cwd=tmp_path)

        assert config_path == tmp_path / "depmesh.toml"
        assert config_path.read_text(encoding="utf-8") == read_base_config_fixture()

    def test_relative_explicit_path(self, tmp_path: Path) -> None:
        config_path = initialize_config(Path("custom.toml"), cwd=tmp_path)

        assert config_path == tmp_path / "custom.toml"
        assert 'id = "governed_by"' in config_path.read_text(encoding="utf-8")

    def test_existing_file(self, tmp_path: Path) -> None:
        config_path = tmp_path / "depmesh.toml"
        config_path.write_text("version = 1\n", encoding="utf-8")

        with pytest.raises(errors.ConfigAlreadyExists):
            initialize_config(cwd=tmp_path)

        assert config_path.read_text(encoding="utf-8") == "version = 1\n"

    def test_write_error(self, tmp_path: Path) -> None:
        with pytest.raises(errors.ConfigUnwritable):
            initialize_config(Path("missing/depmesh.toml"), cwd=tmp_path)
