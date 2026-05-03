from __future__ import annotations

from collections.abc import Mapping

from depmesh.discovery import errors
from depmesh.discovery.entities import DependencyRule, QueryResult
from depmesh.discovery.paths import normalize_path
from depmesh.discovery.sources import EvaluationContext, ListSource
from depmesh.domain.entities import ArtifactId, Dependency, ProjectRootPath, Relation, RelationId, UntrustedPath


def query_dependencies(
    root: ProjectRootPath,
    relations_by_id: Mapping[RelationId, Relation],
    rules: tuple[DependencyRule, ...],
    artifact: ArtifactId,
    *,
    relation_ids: set[RelationId],
    cwd: UntrustedPath | None = None,
) -> QueryResult:
    artifact = ArtifactId(
        normalize_path(
            str(artifact),
            root,
            cwd=cwd,
        )
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

        for dependency in _evaluate_rule_dependencies(root, rule, captures):
            dependencies.add(Dependency(relation=relation.id, dependency=dependency))

    return QueryResult(dependencies=tuple(sorted(dependencies, key=lambda item: (item.relation, item.dependency))))


def normalize_input_artifacts(
    root: ProjectRootPath,
    artifacts: list[ArtifactId],
    *,
    cwd: UntrustedPath | None = None,
) -> list[ArtifactId]:
    input_source = ListSource(
        type="list",
        artifacts=tuple(str(artifact) for artifact in artifacts),
    )
    input_context = EvaluationContext(
        root=root,
        relation_id=RelationId(""),
        captures={},
        cwd=cwd,
    )
    return input_source.evaluate(input_context)


def selected_relation_ids(
    relations_by_id: Mapping[RelationId, Relation],
    relation_filters: list[RelationId] | None,
) -> set[RelationId]:
    if not relation_filters:
        return set(relations_by_id)

    selected: set[RelationId] = set()

    for relation_filter in relation_filters:
        relation = relations_by_id.get(relation_filter)
        if relation is not None:
            selected.add(relation.id)
            continue

        raise errors.UnknownRelationFilter(relation_filter)

    return selected


def _evaluate_rule_dependencies(
    root: ProjectRootPath,
    rule: DependencyRule,
    captures: dict[str, str],
) -> list[ArtifactId]:
    dependencies: set[ArtifactId] = set()
    context = EvaluationContext(root=root, relation_id=rule.relation, captures=captures)

    dependencies.update(rule.output_source.evaluate(context))

    return sorted(dependencies)
