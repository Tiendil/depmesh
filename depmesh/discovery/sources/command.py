from __future__ import annotations

import subprocess  # noqa: S404

from llm_tool_cli.core.result import Err, Ok, Result, unwrap_to_error
from llm_tool_cli.output import output
from llm_tool_cli.paths import normalize_path
from llm_tool_cli.protocol.logic_cells.warning import WarningCell

from depmesh.discovery import errors
from depmesh.discovery.artifacts import EvaluationContext
from depmesh.discovery.sources.base import ArtifactSourceBase
from depmesh.discovery.sources.entities import CommandSourceConfig
from depmesh.domain.entities import ArtifactId


class CommandSource(ArtifactSourceBase):
    __slots__ = ("config",)

    def __init__(self, config: CommandSourceConfig) -> None:
        self.config = config

    @unwrap_to_error
    def evaluate(self, context: EvaluationContext) -> Result[list[ArtifactId]]:
        command = self.config.command.substitute(context.captures)

        try:
            completed = subprocess.run(
                command,
                cwd=context.root,
                shell=True,  # noqa: S602
                text=True,
                capture_output=True,
                check=False,
            )
        except (OSError, UnicodeDecodeError) as error:
            return Err(
                [
                    errors.CommandFailed(relation=context.relation_id, command=command, reason=str(error)).with_cause(
                        error
                    )
                ]
            )

        if completed.stderr.strip():
            output.get().emit(
                [WarningCell(message=f"relation `{context.relation_id}`: command stderr: {completed.stderr.strip()}")]
            ).unwrap()

        if completed.returncode != 0:
            output.get().emit(
                [
                    WarningCell(
                        message=f"relation `{context.relation_id}`: "
                        f"command exited with status {completed.returncode}: {command}"
                    )
                ]
            ).unwrap()

        return Ok(
            [
                ArtifactId(
                    normalize_path(
                        line.strip(),
                        context.root,
                        cwd=context.root,
                    ).unwrap()
                )
                for line in completed.stdout.splitlines()
                if line.strip()
            ]
        )


__all__ = ["CommandSource", "CommandSourceConfig"]
