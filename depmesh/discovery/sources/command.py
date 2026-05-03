from __future__ import annotations

import subprocess
from typing import Literal

from depmesh.core import warnings
from depmesh.discovery.artifacts import CaptureName, EvaluationContext, TemplateText
from depmesh.discovery.paths import normalize_path
from depmesh.discovery.sources.base import ArtifactSourceBase
from depmesh.domain.entities import ArtifactId


class CommandSource(ArtifactSourceBase):
    type: Literal["command"]
    command: TemplateText

    def variables(self) -> set[CaptureName]:
        return set(self.command.variables)

    def evaluate(self, context: EvaluationContext) -> list[ArtifactId]:
        command = self.command.substitute(context.captures)

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
