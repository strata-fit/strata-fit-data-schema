from __future__ import annotations

import os
from pathlib import Path

from dynaconf import Dynaconf

_PACKAGE_DIR = Path(__file__).resolve().parent
_REPO_CONFIG_DIR = _PACKAGE_DIR.parent / "config"


def get_config_dir() -> Path:
    env_path = os.getenv("CONFIG_PATH")
    if env_path:
        return Path(env_path)
    if (_REPO_CONFIG_DIR / "settings.yaml").is_file():
        return _REPO_CONFIG_DIR
    cwd_config = Path.cwd() / "config"
    if (cwd_config / "settings.yaml").is_file():
        return cwd_config
    bundled = _PACKAGE_DIR / "config"
    if (bundled / "settings.yaml").is_file():
        return bundled
    return _REPO_CONFIG_DIR


def resolve_config_file(path_value: str) -> Path:
    path = Path(path_value)
    if path.is_file():
        return path
    config_dir = get_config_dir()
    for candidate in (config_dir / path.name, config_dir / path, Path.cwd() / path):
        if candidate.is_file():
            return candidate
    return path


settings = Dynaconf(
    envvar_prefix="STRATA_FIT_VAL",
    settings_files=[
        str(get_config_dir() / "settings.yaml"),
        str(get_config_dir() / "schema.yaml"),
    ],
    merge_enabled=True,
)
