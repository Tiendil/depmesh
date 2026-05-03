from __future__ import annotations

from pathlib import Path

import pytest

from depmesh.discovery.sources.list import ListSource
from depmesh.domain.entities import Relation
from depmesh.workspace import errors
from depmesh.workspace.config import discover_config, load_config, parse_config
from depmesh.workspace.entities import RelationConfig


def write_config(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8")


@pytest.fixture
def relation_config_text() -> str:
    return '[[relations]]\nid = "tests"\n'


@pytest.fixture
def config_path(tmp_path: Path, relation_config_text: str) -> Path:
    path = tmp_path / "depmesh.toml"
    write_config(path, relation_config_text)
    return path


@pytest.fixture
def project_config_path(tmp_path: Path, relation_config_text: str) -> Path:
    path = tmp_path / "project" / "depmesh.toml"
    path.parent.mkdir()
    write_config(path, relation_config_text)
    return path


@pytest.fixture
def invalid_config_path(tmp_path: Path) -> Path:
    path = tmp_path / "depmesh.toml"
    write_config(path, "[")
    return path


class TestDiscoverConfig:
    def test_success_from_current_directory(self, config_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.chdir(config_path.parent)

        assert discover_config() == config_path

    def test_success_from_nested_directory(self, config_path: Path) -> None:
        nested = config_path.parent / "a" / "b"
        nested.mkdir(parents=True)

        assert discover_config(cwd=nested) == config_path

    def test_not_found(self, tmp_path: Path) -> None:
        assert discover_config(cwd=tmp_path) is None


class TestLoadConfig:
    def test_discovered_config_not_found(self, tmp_path: Path) -> None:
        with pytest.raises(errors.ConfigNotFound):
            load_config(cwd=tmp_path)

    def test_relative_config_path_is_resolved_against_cwd(self, project_config_path: Path) -> None:
        workspace = load_config(Path("project/depmesh.toml"), cwd=project_config_path.parent.parent)

        assert workspace.root == project_config_path.parent
        assert workspace.relations == (Relation(id="tests"),)

    def test_rules_are_compiled_into_runtime_sources(self, tmp_path: Path) -> None:
        config_path = tmp_path / "depmesh.toml"
        write_config(
            config_path,
            """
[[relations]]
id = "tests"

[[rules]]
relation = "tests"
input = { type = "glob", pattern = "@/src/{*module}.py" }
output = { type = "list", artifacts = ["@/tests/test_{module}.py"] }
""",
        )

        workspace = load_config(config_path)

        assert isinstance(workspace.rules[0].output_source, ListSource)

    def test_invalid_toml(self, invalid_config_path: Path) -> None:
        with pytest.raises(errors.ConfigInvalid):
            load_config(invalid_config_path)


class TestParseConfig:
    def test_valid_minimal_config(self, tmp_path: Path) -> None:
        config = parse_config(
            {
                "relations": [
                    {
                        "id": "tests",
                        "description": "Tests related to the input artifacts.",
                    }
                ],
                "rules": [
                    {
                        "relation": "tests",
                        "input": {"type": "glob", "pattern": "./src/{*module}.py"},
                        "output": {"type": "list", "artifacts": ["./tests/test_{module}.py"]},
                    }
                ],
            },
            config_path=tmp_path / "depmesh.toml",
        )

        assert config.relations == (
            RelationConfig(
                id="tests",
                description="Tests related to the input artifacts.",
            ),
        )
        assert config.rules[0].input_predicate.type == "glob"
        assert config.version == 1

    def test_version_omitted_defaults_to_one(self, tmp_path: Path) -> None:
        config = parse_config(
            {"relations": [{"id": "tests"}]},
            config_path=tmp_path / "depmesh.toml",
        )

        assert config.version == 1
        assert config.relations[0].id == "tests"

    def test_relations_omitted_defaults_to_empty(self, tmp_path: Path) -> None:
        config = parse_config({}, config_path=tmp_path / "depmesh.toml")

        assert config.relations == ()

    def test_relations_empty_is_allowed(self, tmp_path: Path) -> None:
        config = parse_config({"relations": []}, config_path=tmp_path / "depmesh.toml")

        assert config.relations == ()

    def test_unknown_top_level_field(self, tmp_path: Path) -> None:
        with pytest.raises(errors.ConfigInvalid):
            parse_config(
                {"relations": [{"id": "tests"}], "unknown": True},
                config_path=tmp_path / "depmesh.toml",
            )

    def test_unsupported_version(self, tmp_path: Path) -> None:
        with pytest.raises(errors.ConfigInvalid):
            parse_config(
                {"version": 2, "relations": [{"id": "tests"}]},
                config_path=tmp_path / "depmesh.toml",
            )

    def test_duplicate_relation_ids(self, tmp_path: Path) -> None:
        with pytest.raises(errors.ConfigInvalid):
            parse_config(
                {
                    "relations": [
                        {"id": "tests"},
                        {"id": "tests"},
                    ]
                },
                config_path=tmp_path / "depmesh.toml",
            )

    def test_rule_references_unknown_relation(self, tmp_path: Path) -> None:
        with pytest.raises(errors.ConfigInvalid):
            parse_config(
                {
                    "relations": [{"id": "tests"}],
                    "rules": [
                        {
                            "relation": "imports",
                            "input": {"type": "one_of", "artifacts": ["./src/a.py"]},
                            "output": {"type": "list", "artifacts": ["./src/b.py"]},
                        }
                    ],
                },
                config_path=tmp_path / "depmesh.toml",
            )

    def test_output_template_must_be_provided_by_every_input_predicate(self, tmp_path: Path) -> None:
        with pytest.raises(errors.ConfigInvalid):
            parse_config(
                {
                    "relations": [{"id": "tests"}],
                    "rules": [
                        {
                            "relation": "tests",
                            "input": {
                                "type": "any",
                                "items": [
                                    {"type": "glob", "pattern": "./src/{*module}.py"},
                                    {"type": "one_of", "artifacts": ["./src/special.py"]},
                                ],
                            },
                            "output": {"type": "list", "artifacts": ["./tests/test_{module}.py"]},
                        }
                    ],
                },
                config_path=tmp_path / "depmesh.toml",
            )
