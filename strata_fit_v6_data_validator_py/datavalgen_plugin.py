"""Datavalgen plugin entrypoints for STRATA-FIT schema models."""

from functools import lru_cache

from pydantic import BaseModel

from config.config import settings
from strata_fit_v6_data_validator_py.logic import load_data_models_from_settings


@lru_cache(maxsize=1)
def _models() -> dict[str, type[BaseModel]]:
    return load_data_models_from_settings()


def _get_model(model_name: str) -> type[BaseModel]:
    models = _models()
    if model_name not in models:
        available = ", ".join(sorted(models.keys()))
        raise RuntimeError(
            f"Configured model {model_name!r} not found. Available models: {available}"
        )
    return models[model_name]


# Stable plugin name for datavalgen entrypoints.
PatientData = _get_model("PatientData")

# Optional alias that tracks settings.app.data.model_name.
DefaultModel = _get_model(settings.app.data.model_name)

