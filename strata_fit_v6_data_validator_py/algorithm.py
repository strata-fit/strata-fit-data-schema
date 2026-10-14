from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import pandas as pd

from .io import write_output
from .logic import get_model, iter_csv_errors, validate_csv
from .runtime import run_context
from .schema import ValidationDetail

logger = logging.getLogger(__name__)


def validate_dataframe(df: pd.DataFrame, model_name: str | None = None) -> dict[str, Any]:
    try:
        _, errors = validate_csv(df.copy(), get_model(model_name))
        total_rows = len(df.index)
        total_errors = len(errors)
        return {
            "total_rows": total_rows,
            "total_errors": total_errors,
            "error_rate_per_row": (total_errors / total_rows) if total_rows else 0,
            "validation_passed": total_errors == 0,
        }
    except Exception as exc:
        logger.error("Validation failed: %s", exc)
        total_rows = len(df.index) if hasattr(df, "index") else 0
        return {
            "total_rows": total_rows,
            "total_errors": None,
            "error_rate_per_row": None,
            "validation_passed": False,
            "error": "Validation failed; see server logs for details.",
        }


def validate_file_errors(
    dataset_path: str | Path,
    *,
    model_name: str | None = None,
    delimiter: str = ",",
) -> list[ValidationDetail]:
    return list(
        iter_csv_errors(
            dataset_path,
            model_name=model_name,
            delimiter=delimiter,
        )
    )


@run_context(input_uris="dataset_path", output_uris="output_path", named_arguments=("model_name",))
def validate_data(
    *,
    dataset_path: Path,
    output_path: Path | None = None,
    model_name: str | None = None,
) -> dict[str, Any]:
    frame = pd.read_csv(dataset_path)
    payload = validate_dataframe(frame, model_name=model_name)
    write_output(output_path, payload)
    return payload
