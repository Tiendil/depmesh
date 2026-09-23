from __future__ import annotations

import json
import sys
from importlib import metadata
from pathlib import Path

import pytest
from llm_tool_cli.config import errors as config_errors
from llm_tool_cli.core import errors as shared_errors
from typer.testing import CliRunner

from depmesh.cli import errors as cli_errors
from depmesh.cli.application import app, main
from depmesh.core import errors as core_errors
from depmesh.discovery import errors as discovery_errors
from depmesh.domain.entities import RelationId
from depmesh.workspace import errors as workspace_errors


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
input = { type = "glob", pattern = "@/src/{*module}.py" }
output = {
    type = "list",
    artifacts = ["@/tests/test_{module}.py"],
}

[[rules]]
relation = "tested_by"
input = { type = "glob", pattern = "@/tests/test_{*module}.py" }
output = { type = "list", artifacts = ["@/src/{module}.py"] }
""",
        encoding="utf-8",
    )


class SharedFailure(shared_errors.Error):
    code = "shared_failure"


class ProjectFailure(core_errors.Error):
    code = "project_failure"


class TestCommandContext:
    @pytest.mark.parametrize("protocol", ["human", "llm", "automation"])
    @pytest.mark.parametrize(
        ("error", "exit_code"),
        [
            (config_errors.DiscoveryFailed(Path("/config.toml"), "denied"), 2),
            (config_errors.PathResolutionFailed(Path("/config.toml"), "denied"), 2),
            (config_errors.Unreadable(Path("/config.toml"), "denied"), 2),
            (config_errors.InvalidEncoding(Path("/config.toml"), "invalid UTF-8"), 2),
            (config_errors.InvalidToml(Path("/config.toml"), "invalid TOML"), 2),
            (config_errors.ValidationFailed(Path("/config.toml"), "invalid version"), 2),
            (config_errors.AlreadyExists(Path("/config.toml"), "exists"), 2),
            (config_errors.Unwritable(Path("/config.toml"), "denied"), 2),
            (config_errors.NotFound(Path("/project"), "config.toml was not found"), 2),
            (workspace_errors.ConfigTemplateUnreadable("base_config.toml", "denied"), 2),
            (cli_errors.InvalidArguments("invalid argument"), 1),
            (discovery_errors.UnknownRelationFilter(RelationId("missing")), 3),
            (SharedFailure("shared failure", details={"context": "shared"}), 3),
            (ProjectFailure("project failure", details={"context": "local"}), 3),
        ],
    )
    def test_native_records_and_exit_categories(
        self, monkeypatch: pytest.MonkeyPatch, protocol: str, error: shared_errors.Error, exit_code: int
    ) -> None:
        def fail_version(_distribution: str) -> str:
            raise error

        monkeypatch.setattr(metadata, "version", fail_version)

        result = CliRunner().invoke(app, ["--protocol", protocol, "version"])

        assert result.exit_code == exit_code
        if protocol == "automation":
            assert json.loads(result.stdout) == error.as_record()
            assert result.stderr == ""
        else:
            assert result.stdout == ""
            assert error.message in result.stderr

    def test_unexpected_failure_is_not_rendered_as_expected(self, monkeypatch: pytest.MonkeyPatch) -> None:
        original = RuntimeError("unexpected failure")

        def fail_version(_distribution: str) -> str:
            raise original

        monkeypatch.setattr(metadata, "version", fail_version)

        result = CliRunner().invoke(app, ["--protocol", "automation", "version"])

        assert result.exception is original
        assert result.stdout == ""
        assert result.stderr == ""


class TestApp:
    def test_protocol_choices__match_cli_contract(self) -> None:
        result = CliRunner().invoke(app, ["--protocol", "invalid", "dependencies", "./src/a.py"])

        assert result.exit_code == 1
        assert "human" in result.output
        assert "llm" in result.output
        assert "automation" in result.output


class TestDependencies:
    @pytest.mark.parametrize("explicit", [False, True])
    def test_config_symlink_selects_expected_root(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, explicit: bool
    ) -> None:
        target_root = tmp_path / "target"
        write_project(target_root)
        config_path = tmp_path / "depmesh.toml"
        config_path.symlink_to(target_root / "depmesh.toml")
        touch(tmp_path / "src/a.py")
        monkeypatch.chdir(tmp_path)
        artifact = (target_root if explicit else tmp_path) / "src/a.py"
        arguments = ["--config", str(config_path)] if explicit else []

        result = CliRunner().invoke(app, [*arguments, "dependencies", str(artifact)])

        assert result.exit_code == 0
        assert result.stdout == "tests:\n  @/tests/test_a.py\n"

    def test_empty_config_outputs_no_dependencies(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
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
        assert result.output == "tests:\n  @/tests/test_a.py\n"

    def test_human_query_accepts_root_anchored_input(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        write_project(tmp_path)
        monkeypatch.chdir(tmp_path)

        result = CliRunner().invoke(app, ["dependencies", "@/src/a.py"])

        assert result.exit_code == 0
        assert result.output == "tests:\n  @/tests/test_a.py\n"

    def test_human_query_accepts_absolute_input(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        write_project(tmp_path)
        monkeypatch.chdir(tmp_path)

        result = CliRunner().invoke(app, ["dependencies", str(tmp_path / "src" / "a.py")])

        assert result.exit_code == 0
        assert result.output == "tests:\n  @/tests/test_a.py\n"

    def test_human_query_accepts_relative_input_from_working_directory(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        write_project(tmp_path)
        monkeypatch.chdir(tmp_path / "src")

        result = CliRunner().invoke(app, ["dependencies", "a.py"])

        assert result.exit_code == 0
        assert result.output == "tests:\n  @/tests/test_a.py\n"

    def test_human_query_rejects_input_outside_project(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        write_project(tmp_path)
        outside = tmp_path.parent / "outside.py"
        outside.write_text("", encoding="utf-8")
        monkeypatch.chdir(tmp_path)

        result = CliRunner().invoke(app, ["dependencies", str(outside)])

        assert result.exit_code == 1
        assert "invalid project path" in result.output

    def test_human_query_output_merges_multiple_input_artifacts(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        write_project(tmp_path)
        monkeypatch.chdir(tmp_path)

        result = CliRunner().invoke(app, ["dependencies", "./src/a.py", "./src/b.py"])

        assert result.exit_code == 0
        assert result.output == "tests:\n  @/tests/test_a.py\n  @/tests/test_b.py\n"

    def test_llm_query_output_includes_relation_description(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        write_project(tmp_path)
        monkeypatch.chdir(tmp_path)

        result = CliRunner().invoke(app, ["--protocol", "llm", "dependencies", "./src/a.py"])

        assert result.exit_code == 0
        assert result.output == "## tests\n\nTests related to the input artifacts.\n\n- @/tests/test_a.py\n"

    def test_automation_query_output_is_json_lines(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        write_project(tmp_path)
        monkeypatch.chdir(tmp_path)

        result = CliRunner().invoke(app, ["--protocol", "automation", "dependencies", "./src/a.py"])

        assert result.exit_code == 0
        records = [json.loads(line) for line in result.output.splitlines()]
        assert records == [{"type": "dependency", "relation": "tests", "dependency": "@/tests/test_a.py"}]

    def test_reverse_relation_query_output(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        write_project(tmp_path)
        monkeypatch.chdir(tmp_path)

        result = CliRunner().invoke(app, ["dependencies", "--relation", "tested_by", "./tests/test_a.py"])

        assert result.exit_code == 0
        assert result.output == "tested_by:\n  @/src/a.py\n"

    def test_default_query_output_includes_reverse_relations_when_configured(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        write_project(tmp_path)
        monkeypatch.chdir(tmp_path)

        result = CliRunner().invoke(app, ["dependencies", "./tests/test_a.py"])

        assert result.exit_code == 0
        assert result.output == "tested_by:\n  @/src/a.py\n"

    def test_short_alias(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        write_project(tmp_path)
        monkeypatch.chdir(tmp_path)

        result = CliRunner().invoke(app, ["deps", "./src/a.py"])

        assert result.exit_code == 0
        assert result.output == "tests:\n  @/tests/test_a.py\n"

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
        assert "missing.toml" in result.stderr
        assert result.stdout == ""

    def test_query_error_exit_code(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        write_project(tmp_path)
        monkeypatch.chdir(tmp_path)

        result = CliRunner().invoke(app, ["dependencies", "--relation", "missing", "./src/a.py"])

        assert result.exit_code == 3
        assert "unknown relation `missing`" in result.output

    def test_automation_error_is_stdout_json(self, tmp_path: Path) -> None:
        config_path = tmp_path / "missing.toml"
        result = CliRunner().invoke(
            app,
            ["--config", str(config_path), "--protocol", "automation", "dependencies", "./src/a.py"],
        )

        assert result.exit_code == 2
        record = json.loads(result.stdout)
        assert record == {
            "type": "error",
            "code": "config_unreadable",
            "message": f"{config_path}: {record['reason']}",
            "path": str(config_path),
            "reason": record["reason"],
        }
        assert "No such file" in record["reason"]
        assert result.stderr == ""

    def test_automation_invalid_toml_preserves_parser_reason(self, tmp_path: Path) -> None:
        config_path = tmp_path / "invalid.toml"
        config_path.write_text("value =\n", encoding="utf-8")

        result = CliRunner().invoke(
            app,
            ["--config", str(config_path), "--protocol", "automation", "dependencies", "./src/a.py"],
        )

        assert result.exit_code == 2
        record = json.loads(result.stdout)
        assert record["type"] == "error"
        assert record["code"] == "config_invalid_toml"
        assert record["path"] == str(config_path)
        assert record["message"] == f"{config_path}: {record['reason']}"
        assert "line 1" in record["reason"]
        assert result.stderr == ""

    def test_automation_invalid_encoding_preserves_reason(self, tmp_path: Path) -> None:
        config_path = tmp_path / "invalid.toml"
        config_path.write_bytes(b"\xff")

        result = CliRunner().invoke(
            app,
            ["--config", str(config_path), "--protocol", "automation", "dependencies", "./src/a.py"],
        )

        assert result.exit_code == 2
        record = json.loads(result.stdout)
        assert record["code"] == "config_invalid_encoding"
        assert record["path"] == str(config_path)
        assert record["reason"]
        assert result.stderr == ""

    @pytest.mark.parametrize(
        ("text", "reason"),
        [
            ("version = 2\n", "Input should be 1"),
            ('[[relations]]\nid = "tests"\n[[relations]]\nid = "tests"\n', "duplicate relation id `tests`"),
        ],
    )
    def test_automation_invalid_schema_preserves_validation_details(
        self, tmp_path: Path, text: str, reason: str
    ) -> None:
        config_path = tmp_path / "invalid.toml"
        config_path.write_text(text, encoding="utf-8")

        result = CliRunner().invoke(
            app,
            ["--config", str(config_path), "--protocol", "automation", "dependencies", "./src/a.py"],
        )

        assert result.exit_code == 2
        record = json.loads(result.stdout)
        assert record["type"] == "error"
        assert record["code"] == "config_validation_failed"
        assert record["message"] == f"{config_path}: {record['reason']}"
        assert record["path"] == str(config_path)
        assert reason in record["reason"]
        assert "validation" not in record
        assert result.stderr == ""


class TestRelations:
    def test_discovers_nearest_config(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        write_project(tmp_path)
        nested_root = tmp_path / "nested"
        cwd = nested_root / "deeper"
        cwd.mkdir(parents=True)
        (nested_root / "depmesh.toml").write_text('[[relations]]\nid = "nearest"\n', encoding="utf-8")
        monkeypatch.chdir(cwd)

        result = CliRunner().invoke(app, ["relations"])

        assert result.exit_code == 0
        assert result.stdout == "nearest:\n"

    @pytest.mark.parametrize("config_path", ["home/depmesh.toml", "~/depmesh.toml"])
    def test_explicit_relative_and_home_paths(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, config_path: str
    ) -> None:
        home_dir = tmp_path / "home"
        home_dir.mkdir()
        (home_dir / "depmesh.toml").write_text('[[relations]]\nid = "selected"\n', encoding="utf-8")
        (tmp_path / "depmesh.toml").write_text("version = 2\n", encoding="utf-8")
        monkeypatch.chdir(tmp_path)
        monkeypatch.setenv("HOME", str(home_dir))

        result = CliRunner().invoke(app, ["--config", config_path, "relations"])

        assert result.exit_code == 0
        assert result.stdout == "selected:\n"

    def test_missing_discovered_config_uses_shared_error(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.chdir(tmp_path)

        result = CliRunner().invoke(app, ["--protocol", "automation", "relations"])

        assert result.exit_code == 2
        record = json.loads(result.stdout)
        assert record == {
            "type": "error",
            "code": "config_not_found",
            "path": str(tmp_path),
            "reason": record["reason"],
            "message": f"{tmp_path}: {record['reason']}",
        }
        assert "depmesh.toml" in record["reason"]
        assert result.stderr == ""

    def test_explicit_missing_config_does_not_use_discovery(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        write_project(tmp_path)
        monkeypatch.chdir(tmp_path)

        result = CliRunner().invoke(app, ["--protocol", "automation", "--config", "missing.toml", "relations"])

        assert result.exit_code == 2
        record = json.loads(result.stdout)
        assert record["code"] == "config_unreadable"
        assert record["path"] == str(tmp_path / "missing.toml")

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
        assert "missing.toml" in result.stderr
        assert result.stdout == ""


class TestSkill:
    def test_skill_defaults_to_llm_protocol(self) -> None:
        result = CliRunner().invoke(app, ["skill"])

        assert result.exit_code == 0
        assert result.output.startswith("# `depmesh` Usage\n")

    def test_skill_usage_document(self) -> None:
        result = CliRunner().invoke(app, ["skill", "usage"])

        assert result.exit_code == 0
        assert result.output.startswith("# `depmesh` Usage\n")

    def test_skill_configuration_document(self) -> None:
        result = CliRunner().invoke(app, ["skill", "configuration"])

        assert result.exit_code == 0
        assert result.output.startswith("# `depmesh` Configuration\n")

    def test_skill_initialization_document(self) -> None:
        result = CliRunner().invoke(app, ["skill", "initialization"])

        assert result.exit_code == 0
        assert result.output.startswith("# `depmesh` Initialization\n")

    def test_skill_rejects_unknown_document(self) -> None:
        result = CliRunner().invoke(app, ["skill", "missing"])

        assert result.exit_code != 0
        assert "usage" in result.output
        assert "configuration" in result.output
        assert "initialization" in result.output

    def test_skill_automation_protocol(self) -> None:
        result = CliRunner().invoke(app, ["--protocol", "automation", "skill"])

        assert result.exit_code == 0
        assert json.loads(result.output)["type"] == "skill"

    def test_skill_automation_protocol_includes_selected_document(self) -> None:
        result = CliRunner().invoke(app, ["--protocol", "automation", "skill", "configuration"])

        assert result.exit_code == 0
        record = json.loads(result.output)
        assert record["document"] == "configuration"
        assert record["text"].startswith("# `depmesh` Configuration\n")

    def test_global_config_option_is_accepted(self, tmp_path: Path) -> None:
        result = CliRunner().invoke(app, ["--config", str(tmp_path / "missing.toml"), "skill"])

        assert result.exit_code == 0
        assert result.output.startswith("# `depmesh` Usage\n")


class TestInit:
    def test_expands_home_in_config_path(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        home_dir = tmp_path / "home"
        home_dir.mkdir()
        monkeypatch.chdir(tmp_path)
        monkeypatch.setenv("HOME", str(home_dir))

        result = CliRunner().invoke(app, ["--config", "~/custom.toml", "init"])

        assert result.exit_code == 0
        assert result.stdout == f"created {home_dir / 'custom.toml'}\n"
        assert (home_dir / "custom.toml").is_file()

    def test_creates_default_config(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.chdir(tmp_path)

        result = CliRunner().invoke(app, ["init"])

        config_path = tmp_path / "depmesh.toml"
        assert result.exit_code == 0
        assert result.output == f"created {config_path}\n"
        assert 'id = "governed_by"' in config_path.read_text(encoding="utf-8")
        assert 'id = "governs"' in config_path.read_text(encoding="utf-8")

    def test_uses_global_config_path(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.chdir(tmp_path)

        result = CliRunner().invoke(app, ["--config", "custom.toml", "init"])

        assert result.exit_code == 0
        assert (tmp_path / "custom.toml").is_file()

    def test_does_not_overwrite_existing_config(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.chdir(tmp_path)
        config_path = tmp_path / "depmesh.toml"
        config_path.write_text("version = 1\n", encoding="utf-8")

        result = CliRunner().invoke(app, ["init"])

        assert result.exit_code == 2
        assert "File exists" in result.stderr
        assert result.stdout == ""
        assert config_path.read_text(encoding="utf-8") == "version = 1\n"


class TestVersion:
    def test_version_output(self) -> None:
        result = CliRunner().invoke(app, ["version"])

        assert result.exit_code == 0
        assert result.output == f"{metadata.version('depmesh')}\n"

    def test_global_options_are_accepted(self, tmp_path: Path) -> None:
        result = CliRunner().invoke(
            app,
            ["--config", str(tmp_path / "missing.toml"), "--protocol", "automation", "version"],
        )

        assert result.exit_code == 0
        assert result.output == f"{metadata.version('depmesh')}\n"


class TestMain:
    def test_success(self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
        monkeypatch.setattr(sys, "argv", ["depmesh", "version"])

        with pytest.raises(SystemExit) as exit_info:
            main()

        assert exit_info.value.code == 0
        assert capsys.readouterr().out == f"{metadata.version('depmesh')}\n"
