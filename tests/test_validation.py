from __future__ import annotations

from pathlib import Path

import pandas as pd

from strata_fit_v6_data_validator_py.algorithm import (
    validate_dataframe,
    validate_file_errors,
)


TEST_DATA_DIR = Path(__file__).parent / "fixtures"


def test_validate_dataframe_accepts_valid_rows() -> None:
    frame = pd.read_csv(TEST_DATA_DIR / "valid.csv")
    result = validate_dataframe(frame)
    assert result == {
        "total_rows": 2,
        "total_errors": 0,
        "error_rate_per_row": 0,
        "validation_passed": True,
    }


def test_validate_dataframe_reports_invalid_rows() -> None:
    frame = pd.read_csv(TEST_DATA_DIR / "invalid.csv")
    result = validate_dataframe(frame)
    assert result["total_rows"] == 1
    assert result["total_errors"] == 2
    assert result["validation_passed"] is False


def test_validate_file_errors_returns_detail_objects() -> None:
    errors = validate_file_errors(TEST_DATA_DIR / "invalid.csv")
    assert len(errors) == 2
    assert {error.field for error in errors} == {"pat_ID", "Age_diagnosis"}
