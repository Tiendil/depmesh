from __future__ import annotations

from collections.abc import Mapping

from llm_tool_cli.core.errors import EnvironmentErrors
from llm_tool_cli.core.result import Err, Ok, Result, unwrap_to_error

from depmesh.discovery import errors
from depmesh.discovery.artifacts import EvaluationContext
from depmesh.discovery.entities import DependencyRule, QueryResult
from depmesh.discovery.paths import normalize_path
from depmesh.domain.entities import ArtifactId, Dependency, ProjectRootPath, Relation, RelationId, UntrustedPath


@unwrap_to_error
def query_dependencies(
    root: ProjectRootPath,
    relations_by_id: Mapping[RelationId, Relation],
    rules: tuple[DependencyRule, ...],
    artifact: ArtifactId,
    *,
    relation_ids: set[RelationId],
    cwd: UntrustedPath | None = None,
) -> Result[QueryResult, EnvironmentErrors]:
    artifact = ArtifactId(
        normalize_path(
            str(artifact),
            root,
            cwd=cwd,
        ).unwrap()
    )
    dependencies: set[Dependency] = set()

    for rule in rules:
        if rule.relation not in relation_ids:
            continue

        captures = rule.input_predicate.match(artifact, root)
        if captures is None:
            continue

        relation = relations_by_id.get(rule.relation)
        if relation is None:
            continue

        for dependency in _evaluate_rule_dependencies(root, rule, captures).unwrap():
            dependencies.add(Dependency(relation=relation.id, dependency=dependency))

    return Ok(QueryResult(dependencies=tuple(sorted(dependencies, key=lambda item: (item.relation, item.dependency)))))


@unwrap_to_error
def normalize_input_artifacts(
    root: ProjectRootPath,
    artifacts: list[ArtifactId],
    *,
    cwd: UntrustedPath | None = None,
) -> Result[list[ArtifactId], EnvironmentErrors]:
    return Ok(
        sorted(
            {
                ArtifactId(
                    normalize_path(
                        str(artifact),
                        root,
                        cwd=cwd,
                    ).unwrap()
                )
                for artifact in artifacts
            }
        )
    )


def selected_relation_ids(
    relations_by_id: Mapping[RelationId, Relation],
    relation_filters: list[RelationId] | None,
) -> Result[set[RelationId], EnvironmentErrors]:
    if not relation_filters:
        return Ok(set(relations_by_id))

    selected: set[RelationId] = set()

    for relation_filter in relation_filters:
        relation = relations_by_id.get(relation_filter)
        if relation is not None:
            selected.add(relation.id)
            continue

        return Err([errors.UnknownRelationFilter(relation=relation_filter)])

    return Ok(selected)


@unwrap_to_error
def _evaluate_rule_dependencies(
    root: ProjectRootPath,
    rule: DependencyRule,
    captures: dict[str, str],
) -> Result[list[ArtifactId], EnvironmentErrors]:
    dependencies: set[ArtifactId] = set()
    context = EvaluationContext(root=root, relation_id=rule.relation, captures=captures)

    dependencies.update(rule.output_source.evaluate(context).unwrap())

    return Ok(sorted(dependencies))
