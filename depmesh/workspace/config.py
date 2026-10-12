from __future__ import annotations

from depmesh.discovery.entities import compile_dependency_rule
from depmesh.workspace.entities import Config, Workspace


def construct_workspace(config: Config) -> Workspace:
    return Workspace(
        relations=tuple(relation.to_relation() for relation in config.relations),
        rules=tuple(compile_dependency_rule(rule) for rule in config.rules),
    )
