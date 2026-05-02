from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest
from typer.testing import CliRunner

from depmesh.cli.application import app, main


def touch(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("", encoding="utf-8")


def write_project(tmp_path: Path) -> None:
    touch(tmp_path / "src/a.py")
    touch(tmp_path / "src/b.py")
    touch(tmp_path / "tests/test_a.py")
    touch(tmp_path / "tests/test_b.py")
    (tmp_path / "depmesh.toml").write_text(
        """
[[relations]]
id = "tests"
description = "Tests related to the input artifacts."

[[relations]]
id = "tested_by"
description = "Artifacts tested by the input artifacts."

[[rules]]
relation = "tests"
artifact = { type = "glob", pattern = "./src/{*module}.py" }
dependency = { type = "path", path = "./tests/test_{module}.py" }

[[rules]]
relation = "tested_by"
artifact = { type = "glob", pattern = "./tests/test_{*module}.py" }
dependency = { type = "path", path = "./src/{module}.py" }
""",
        encoding="utf-8",
    )


class TestApp:
    def test_protocol_choices__match_cli_contract(self) -> None:
        result = CliRunner().invoke(app, ["--protocol", "invalid", "dependencies", "./src/a.py"])

        assert result.exit_code == 1
        assert "human" in result.output
        assert "llm" in result.output
        assert "automation" in result.output


class TestDependencies:
    def test_empty_config_outputs_no_dependencies(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        config_path = tmp_path / "depmesh.toml"
        config_path.write_text("", encoding="utf-8")
        monkeypatch.chdir(tmp_path)

        result = CliRunner().invoke(app, ["dependencies", "./src/a.py"])

        assert result.exit_code == 0
        assert result.output == ""

    def test_human_query_output(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        write_project(tmp_path)
        monkeypatch.chdir(tmp_path)

        result = CliRunner().invoke(app, ["dependencies", "./src/a.py"])

        assert result.exit_code == 0
        assert result.output == "tests:\n  ./tests/test_a.py\n"

    def test_llm_query_output_includes_relation_description(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        write_project(tmp_path)
        monkeypatch.chdir(tmp_path)

        result = CliRunner().invoke(app, ["--protocol", "llm", "dependencies", "./src/a.py"])

        assert result.exit_code == 0
        assert result.output == (
            "## tests\n\n"
            "Tests related to the input artifacts.\n\n"
            "- ./tests/test_a.py\n"
        )

    def test_automation_query_output_is_json_lines(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        write_project(tmp_path)
        monkeypatch.chdir(tmp_path)

        result = CliRunner().invoke(app, ["--protocol", "automation", "dependencies", "./src/a.py"])

        assert result.exit_code == 0
        records = [json.loads(line) for line in result.output.splitlines()]
        assert records == [{"type": "dependency", "relation": "tests", "dependency": "./tests/test_a.py"}]

    def test_reverse_relation_query_output(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        write_project(tmp_path)
        monkeypatch.chdir(tmp_path)

        result = CliRunner().invoke(app, ["dependencies", "--relation", "tested_by", "./tests/test_a.py"])

        assert result.exit_code == 0
        assert result.output == "tested_by:\n  ./src/a.py\n"

    def test_default_query_output_includes_reverse_relations_when_configured(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        write_project(tmp_path)
        monkeypatch.chdir(tmp_path)

        result = CliRunner().invoke(app, ["dependencies", "./tests/test_a.py"])

        assert result.exit_code == 0
        assert result.output == "tested_by:\n  ./src/a.py\n"

    def test_short_alias(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        write_project(tmp_path)
        monkeypatch.chdir(tmp_path)

        result = CliRunner().invoke(app, ["deps", "./src/a.py"])

        assert result.exit_code == 0
        assert result.output == "tests:\n  ./tests/test_a.py\n"

    def test_protocol_is_not_a_dependencies_option(self) -> None:
        result = CliRunner().invoke(app, ["dependencies", "--protocol", "llm", "./src/a.py"])

        assert result.exit_code != 0
        assert "--protocol" in result.output

    def test_invalid_arguments_exit_code(self) -> None:
        result = CliRunner().invoke(app, ["dependencies"])

        assert result.exit_code == 1
        assert "at least one artifact is required" in result.output

    def test_config_error_exit_code(self, tmp_path: Path) -> None:
        result = CliRunner().invoke(app, ["--config", str(tmp_path / "missing.toml"), "dependencies", "./src/a.py"])

        assert result.exit_code == 2
        assert "could not read configuration" in result.output

    def test_query_error_exit_code(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        write_project(tmp_path)
        monkeypatch.chdir(tmp_path)

        result = CliRunner().invoke(app, ["dependencies", "--relation", "missing", "./src/a.py"])

        assert result.exit_code == 3
        assert "unknown relation `missing`" in result.output

    def test_automation_error_is_stdout_json(self, tmp_path: Path) -> None:
        result = CliRunner().invoke(
            app,
            ["--config", str(tmp_path / "missing.toml"), "--protocol", "automation", "dependencies", "./src/a.py"],
        )

        assert result.exit_code == 2
        assert json.loads(result.output)["type"] == "error"


class TestRelations:
    def test_human_output(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        write_project(tmp_path)
        monkeypatch.chdir(tmp_path)

        result = CliRunner().invoke(app, ["relations"])

        assert result.exit_code == 0
        assert result.output == (
            "tested_by:\n"
            "  Artifacts tested by the input artifacts.\n\n"
            "tests:\n"
            "  Tests related to the input artifacts.\n"
        )

    def test_short_alias(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        write_project(tmp_path)
        monkeypatch.chdir(tmp_path)

        result = CliRunner().invoke(app, ["rels"])

        assert result.exit_code == 0
        assert "tests:" in result.output

    def test_llm_output(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        write_project(tmp_path)
        monkeypatch.chdir(tmp_path)

        result = CliRunner().invoke(app, ["--protocol", "llm", "relations"])

        assert result.exit_code == 0
        assert result.output == (
            "## tested_by\n\n"
            "Artifacts tested by the input artifacts.\n\n"
            "## tests\n\n"
            "Tests related to the input artifacts.\n"
        )

    def test_automation_output(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        write_project(tmp_path)
        monkeypatch.chdir(tmp_path)

        result = CliRunner().invoke(app, ["--protocol", "automation", "relations"])

        assert result.exit_code == 0
        assert [json.loads(line) for line in result.output.splitlines()] == [
            {
                "type": "relation",
                "id": "tested_by",
                "description": "Artifacts tested by the input artifacts.",
            },
            {
                "type": "relation",
                "id": "tests",
                "description": "Tests related to the input artifacts.",
            },
        ]

    def test_config_error_exit_code(self, tmp_path: Path) -> None:
        result = CliRunner().invoke(app, ["--config", str(tmp_path / "missing.toml"), "relations"])

        assert result.exit_code == 2
        assert "could not read configuration" in result.output


class TestSkill:
    def test_skill_defaults_to_llm_protocol(self) -> None:
        result = CliRunner().invoke(app, ["skill"])

        assert result.exit_code == 0
        assert result.output.startswith("# depmesh usage\n")

    def test_skill_automation_protocol(self) -> None:
        result = CliRunner().invoke(app, ["--protocol", "automation", "skill"])

        assert result.exit_code == 0
        assert json.loads(result.output)["type"] == "skill"

    def test_global_config_option_is_accepted(self, tmp_path: Path) -> None:
        result = CliRunner().invoke(app, ["--config", str(tmp_path / "missing.toml"), "skill"])

        assert result.exit_code == 0
        assert result.output.startswith("# depmesh usage\n")


class TestVersion:
    def test_version_output(self) -> None:
        result = CliRunner().invoke(app, ["version"])

        assert result.exit_code == 0
        assert result.output == "0.1.0\n"

    def test_global_options_are_accepted(self, tmp_path: Path) -> None:
        result = CliRunner().invoke(
            app,
            ["--config", str(tmp_path / "missing.toml"), "--protocol", "automation", "version"],
        )

        assert result.exit_code == 0
        assert result.output == "0.1.0\n"


class TestMain:
    def test_success(self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
        monkeypatch.setattr(sys, "argv", ["depmesh", "version"])

        with pytest.raises(SystemExit) as exit_info:
            main()

        assert exit_info.value.code == 0
        assert capsys.readouterr().out == "0.1.0\n"
