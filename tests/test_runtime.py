from __future__ import annotations

import json
import os

from pathlib import Path

import pytest

from strata_fit_v6_data_validator_py import validate_data as exported_validate_data
from strata_fit_v6_data_validator_py.runtime import (
    RunContext,
    decode_env_value,
    dispatch_run_context,
    main,
)


TEST_DATA_DIR = Path(__file__).parent / "fixtures"


class _FakeEntryPoint:
    def __init__(self, name: str, func, dist_name: str = "strata_fit_v6_data_validator_py") -> None:
        self.name = name
        self._func = func
        self.dist = type("Dist", (), {"name": dist_name})()

    def load(self):
        return self._func


def test_run_context_from_path(tmp_path: Path) -> None:
    context_path = tmp_path / "run_context.json"
    context_path.write_text(
        json.dumps(
            {
                "entrypoint": {"name": "validate_data"},
                "arguments": {"named": {"model_name": "PatientData"}},
                "inputs": [{"uri": str(TEST_DATA_DIR / "valid.csv")}],
                "outputs": [{"uri": str(tmp_path / "result.json")}],
            }
        ),
        encoding="utf-8",
    )
    context = RunContext.from_path(context_path)
    assert context.entrypoint_name() == "validate_data"
    assert context.named_args() == {"model_name": "PatientData"}
    assert context.input_uris() == [TEST_DATA_DIR / "valid.csv"]


def test_decode_env_value_passthrough() -> None:
    assert decode_env_value("/tmp/example.json") == "/tmp/example.json"


def test_dispatch_run_context_writes_output(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    context_path = tmp_path / "run_context.json"
    output_path = tmp_path / "result.json"
    context_path.write_text(
        json.dumps(
            {
                "entrypoint": {"name": "validate_data"},
                "arguments": {"named": {}},
                "inputs": [{"uri": str(TEST_DATA_DIR / "valid.csv")}],
                "outputs": [{"uri": str(output_path)}],
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("RUN_CONTEXT_FILE", str(context_path))
    monkeypatch.setattr(
        "strata_fit_v6_data_validator_py.runtime.entry_points",
        lambda group: [_FakeEntryPoint("validate_data", exported_validate_data)],
    )

    result = dispatch_run_context()
    assert result["validation_passed"] is True
    assert json.loads(output_path.read_text(encoding="utf-8")) == result


def test_main_requires_run_context(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("RUN_CONTEXT_FILE", raising=False)
    with pytest.raises(RuntimeError, match="RUN_CONTEXT_FILE"):
        main()
