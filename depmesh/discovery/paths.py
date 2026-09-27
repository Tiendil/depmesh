from __future__ import annotations

from pathlib import Path

from llm_tool_cli.core.result import Ok, Result, unwrap_to_error
from llm_tool_cli.paths import (
    ProjectPathId,
    ProjectRootPath,
    ResolvedProjectPath,
    normalize_project_path_id,
    resolve_inside_project,
    resolve_project_root,
    resolve_root_anchored_path,
)
from llm_tool_cli.paths.errors import InvalidProjectPath

from depmesh.domain.entities import PathInput, UntrustedPath

PROJECT_ROOT_PREFIX = "@/"


def _canonical_from_resolved(resolved: ResolvedProjectPath, root: ProjectRootPath) -> ProjectPathId:
    return ProjectPathId(PROJECT_ROOT_PREFIX + resolved.relative_to(Path(root)).as_posix())


@unwrap_to_error
def resolve_project_path(
    value: str, root: PathInput, *, allow_absolute: bool = True
) -> Result[ResolvedProjectPath | None]:
    project_root = resolve_project_root(root).unwrap()

    if value.startswith("@"):
        if not value.startswith(PROJECT_ROOT_PREFIX):
            return Ok(None)
        resolved = resolve_root_anchored_path(value, project_root)
    else:
        path = Path(value)
        if path.is_absolute() and not allow_absolute:
            return Ok(None)
        resolved = resolve_inside_project(path if path.is_absolute() else project_root / path, project_root)

    if resolved.is_err(InvalidProjectPath):
        return Ok(None)
    return resolved


@unwrap_to_error
def normalize_path(value: str, root: PathInput, *, cwd: PathInput | None = None) -> Result[ProjectPathId]:
    project_root = resolve_project_root(root).unwrap()

    if value.startswith("@"):
        return normalize_project_path_id(value)

    path = Path(value)
    candidate = path if path.is_absolute() else (cwd or root) / path
    resolved = resolve_inside_project(candidate, project_root).unwrap()
    return Ok(_canonical_from_resolved(resolved, project_root))


def normalize_path_pattern(value: str, root: PathInput, *, cwd: PathInput | None = None) -> Result[str | None]:
    result = normalize_path(value, root, cwd=cwd)
    if result.is_err(InvalidProjectPath):
        return Ok(None)
    return result


@unwrap_to_error
def normalize_existing_path(path: UntrustedPath, root: PathInput) -> Result[ProjectPathId]:
    project_root = resolve_project_root(root).unwrap()
    resolved = resolve_inside_project(path, project_root).unwrap()
    return Ok(_canonical_from_resolved(resolved, project_root))
