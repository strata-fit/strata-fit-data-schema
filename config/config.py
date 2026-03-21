import os
from pathlib import Path

from dynaconf import Dynaconf

DEFAULT_CONFIG_PATH = Path(__file__).resolve().parent
config_path = Path(os.getenv("CONFIG_PATH", str(DEFAULT_CONFIG_PATH)))

settings = Dynaconf(
    envvar_prefix="STRATA_FIT_VAL",
    settings_files=[
        str(config_path / "settings.yaml"),
        str(config_path / "schema.yaml"),
    ],
    merge_enabled=True,
)
