from __future__ import annotations

from pathlib import Path
from typing import Any

import pydantic
import tomli

from depmesh.discovery.entities import compile_dependency_rule
from depmesh.workspace import errors
from depmesh.workspace.entities import Config, Workspace

CONFIG_FILE_NAME = "depmesh.toml"


def discover_config(cwd: Path | None = None) -> Path | None:
    current = (cwd or Path.cwd()).resolve()

    for directory in (current, *current.parents):
        candidate = directory / CONFIG_FILE_NAME
        if candidate.is_file():
            return candidate

    return None


def load_config(path: Path | None = None, *, cwd: Path | None = None) -> Workspace:
    config_path = _resolve_config_path(path, cwd=cwd)

    try:
        with config_path.open("rb") as config_file:
            raw = tomli.load(config_file)
    except OSError as error:
        raise errors.ConfigUnreadable(config_path, error) from error
    except tomli.TOMLDecodeError as error:
        raise errors.ConfigInvalid(f"invalid TOML: {error}", path=config_path) from error

    config = parse_config(raw, config_path=config_path)

    return Workspace(
        root=config_path.parent,
        relations=tuple(relation.to_relation() for relation in config.relations),
        rules=tuple(compile_dependency_rule(rule) for rule in config.rules),
    )


def parse_config(raw: dict[str, Any], *, config_path: Path) -> Config:
    try:
        return Config.model_validate(raw)
    except pydantic.ValidationError as error:
        raise errors.ConfigInvalid(
            "invalid configuration", path=config_path, details={"validation": str(error)}
        ) from error
    except ValueError as error:
        raise errors.ConfigInvalid(str(error), path=config_path) from error


def _resolve_config_path(path: Path | None, *, cwd: Path | None = None) -> Path:
    if path is None:
        discovered_path = discover_config(cwd=cwd)

        if discovered_path is None:
            raise errors.ConfigNotFound((cwd or Path.cwd()).resolve())

        return discovered_path

    if path.is_absolute():
        return path.resolve()

    return ((cwd or Path.cwd()) / path).resolve()
