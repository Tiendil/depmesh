from __future__ import annotations

from pathlib import Path

from depmesh.discovery.entities import compile_dependency_rule
from depmesh.workspace.entities import Config, Workspace

CONFIG_FILE_NAME = "depmesh.toml"


def construct_workspace(config: Config, *, root: Path) -> Workspace:
    return Workspace(
        root=root,
        relations=tuple(relation.to_relation() for relation in config.relations),
        rules=tuple(compile_dependency_rule(rule) for rule in config.rules),
    )
