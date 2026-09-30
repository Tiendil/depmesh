from __future__ import annotations

import base64
import json
import re
import sys
import uuid
from importlib import metadata
from pathlib import Path

import pytest
from llm_tool_cli.cli import errors as cli_errors
from llm_tool_cli.config import errors as config_errors
from llm_tool_cli.core import errors as shared_errors
from llm_tool_cli.core.errors import EnvironmentErrors
from llm_tool_cli.core.result import Err, Result, UnwrapErrError, UnwrapError
from llm_tool_cli.paths import resolve_project_root
from llm_tool_cli.paths.errors import InvalidProjectPath, PathResolutionFailed
from llm_tool_cli.protocol.tests.helpers import assert_error_cells
from pytest_mock import MockerFixture
from typer.testing import CliRunner

from depmesh.cli.application import CommandContext, app, main
from depmesh.core import errors as core_errors
from depmesh.core import warnings
from depmesh.discovery import errors as discovery_errors
from depmesh.domain.entities import RelationId
from depmesh.workspace import Workspace


def normalize_cell_ids(text: str) -> str:
    return re.sub(
        r"(?m)^(--DEPMESH-CELL |----- DEPMESH CELL )[A-Za-z0-9_-]{22}( BEGIN--| END--| -----)$",
        r"\1<id>\2",
        text,
    )


def cell_records(text: str) -> list[dict[str, object]]:
    records = []
    for line in text.splitlines():
        record = json.loads(line)
        cell_id = record.pop("id")
        assert uuid.UUID(bytes=base64.urlsafe_b64decode(cell_id + "==")).version == 4
        records.append(record)
    return records


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


class SharedFailure(shared_errors.EnvironmentError):
    code: str = "shared_failure"
    context: str


class ProjectFailure(core_errors.EnvironmentError):
    code: str = "project_failure"
    context: str


class TestCommandContext:
    @pytest.mark.parametrize("protocol", ["human", "llm", "automation"])
    @pytest.mark.parametrize("command, code", [("relations", "config_unreadable"), ("init", "config_already_exists")])
    def test_config_path_directory_is_checked_by_configuration_operation(
        self, tmp_path: Path, protocol: str, command: str, code: str
    ) -> None:
        result = CliRunner().invoke(app, ["--config", str(tmp_path), "-p", protocol, command])

        assert result.exit_code == 2
        assert tmp_path.is_dir()
        assert not list(tmp_path.iterdir())
        if protocol == "automation":
            assert not result.stderr
            records = cell_records(result.stdout)
            assert len(records) == 1
            assert records[0]["type"] == "error"
            assert records[0]["code"] == code
            assert records[0]["path"] == str(tmp_path)
        else:
            assert not result.stdout
            separator = " = " if protocol == "human" else "="
            assert f"kind{separator}error\n" in result.stderr
            assert f"code{separator}{code}\n" in result.stderr
            assert f"path{separator}{tmp_path}\n" in result.stderr

    @pytest.mark.parametrize("command", ["skill", "version"])
    def test_config_path_unused_directory_does_not_prevent_execution(self, tmp_path: Path, command: str) -> None:
        result = CliRunner().invoke(app, ["--config", str(tmp_path), "-p", "automation", command])

        assert result.exit_code == 0
        assert not result.stderr
        records = cell_records(result.stdout)
        assert len(records) == 1
        assert records[0]["type"] == command
        assert not list(tmp_path.iterdir())

    def test_config_path_does_not_leak_between_invocations(self, mocker: MockerFixture, tmp_path: Path) -> None:
        write_project(tmp_path)
        mocker.patch("pathlib.Path.cwd", return_value=tmp_path)
        runner = CliRunner()

        for name in ["first.toml", "second.toml"]:
            warnings.clear()
            result = runner.invoke(app, ["--config", name, "-p", "automation", "relations"])

            assert result.exit_code == 2
            assert not result.stderr
            record = cell_records(result.stdout)[0]
            assert record["code"] == "config_unreadable"
            assert record["path"] == str(tmp_path / name)

        warnings.clear()
        result = runner.invoke(app, ["relations"])

        assert result.exit_code == 0
        assert not result.stderr
        assert result.stdout.startswith("----- DEPMESH CELL ")
        assert "relation = tests" in result.stdout

    def test_protocol_defaults_are_selected_for_each_invocation(self) -> None:
        invocations = [
            (["skill"], "--DEPMESH-CELL ", "kind=skill\n"),
            (["version"], "----- DEPMESH CELL ", "kind = version\n"),
            (["-p", "human", "skill"], "----- DEPMESH CELL ", "kind = skill\n"),
            (["skill"], "--DEPMESH-CELL ", "kind=skill\n"),
        ]
        for arguments, prefix, kind in invocations:
            warnings.clear()
            result = CliRunner().invoke(app, arguments)

            assert result.exit_code == 0
            assert not result.stderr
            assert result.stdout.startswith(prefix)
            assert kind in result.stdout

    @pytest.mark.parametrize("protocol", ["human", "llm", "automation"])
    @pytest.mark.parametrize(
        "payload",
        [
            config_errors.Unreadable(path=Path("/config.toml"), reason="denied"),
            (config_errors.Unreadable(path=Path("/config.toml"), reason="denied"),),
            [config_errors.Unreadable(path=Path("/config.toml"), reason="denied"), "unexpected payload"],
        ],
    )
    def test_malformed_unwrap_payload_is_not_rendered_as_expected(
        self, mocker: MockerFixture, protocol: str, payload: object
    ) -> None:
        failure = UnwrapError(error=[])
        failure.details["error"] = payload
        mocker.patch.object(CommandContext, "load_workspace", side_effect=failure)

        result = CliRunner().invoke(app, ["--protocol", protocol, "relations"])

        assert result.exception == failure
        assert result.exit_code != 0
        assert not result.stdout
        assert not result.stderr

    @pytest.mark.parametrize("protocol", ["human", "llm", "automation"])
    def test_error_cells_include_guidance_and_keep_stream_policy(self, mocker: MockerFixture, protocol: str) -> None:
        failure = ProjectFailure(
            message="Problem with {error.context}.", context="project", ways_to_fix=["Check {error.context}."]
        )
        mocker.patch.object(CommandContext, "load_workspace", return_value=Err([failure]))

        result = CliRunner().invoke(app, ["--protocol", protocol, "relations"])

        assert result.exit_code == 3
        if protocol == "automation":
            assert not result.stderr
            assert cell_records(result.stdout) == [
                {
                    "type": "error",
                    "code": "project_failure",
                    "context": "project",
                    "content": "Problem with project.\nWay to fix: Check project.",
                }
            ]
        else:
            assert not result.stdout
            assert "Problem with project.\nWay to fix: Check project." in result.stderr

    @pytest.mark.parametrize("unwrap_in_helper", [False, True])
    @pytest.mark.parametrize("reverse", [False, True])
    @pytest.mark.parametrize("protocol", ["human", "llm", "automation"])
    def test_multiple_errors_keep_order_and_use_highest_code(
        self, monkeypatch: pytest.MonkeyPatch, unwrap_in_helper: bool, reverse: bool, protocol: str
    ) -> None:
        failures: EnvironmentErrors = [
            cli_errors.InvalidArguments(reason="invalid argument"),
            config_errors.Unreadable(path=Path("/config.toml"), reason="denied"),
            discovery_errors.UnknownRelationFilter(relation=RelationId("missing")),
        ]
        if reverse:
            failures.reverse()

        def fail_workspace(_self: CommandContext) -> Result[Workspace]:
            result: Result[Workspace] = Err(failures)
            if unwrap_in_helper:
                result.unwrap()
            return result

        monkeypatch.setattr(CommandContext, "load_workspace", fail_workspace)

        result = CliRunner().invoke(app, ["--protocol", protocol, "relations"])

        assert result.exit_code == 3
        if protocol == "automation":
            assert_error_cells([json.loads(line) for line in result.stdout.splitlines()], failures)
            assert not result.stderr
        else:
            assert not result.stdout
            separator = " = " if protocol == "human" else "="
            codes = [f"code{separator}{error.code}\n" for error in failures]
            assert all(code in result.stderr for code in codes)
            positions = [result.stderr.index(code) for code in codes]
            assert positions == sorted(positions)
            assert "cli_exit_code" not in result.stderr

    @pytest.mark.parametrize("protocol", ["human", "llm", "automation"])
    @pytest.mark.parametrize(
        ("error", "exit_code"),
        [
            (config_errors.DiscoveryFailed(path=Path("/config.toml"), reason="denied"), 2),
            (config_errors.PathResolutionFailed(path=Path("/config.toml"), reason="denied"), 2),
            (config_errors.Unreadable(path=Path("/config.toml"), reason="denied"), 2),
            (config_errors.InvalidEncoding(path=Path("/config.toml"), reason="invalid UTF-8"), 2),
            (config_errors.InvalidToml(path=Path("/config.toml"), reason="invalid TOML"), 2),
            (config_errors.ValidationFailed(path=Path("/config.toml"), reason="invalid version"), 2),
            (config_errors.AlreadyExists(path=Path("/config.toml"), reason="exists"), 2),
            (config_errors.Unwritable(path=Path("/config.toml"), reason="denied"), 2),
            (config_errors.NotFound(path=Path("/project"), reason="config.toml was not found"), 2),
            (
                config_errors.TemplateUnreadable(
                    path=Path("/config.toml"), template="base_config.toml", reason="denied"
                ),
                2,
            ),
            (cli_errors.InvalidArguments(reason="invalid argument"), 1),
            (discovery_errors.UnknownRelationFilter(relation=RelationId("missing")), 3),
            (InvalidProjectPath(path="@/../outside.py"), 3),
            (PathResolutionFailed(path="/project", reason="denied"), 3),
            (SharedFailure(message="shared failure", context="shared"), 3),
            (ProjectFailure(message="project failure", context="local"), 3),
        ],
    )
    def test_error_cells_and_exit_categories(
        self, monkeypatch: pytest.MonkeyPatch, protocol: str, error: shared_errors.EnvironmentError, exit_code: int
    ) -> None:
        def fail_workspace(_self: CommandContext) -> Result[Workspace]:
            return Err([error])

        monkeypatch.setattr(CommandContext, "load_workspace", fail_workspace)

        result = CliRunner().invoke(app, ["--protocol", protocol, "relations"])

        assert result.exit_code == exit_code
        if protocol == "automation":
            assert_error_cells([json.loads(line) for line in result.stdout.splitlines()], [error])
            assert result.stderr == ""
        else:
            assert result.stdout == ""
            assert error.format_message() in result.stderr
            prefix = "----- DEPMESH CELL " if protocol == "human" else "--DEPMESH-CELL "
            assert result.stderr.startswith(prefix)
            separator = " = " if protocol == "human" else "="
            assert f"kind{separator}error\n" in result.stderr
            assert f"code{separator}{error.code}\n" in result.stderr

    @pytest.mark.parametrize(
        "original",
        [
            RuntimeError("unexpected failure"),
            shared_errors.InternalError("technical failure"),
            UnwrapErrError("successful value"),
        ],
    )
    def test_unexpected_failure_is_not_rendered_as_expected(
        self, monkeypatch: pytest.MonkeyPatch, original: Exception
    ) -> None:

        def fail_version(_distribution: str) -> str:
            raise original

        monkeypatch.setattr(metadata, "version", fail_version)

        result = CliRunner().invoke(app, ["--protocol", "automation", "version"])

        assert result.exception is original
        assert result.stdout == ""
        assert result.stderr == ""


class TestApp:
    @pytest.mark.parametrize("option", ["-h", "--help"])
    @pytest.mark.parametrize("command", [[], ["skill"]])
    def test_shared_help(self, option: str, command: list[str]) -> None:
        result = CliRunner().invoke(app, [*command, option])

        assert result.exit_code == 0
        assert not result.stderr
        if command:
            assert "initialization" in result.stdout
            assert "workflows" not in result.stdout
        else:
            assert "--show-completion" in result.stdout
            assert "--install-completion" in result.stdout

    def test_skill_completion_uses_local_documents(self) -> None:
        result = CliRunner().invoke(
            app,
            [],
            prog_name="depmesh",
            env={"_DEPMESH_COMPLETE": "complete_bash", "COMP_WORDS": "depmesh skill i", "COMP_CWORD": "2"},
        )

        assert result.exit_code == 0
        assert result.stdout.splitlines() == ["initialization"]
        assert not result.stderr

    @pytest.mark.parametrize("option", ["-p", "--protocol"])
    @pytest.mark.parametrize("protocol", ["invalid", "{protocol}", "{"])
    def test_protocol_choices__match_cli_contract(self, option: str, protocol: str) -> None:
        result = CliRunner().invoke(app, [option, protocol, "dependencies", "./src/a.py"])

        assert result.exit_code == 1
        assert result.stderr.startswith("--DEPMESH-CELL ")
        assert result.stderr.count(" BEGIN--\n") == 1
        assert "kind=error\n" in result.stderr
        assert "code=invalid_arguments\n" in result.stderr
        assert protocol in result.stderr
        assert "human" in result.stderr
        assert "llm" in result.stderr
        assert "automation" in result.stderr
        assert result.stdout == ""


class TestDependencies:
    @pytest.mark.parametrize("protocol", ["human", "llm", "automation"])
    def test_repeated_queries_preserve_payloads_with_random_ids(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, protocol: str
    ) -> None:
        write_project(tmp_path)
        monkeypatch.chdir(tmp_path)
        arguments = ["-p", protocol, "dependencies", "@/src/b.py", "@/src/a.py", "@/src/a.py"]

        first = CliRunner().invoke(app, arguments)
        warnings.clear()
        second = CliRunner().invoke(app, arguments)

        assert first.exit_code == second.exit_code == 0
        assert first.stderr == second.stderr == ""
        assert first.stdout != second.stdout
        if protocol == "automation":
            assert (
                cell_records(first.stdout)
                == cell_records(second.stdout)
                == [
                    {"type": "dependency", "relation": "tests", "dependency": "@/tests/test_a.py", "content": None},
                    {"type": "dependency", "relation": "tests", "dependency": "@/tests/test_b.py", "content": None},
                ]
            )
        else:
            assert normalize_cell_ids(first.stdout) == normalize_cell_ids(second.stdout)
            assert first.stdout.count("- @/tests/test_a.py\n") == 1
            assert first.stdout.index("- @/tests/test_a.py") < first.stdout.index("- @/tests/test_b.py")

    @pytest.mark.parametrize("protocol", ["human", "llm", "automation"])
    def test_warning_cells_follow_results_with_explicit_invocation_cleanup(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, protocol: str
    ) -> None:
        (tmp_path / "depmesh.toml").write_text(
            """[[relations]]
id = "tests"
[[rules]]
relation = "tests"
input = {type = "one_of", artifacts = ["@/a.py"]}
output = {type = "command", command = "printf '@/café.py'; printf 'notice' >&2"}
""",
            encoding="utf-8",
        )
        monkeypatch.chdir(tmp_path)

        result = CliRunner().invoke(app, ["-p", protocol, "dependencies", "@/a.py"])
        warnings.clear()
        following = CliRunner().invoke(app, ["-p", protocol, "dependencies", "@/other.py"])

        assert result.exit_code == following.exit_code == 0
        assert result.stderr == following.stderr == ""
        assert following.stdout == ""
        message = "relation `tests`: command stderr: notice"
        if protocol == "automation":
            assert cell_records(result.stdout) == [
                {"type": "dependency", "relation": "tests", "dependency": "@/café.py", "content": None},
                {"type": "warning", "message": message, "content": None},
            ]
        else:
            assert result.stdout.index("@/café.py") < result.stdout.index(message)
            assert result.stdout.startswith("----- DEPMESH CELL" if protocol == "human" else "--DEPMESH-CELL")

    def test_home_relative_input(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        write_project(tmp_path)
        monkeypatch.setenv("HOME", str(tmp_path))

        result = CliRunner().invoke(
            app,
            ["--config", str(tmp_path / "depmesh.toml"), "-p", "automation", "dependencies", "~/src/a.py"],
        )

        assert result.exit_code == 0
        assert cell_records(result.stdout) == [
            {"type": "dependency", "relation": "tests", "dependency": "@/tests/test_a.py", "content": None}
        ]

    @pytest.mark.parametrize(
        ("predicate", "source"),
        [
            (
                '{ type = "one_of", artifacts = ["~/src/a.py"] }',
                '{ type = "list", artifacts = ["@/tests/test_a.py"] }',
            ),
            ('{ type = "glob", pattern = "~/src/*.py" }', '{ type = "list", artifacts = ["@/tests/test_a.py"] }'),
            (
                '{ type = "one_of", artifacts = ["@/src/a.py"] }',
                '{ type = "list", artifacts = ["~/tests/test_a.py"] }',
            ),
            (
                '{ type = "one_of", artifacts = ["@/src/a.py"] }',
                '{ type = "command", command = "printf \'~/tests/test_a.py\'" }',
            ),
        ],
    )
    def test_home_relative_rule_paths(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, predicate: str, source: str
    ) -> None:
        config_path = tmp_path / "depmesh.toml"
        config_path.write_text(
            f'[[relations]]\nid = "tests"\n[[rules]]\nrelation = "tests"\ninput = {predicate}\noutput = {source}\n',
            encoding="utf-8",
        )
        monkeypatch.setenv("HOME", str(tmp_path))

        result = CliRunner().invoke(
            app, ["--config", str(config_path), "-p", "automation", "dependencies", "@/src/a.py"]
        )

        assert result.exit_code == 0
        assert cell_records(result.stdout) == [
            {"type": "dependency", "relation": "tests", "dependency": "@/tests/test_a.py", "content": None}
        ]

    def test_home_expansion_failure_uses_shared_diagnostic(self, tmp_path: Path, mocker: MockerFixture) -> None:
        write_project(tmp_path)
        expanduser = Path.expanduser

        def expand(path: Path) -> Path:
            if str(path).startswith("~"):
                raise RuntimeError("unknown home")
            return expanduser(path)

        mocker.patch.object(Path, "expanduser", expand)

        result = CliRunner().invoke(
            app,
            ["--config", str(tmp_path / "depmesh.toml"), "-p", "automation", "dependencies", "~/src/a.py"],
        )

        assert result.exit_code == 3
        record = cell_records(result.stdout)[0]
        assert record["code"] == "path_resolution_failed"
        assert record["path"] == "~/src/a.py"
        assert record["reason"] == "unknown home"
        assert "cause" not in record
        assert not result.stderr

    @pytest.mark.parametrize("protocol", ["human", "llm", "automation"])
    def test_target_resolution_failure_uses_shared_diagnostic(self, tmp_path: Path, protocol: str) -> None:
        write_project(tmp_path)
        link = tmp_path / "loop"
        link.symlink_to(link)
        target = link / "a.py"

        result = CliRunner().invoke(
            app, ["--config", str(tmp_path / "depmesh.toml"), "-p", protocol, "dependencies", str(target)]
        )

        assert result.exit_code == 3
        if protocol == "automation":
            diagnostic = json.loads(result.stdout)
            assert diagnostic["code"] == "path_resolution_failed"
            assert diagnostic["path"] == str(target)
            assert diagnostic["reason"]
            assert "cause" not in diagnostic
            assert not result.stderr
        else:
            assert not result.stdout
            assert str(target) in result.stderr

    @pytest.mark.parametrize("protocol", ["human", "llm", "automation"])
    def test_root_resolution_failure_uses_shared_diagnostic(
        self, tmp_path: Path, mocker: MockerFixture, protocol: str
    ) -> None:
        write_project(tmp_path)
        root = tmp_path / "loop"
        root.symlink_to(root)
        failure = resolve_project_root(root)
        mocker.patch("depmesh.cli.application.resolve_project_root", return_value=failure)

        result = CliRunner().invoke(
            app, ["--config", str(tmp_path / "depmesh.toml"), "-p", protocol, "dependencies", "@/src/a.py"]
        )

        assert result.exit_code == 3
        error = failure.unwrap_err()[0]
        if protocol == "automation":
            assert_error_cells([json.loads(line) for line in result.stdout.splitlines()], [error])
            assert not result.stderr
        else:
            assert not result.stdout
            assert error.format_message() in result.stderr

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
        assert normalize_cell_ids(result.stdout) == (
            "----- DEPMESH CELL <id> -----\n"
            "kind = dependencies\n"
            "media_type = text/markdown\n"
            "relation = tests\n"
            "type = dependencies\n"
            "\n"
            "Tests related to the input artifacts.\n"
            "\n"
            "- @/tests/test_a.py\n"
            "\n"
        )

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
        assert normalize_cell_ids(result.output) == (
            "----- DEPMESH CELL <id> -----\n"
            "kind = dependencies\n"
            "media_type = text/markdown\n"
            "relation = tests\n"
            "type = dependencies\n"
            "\n"
            "Tests related to the input artifacts.\n"
            "\n"
            "- @/tests/test_a.py\n"
            "\n"
        )

    @pytest.mark.parametrize("artifact", ["@/src/a.py", "@/src/../src/./a.py"])
    def test_human_query_accepts_root_anchored_input(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, artifact: str
    ) -> None:
        write_project(tmp_path)
        monkeypatch.chdir(tmp_path)

        result = CliRunner().invoke(app, ["dependencies", artifact])

        assert result.exit_code == 0
        assert normalize_cell_ids(result.output) == (
            "----- DEPMESH CELL <id> -----\n"
            "kind = dependencies\n"
            "media_type = text/markdown\n"
            "relation = tests\n"
            "type = dependencies\n"
            "\n"
            "Tests related to the input artifacts.\n"
            "\n"
            "- @/tests/test_a.py\n"
            "\n"
        )

    def test_invalid_root_anchored_input_keeps_argument_error(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        write_project(tmp_path)
        monkeypatch.chdir(tmp_path)

        result = CliRunner().invoke(app, ["--protocol", "automation", "dependencies", "@/../outside.py"])

        assert result.exit_code == 1
        assert cell_records(result.stdout)[0] == {
            "type": "error",
            "code": "invalid_arguments",
            "content": "invalid project path `@/../outside.py`",
            "reason": "invalid project path `@/../outside.py`",
        }
        assert result.stderr == ""

    def test_human_query_accepts_absolute_input(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        write_project(tmp_path)
        monkeypatch.chdir(tmp_path)

        result = CliRunner().invoke(app, ["dependencies", str(tmp_path / "src" / "a.py")])

        assert result.exit_code == 0
        assert normalize_cell_ids(result.output) == (
            "----- DEPMESH CELL <id> -----\n"
            "kind = dependencies\n"
            "media_type = text/markdown\n"
            "relation = tests\n"
            "type = dependencies\n"
            "\n"
            "Tests related to the input artifacts.\n"
            "\n"
            "- @/tests/test_a.py\n"
            "\n"
        )

    def test_human_query_accepts_relative_input_from_working_directory(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        write_project(tmp_path)
        monkeypatch.chdir(tmp_path / "src")

        result = CliRunner().invoke(app, ["dependencies", "a.py"])

        assert result.exit_code == 0
        assert normalize_cell_ids(result.output) == (
            "----- DEPMESH CELL <id> -----\n"
            "kind = dependencies\n"
            "media_type = text/markdown\n"
            "relation = tests\n"
            "type = dependencies\n"
            "\n"
            "Tests related to the input artifacts.\n"
            "\n"
            "- @/tests/test_a.py\n"
            "\n"
        )

    @pytest.mark.parametrize("protocol", ["human", "llm", "automation"])
    @pytest.mark.parametrize("filename", ["outside.py", "{name}.py"])
    def test_query_rejects_input_outside_project(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, protocol: str, filename: str
    ) -> None:
        write_project(tmp_path)
        outside = tmp_path.parent / filename
        outside.write_text("", encoding="utf-8")
        monkeypatch.chdir(tmp_path)

        result = CliRunner().invoke(app, ["--protocol", protocol, "dependencies", str(outside)])

        assert result.exit_code == 1
        reason = f"invalid project path `{outside}`"
        if protocol == "automation":
            assert cell_records(result.stdout)[0] == {
                "type": "error",
                "code": "invalid_arguments",
                "content": reason,
                "reason": reason,
            }
            assert result.stderr == ""
        else:
            assert reason in result.stderr
            assert result.stdout == ""

    def test_human_query_output_merges_multiple_input_artifacts(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        write_project(tmp_path)
        monkeypatch.chdir(tmp_path)

        result = CliRunner().invoke(app, ["dependencies", "./src/a.py", "./src/b.py"])

        assert result.exit_code == 0
        assert normalize_cell_ids(result.output) == (
            "----- DEPMESH CELL <id> -----\n"
            "kind = dependencies\n"
            "media_type = text/markdown\n"
            "relation = tests\n"
            "type = dependencies\n"
            "\n"
            "Tests related to the input artifacts.\n"
            "\n"
            "- @/tests/test_a.py\n"
            "- @/tests/test_b.py\n"
            "\n"
        )

    def test_llm_query_output_includes_relation_description(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        write_project(tmp_path)
        monkeypatch.chdir(tmp_path)

        result = CliRunner().invoke(app, ["--protocol", "llm", "dependencies", "./src/a.py"])

        assert result.exit_code == 0
        assert normalize_cell_ids(result.output) == (
            "--DEPMESH-CELL <id> BEGIN--\n"
            "kind=dependencies\n"
            "media_type=text/markdown\n"
            "relation=tests\n"
            "type=dependencies\n"
            "\n"
            "Tests related to the input artifacts.\n"
            "\n"
            "- @/tests/test_a.py\n"
            "--DEPMESH-CELL <id> END--\n"
        )

    def test_automation_query_output_is_json_lines(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        write_project(tmp_path)
        monkeypatch.chdir(tmp_path)

        result = CliRunner().invoke(app, ["--protocol", "automation", "dependencies", "./src/a.py"])

        assert result.exit_code == 0
        assert cell_records(result.output) == [
            {"type": "dependency", "relation": "tests", "dependency": "@/tests/test_a.py", "content": None}
        ]

    def test_reverse_relation_query_output(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        write_project(tmp_path)
        monkeypatch.chdir(tmp_path)

        result = CliRunner().invoke(app, ["dependencies", "--relation", "tested_by", "./tests/test_a.py"])

        assert result.exit_code == 0
        assert normalize_cell_ids(result.output) == (
            "----- DEPMESH CELL <id> -----\n"
            "kind = dependencies\n"
            "media_type = text/markdown\n"
            "relation = tested_by\n"
            "type = dependencies\n"
            "\n"
            "Artifacts tested by the input artifacts.\n"
            "\n"
            "- @/src/a.py\n"
            "\n"
        )

    def test_default_query_output_includes_reverse_relations_when_configured(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        write_project(tmp_path)
        monkeypatch.chdir(tmp_path)

        result = CliRunner().invoke(app, ["dependencies", "./tests/test_a.py"])

        assert result.exit_code == 0
        assert normalize_cell_ids(result.output) == (
            "----- DEPMESH CELL <id> -----\n"
            "kind = dependencies\n"
            "media_type = text/markdown\n"
            "relation = tested_by\n"
            "type = dependencies\n"
            "\n"
            "Artifacts tested by the input artifacts.\n"
            "\n"
            "- @/src/a.py\n"
            "\n"
        )

    def test_short_alias(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        write_project(tmp_path)
        monkeypatch.chdir(tmp_path)

        result = CliRunner().invoke(app, ["deps", "./src/a.py"])

        assert result.exit_code == 0
        assert normalize_cell_ids(result.output) == (
            "----- DEPMESH CELL <id> -----\n"
            "kind = dependencies\n"
            "media_type = text/markdown\n"
            "relation = tests\n"
            "type = dependencies\n"
            "\n"
            "Tests related to the input artifacts.\n"
            "\n"
            "- @/tests/test_a.py\n"
            "\n"
        )

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
        record = cell_records(result.stdout)[0]
        assert record == {
            "type": "error",
            "code": "config_unreadable",
            "content": f"{config_path}: {record['reason']}",
            "path": str(config_path),
            "reason": record["reason"],
        }
        assert isinstance(record["reason"], str)
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
        record = cell_records(result.stdout)[0]
        assert record["type"] == "error"
        assert record["code"] == "config_invalid_toml"
        assert record["path"] == str(config_path)
        assert record["content"] == f"{config_path}: {record['reason']}"
        assert isinstance(record["reason"], str)
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
        record = cell_records(result.stdout)[0]
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
        record = cell_records(result.stdout)[0]
        assert record["type"] == "error"
        assert record["code"] == "config_validation_failed"
        assert record["content"] == f"{config_path}: {record['reason']}"
        assert record["path"] == str(config_path)
        assert isinstance(record["reason"], str)
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
        assert normalize_cell_ids(result.stdout) == (
            "----- DEPMESH CELL <id> -----\n" "kind = relation\n" "relation = nearest\n" "type = relation\n" "\n"
        )

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
        assert normalize_cell_ids(result.stdout) == (
            "----- DEPMESH CELL <id> -----\n" "kind = relation\n" "relation = selected\n" "type = relation\n" "\n"
        )

    def test_missing_discovered_config_uses_shared_error(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.chdir(tmp_path)

        result = CliRunner().invoke(app, ["--protocol", "automation", "relations"])

        assert result.exit_code == 2
        record = cell_records(result.stdout)[0]
        assert record == {
            "type": "error",
            "code": "config_not_found",
            "path": str(tmp_path),
            "reason": record["reason"],
            "content": f"{tmp_path}: {record['reason']}",
        }
        assert isinstance(record["reason"], str)
        assert "depmesh.toml" in record["reason"]
        assert result.stderr == ""

    def test_explicit_missing_config_does_not_use_discovery(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        write_project(tmp_path)
        monkeypatch.chdir(tmp_path)

        result = CliRunner().invoke(app, ["--protocol", "automation", "--config", "missing.toml", "relations"])

        assert result.exit_code == 2
        record = cell_records(result.stdout)[0]
        assert record["code"] == "config_unreadable"
        assert record["path"] == str(tmp_path / "missing.toml")

    def test_human_output(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        write_project(tmp_path)
        monkeypatch.chdir(tmp_path)

        result = CliRunner().invoke(app, ["relations"])

        assert result.exit_code == 0
        assert normalize_cell_ids(result.output) == (
            "----- DEPMESH CELL <id> -----\n"
            "kind = relation\n"
            "description = Artifacts tested by the input artifacts.\n"
            "relation = tested_by\n"
            "type = relation\n"
            "\n"
            "----- DEPMESH CELL <id> -----\n"
            "kind = relation\n"
            "description = Tests related to the input artifacts.\n"
            "relation = tests\n"
            "type = relation\n"
            "\n"
        )

    def test_short_alias(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        write_project(tmp_path)
        monkeypatch.chdir(tmp_path)

        result = CliRunner().invoke(app, ["rels"])

        assert result.exit_code == 0
        assert "relation = tests\n" in result.output

    def test_llm_output(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        write_project(tmp_path)
        monkeypatch.chdir(tmp_path)

        result = CliRunner().invoke(app, ["--protocol", "llm", "relations"])

        assert result.exit_code == 0
        assert normalize_cell_ids(result.output) == (
            "--DEPMESH-CELL <id> BEGIN--\n"
            "kind=relation\n"
            "description=Artifacts tested by the input artifacts.\n"
            "relation=tested_by\n"
            "type=relation\n"
            "--DEPMESH-CELL <id> END--\n"
            "--DEPMESH-CELL <id> BEGIN--\n"
            "kind=relation\n"
            "description=Tests related to the input artifacts.\n"
            "relation=tests\n"
            "type=relation\n"
            "--DEPMESH-CELL <id> END--\n"
        )

    def test_automation_output(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        write_project(tmp_path)
        monkeypatch.chdir(tmp_path)

        result = CliRunner().invoke(app, ["--protocol", "automation", "relations"])

        assert result.exit_code == 0
        assert cell_records(result.output) == [
            {
                "type": "relation",
                "description": "Artifacts tested by the input artifacts.",
                "relation": "tested_by",
                "content": None,
            },
            {
                "type": "relation",
                "description": "Tests related to the input artifacts.",
                "relation": "tests",
                "content": None,
            },
        ]

    def test_config_error_exit_code(self, tmp_path: Path) -> None:
        result = CliRunner().invoke(app, ["--config", str(tmp_path / "missing.toml"), "relations"])

        assert result.exit_code == 2
        assert "missing.toml" in result.stderr
        assert result.stdout == ""


class TestSkill:
    def test_human_protocol(self) -> None:
        result = CliRunner().invoke(app, ["-p", "human", "skill"])

        assert result.exit_code == 0
        assert result.stderr == ""
        assert result.stdout.startswith("----- DEPMESH CELL ")
        assert "kind = skill\n" in result.stdout
        assert "type = skill\n" in result.stdout
        assert "document = usage\n" in result.stdout
        assert "# `depmesh` Usage\n" in result.stdout

    @pytest.mark.parametrize("protocol", ["human", "llm", "automation"])
    @pytest.mark.parametrize("content", [None, b"\xff"])
    def test_unreadable_document_reports_shared_error(
        self, tmp_path: Path, mocker: MockerFixture, protocol: str, content: bytes | None
    ) -> None:
        fixtures = tmp_path / "fixtures"
        fixtures.mkdir()
        if content is not None:
            (fixtures / "usage.md").write_bytes(content)
        mocker.patch("llm_tool_cli.skills.fixtures.importlib.resources.files", return_value=tmp_path)

        result = CliRunner().invoke(app, ["-p", protocol, "skill"])

        assert result.exit_code == 3
        if protocol == "automation":
            records = cell_records(result.stdout)
            assert len(records) == 1
            record = records[0]
            assert record["type"] == "error"
            assert record["document"] == "usage"
            assert record["code"] == "skill_unreadable"
            assert record["reason"]
            assert record["content"]
            assert result.stderr == ""
        else:
            assert result.stdout == ""
            separator = "=" if protocol == "llm" else " = "
            assert f"kind{separator}error\n" in result.stderr
            assert f"code{separator}skill_unreadable\n" in result.stderr
            assert f"document{separator}usage\n" in result.stderr

    def test_skill_defaults_to_llm_protocol(self) -> None:
        result = CliRunner().invoke(app, ["skill"])

        assert result.exit_code == 0
        assert result.output.startswith("--DEPMESH-CELL ")
        assert "type=skill\n" in result.output
        assert "# `depmesh` Usage\n" in result.output

    def test_skill_usage_document(self) -> None:
        result = CliRunner().invoke(app, ["skill", "usage"])

        assert result.exit_code == 0
        assert result.output.startswith("--DEPMESH-CELL ")
        assert "# `depmesh` Usage\n" in result.output

    def test_skill_configuration_document(self) -> None:
        result = CliRunner().invoke(app, ["skill", "configuration"])

        assert result.exit_code == 0
        assert result.output.startswith("--DEPMESH-CELL ")
        assert "# `depmesh` Configuration\n" in result.output

    def test_skill_initialization_document(self) -> None:
        result = CliRunner().invoke(app, ["skill", "initialization"])

        assert result.exit_code == 0
        assert result.output.startswith("--DEPMESH-CELL ")
        assert "# `depmesh` Initialization\n" in result.output

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

    @pytest.mark.parametrize("document", ["usage", "configuration", "initialization"])
    def test_skill_automation_protocol_includes_selected_document(self, document: str) -> None:
        result = CliRunner().invoke(app, ["--protocol", "automation", "skill", document])

        assert result.exit_code == 0
        assert result.stderr == ""
        records = cell_records(result.stdout)
        assert len(records) == 1
        assert records[0]["type"] == "skill"
        assert records[0]["document"] == document
        content = records[0]["content"]
        assert isinstance(content, str)
        assert content.startswith(f"# `depmesh` {document.title()}\n")

    def test_global_config_option_is_accepted(self, tmp_path: Path) -> None:
        result = CliRunner().invoke(app, ["--config", str(tmp_path / "missing.toml"), "skill"])

        assert result.exit_code == 0
        assert result.output.startswith("--DEPMESH-CELL ")
        assert "# `depmesh` Usage\n" in result.output


class TestInit:
    def test_parent_config_is_not_reused(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        parent_config = tmp_path / "depmesh.toml"
        parent_config.write_text("version = 2", encoding="utf-8")
        project = tmp_path / "project"
        project.mkdir()
        monkeypatch.chdir(project)

        result = CliRunner().invoke(app, ["-p", "automation", "init"])

        assert result.exit_code == 0
        assert (project / "depmesh.toml").is_file()
        assert parent_config.read_text(encoding="utf-8") == "version = 2"
        assert cell_records(result.stdout) == [
            {
                "type": "operation_succeeded",
                "path": str(project / "depmesh.toml"),
                "content": "Configuration created.",
            }
        ]
        assert not result.stderr

    @pytest.mark.parametrize("protocol", ["human", "llm", "automation"])
    @pytest.mark.parametrize("content", [None, b"\xff"])
    def test_template_failure_uses_shared_configuration_error(
        self, mocker: MockerFixture, tmp_path: Path, protocol: str, content: bytes | None
    ) -> None:
        fixtures = tmp_path / "fixtures"
        fixtures.mkdir()
        if content is not None:
            (fixtures / "base_config.toml").write_bytes(content)
        mocker.patch("llm_tool_cli.config.files.importlib.resources.files", return_value=tmp_path)
        config_path = tmp_path / "depmesh.toml"

        result = CliRunner().invoke(app, ["--config", str(config_path), "-p", protocol, "init"])

        assert result.exit_code == 2
        assert not config_path.exists()
        if protocol == "automation":
            assert not result.stderr
            records = cell_records(result.stdout)
            assert len(records) == 1
            record = records[0]
            assert record["type"] == "error"
            assert record["code"] == "config_template_unreadable"
            assert record["path"] == str(config_path)
            assert record["template"] == "base_config.toml"
            assert record["reason"]
            assert record["content"]
        else:
            assert not result.stdout
            separator = " = " if protocol == "human" else "="
            assert f"kind{separator}error\n" in result.stderr
            assert f"code{separator}config_template_unreadable\n" in result.stderr
            assert f"path{separator}{config_path}\n" in result.stderr
            assert f"template{separator}base_config.toml\n" in result.stderr

    @pytest.mark.parametrize("protocol", ["llm", "automation"])
    def test_success_respects_protocol(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, protocol: str) -> None:
        monkeypatch.chdir(tmp_path)

        result = CliRunner().invoke(app, ["-p", protocol, "init"])

        assert result.exit_code == 0
        assert result.stderr == ""
        assert (tmp_path / "depmesh.toml").is_file()
        if protocol == "automation":
            assert cell_records(result.stdout) == [
                {
                    "type": "operation_succeeded",
                    "path": str(tmp_path / "depmesh.toml"),
                    "content": "Configuration created.",
                }
            ]
        else:
            assert result.stdout.startswith("--DEPMESH-CELL ")
            assert "kind=operation_succeeded\n" in result.stdout
            assert "type=operation_succeeded\n" in result.stdout
            assert f"path={tmp_path / 'depmesh.toml'}\n" in result.stdout
            assert "Configuration created.\n" in result.stdout

    def test_expands_home_in_config_path(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        home_dir = tmp_path / "home"
        home_dir.mkdir()
        monkeypatch.chdir(tmp_path)
        monkeypatch.setenv("HOME", str(home_dir))

        result = CliRunner().invoke(app, ["--config", "~/custom.toml", "init"])

        assert result.exit_code == 0
        assert "kind = operation_succeeded\n" in result.stdout
        assert f"path = {home_dir / 'custom.toml'}\n" in result.stdout
        assert "Configuration created.\n" in result.stdout
        assert (home_dir / "custom.toml").is_file()

    def test_creates_default_config(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.chdir(tmp_path)

        result = CliRunner().invoke(app, ["init"])

        config_path = tmp_path / "depmesh.toml"
        assert result.exit_code == 0
        assert "kind = operation_succeeded\n" in result.output
        assert "type = operation_succeeded\n" in result.output
        assert f"path = {config_path}\n" in result.output
        assert "Configuration created.\n" in result.output
        assert 'id = "governed_by"' in config_path.read_text(encoding="utf-8")
        assert 'id = "governs"' in config_path.read_text(encoding="utf-8")

    def test_uses_global_config_path(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.chdir(tmp_path)

        result = CliRunner().invoke(app, ["--config", "custom.toml", "init"])

        assert result.exit_code == 0
        assert (tmp_path / "custom.toml").is_file()
        assert f"path = {tmp_path / 'custom.toml'}\n" in result.stdout

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
    @pytest.mark.parametrize("protocol", [None, "human", "llm", "automation"])
    def test_version_output(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, protocol: str | None) -> None:
        monkeypatch.chdir(tmp_path)
        options = [] if protocol is None else ["-p", protocol]

        result = CliRunner().invoke(app, [*options, "version"])

        assert result.exit_code == 0
        assert not result.stderr
        version = metadata.version("depmesh")
        if protocol == "automation":
            assert cell_records(result.stdout) == [{"type": "version", "version": version, "content": None}]
        elif protocol == "llm":
            assert normalize_cell_ids(result.stdout) == (
                f"--DEPMESH-CELL <id> BEGIN--\nkind=version\ntype=version\nversion={version}\n"
                "--DEPMESH-CELL <id> END--\n"
            )
        else:
            assert normalize_cell_ids(result.stdout) == (
                f"----- DEPMESH CELL <id> -----\nkind = version\ntype = version\nversion = {version}\n\n"
            )

    @pytest.mark.parametrize("content", [None, "not valid TOML"])
    def test_global_options_are_accepted(self, tmp_path: Path, content: str | None) -> None:
        config_path = tmp_path / "depmesh.toml"
        if content is not None:
            config_path.write_text(content, encoding="utf-8")

        result = CliRunner().invoke(
            app,
            ["--config", str(config_path), "--protocol", "automation", "version"],
        )

        assert result.exit_code == 0
        assert not result.stderr
        assert cell_records(result.stdout) == [
            {"type": "version", "version": metadata.version("depmesh"), "content": None}
        ]


class TestMain:
    @pytest.fixture
    def initialized_settings(self, isolated_settings: None) -> None:
        """Keep the label unset so main must initialize it."""

    def test_success(self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
        monkeypatch.setattr(sys, "argv", ["depmesh", "version"])

        with pytest.raises(SystemExit) as exit_info:
            main()

        assert exit_info.value.code == 0
        captured = capsys.readouterr()
        assert not captured.err
        assert normalize_cell_ids(captured.out) == (
            "----- DEPMESH CELL <id> -----\nkind = version\ntype = version\n"
            f"version = {metadata.version('depmesh')}\n\n"
        )

    def test_initializes_label_before_parsing(self, mocker: MockerFixture, capsys: pytest.CaptureFixture[str]) -> None:
        mocker.patch.object(sys, "argv", ["depmesh", "--protocol", "invalid", "version"])

        for _ in range(2):
            with pytest.raises(SystemExit) as caught:
                main()

            assert caught.value.code == 1
            captured = capsys.readouterr()
            assert not captured.out
            assert captured.err.startswith("--DEPMESH-CELL ")
            assert "code=invalid_arguments\n" in captured.err
