from __future__ import annotations

from pathlib import Path


def resolve_project_path(value: str, root: Path, *, allow_absolute: bool = True) -> Path | None:
    path = Path(value)

    if path.is_absolute():
        if not allow_absolute:
            return None
        return path.resolve()

    resolved = (root / path).resolve()

    if not resolved.is_relative_to(root.resolve()):
        return None

    return resolved


def normalize_path(value: str, root: Path, *, cwd: Path | None = None) -> str:
    path = Path(value)

    if path.is_absolute():
        resolved = path.resolve()
    else:
        base = cwd or root
        resolved = (base / path).resolve()

    root = root.resolve()

    if resolved == root:
        return "."

    if resolved.is_relative_to(root):
        return "./" + resolved.relative_to(root).as_posix()

    return resolved.as_posix()


def normalize_existing_path(path: Path, root: Path) -> str:
    root = root.resolve()
    resolved = path.resolve()

    if resolved.is_relative_to(root):
        return "./" + resolved.relative_to(root).as_posix()

    return resolved.as_posix()
