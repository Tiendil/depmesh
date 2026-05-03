from __future__ import annotations

import subprocess

from depmesh.core import warnings
from depmesh.discovery.artifacts import EvaluationContext
from depmesh.discovery.paths import normalize_path
from depmesh.discovery.sources.base import ArtifactSourceBase
from depmesh.discovery.sources.entities import CommandSourceConfig
from depmesh.domain.entities import ArtifactId


class CommandSource(ArtifactSourceBase):
    __slots__ = ("config",)

    def __init__(self, config: CommandSourceConfig) -> None:
        self.config = config

    def evaluate(self, context: EvaluationContext) -> list[ArtifactId]:
        command = self.config.command.substitute(context.captures)

        completed = subprocess.run(  # noqa: S602
            command,
            cwd=context.root,
            shell=True,
            text=True,
            capture_output=True,
            check=False,
        )

        if completed.stderr.strip():
            warnings.add(f"relation `{context.relation_id}`: command stderr: {completed.stderr.strip()}")

        if completed.returncode != 0:
            warnings.add(f"relation `{context.relation_id}`: command exited with status {completed.returncode}: {command}")

        return [
            ArtifactId(
                normalize_path(
                    line.strip(),
                    context.root,
                    cwd=context.root,
                )
            )
            for line in completed.stdout.splitlines()
            if line.strip()
        ]


__all__ = ["CommandSource", "CommandSourceConfig"]
