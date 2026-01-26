"""Vantage6 algorithm entrypoints."""

from typing import Any, Dict, Optional

import pandas as pd
from vantage6.algorithm.tools.decorators import data

from config.config import settings
from strata_fit_v6_data_validator_py.logic import (
    load_data_models_from_settings,
    validate_csv,
)


@data(1)
def validate_data(
    df: pd.DataFrame,
    model_name: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Validate a dataframe against the configured schema and summarize results.
    Designed to be safe for V6: no tracebacks or detailed errors are returned.

    Parameters
    ----------
    df : pd.DataFrame
        Local dataframe provided by Vantage6.
    model_name : str, optional
        Override the model name; defaults to settings.app.data.model_name.
    """
    try:
        models = load_data_models_from_settings()
        target_model = model_name or settings.app.data.model_name
        model = models[target_model]

        _, errors = validate_csv(df, model)
        total_rows = len(df.index)
        total_errors = len(errors)

        return {
            "total_rows": total_rows,
            "total_errors": total_errors,
            "error_rate_per_row": (total_errors / total_rows) if total_rows else 0,
            "validation_passed": total_errors == 0,
        }
    except Exception:
        # Avoid leaking stack traces to the caller; surface only coarse metadata.
        total_rows = len(df.index) if hasattr(df, "index") else 0
        return {
            "total_rows": total_rows,
            "total_errors": None,
            "error_rate_per_row": None,
            "validation_passed": False,
            "error": "Validation failed; see server logs for details.",
        }
