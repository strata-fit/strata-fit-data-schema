# STRATA-FIT Data Validation

Standalone schema validator for STRATA-FIT datasets. This repo now supports three execution modes on top of the same pure validation logic:

- FastAPI service
- local CLI validation
- federated `run_context` execution with the stable method name `validate_data`

The runtime no longer depends on `vantage6-algorithm-tools` or the Harbor wrapper base image.

## Runtime model

The Docker image (and `./entrypoint.sh` locally) dispatches on `RUN_MODE`:

```bash
RUN_MODE=api ./entrypoint.sh                                   # uvicorn FastAPI service
RUN_MODE=cli ./entrypoint.sh --input tests/fixtures/valid.csv  # CLI validator
RUN_MODE=algorithm ./entrypoint.sh                             # default: run_context dispatch
```

`algorithm` mode (the default when `RUN_MODE` is unset) runs `python -m strata_fit_v6_data_validator_py.container`, which expects `RUN_CONTEXT_FILE` and resolves the `validate_data` entrypoint from the package metadata.

## Local development

- Python `>=3.11`
- install: `pip install -e .[dev]`
- API: `uvicorn strata_fit_v6_data_validator_py.main:app --reload`
- CLI: `strata-fit-validate --input tests/fixtures/valid.csv`
- local runner: `python tests/mock_client.py`

## Federated runtime contract

Stable task method:

- `validate_data`

Expected behavior:

- input: one mounted CSV dataset
- output: a JSON summary with:
  - `total_rows`
  - `total_errors`
  - `error_rate_per_row`
  - `validation_passed`

Validation failures stay coarse on purpose so task callers do not receive internal stack traces.

## Datavalgen plugin mode

This package also exposes STRATA-FIT models as `datavalgen` plugins.

```bash
pip install -e .
pip install datavalgen
datavalgen validate --list
datavalgen generate --list
```

Expected plugin names:

- `strata_fit_patient_data`
- `strata_fit_default`

## Configuration

The runtime reads:

- [config/settings.yaml](config/settings.yaml)
- [config/schema.yaml](config/schema.yaml)

Update those YAML files to change the active model, chunking, or schema constraints.

## Verification

Primary checks:

- `pytest`
- local `RUN_CONTEXT_FILE` smoke through `tests/test_runtime.py`
- package-root imports of:
  - `strata_fit_v6_data_validator_py`
  - `strata_fit_v6_data_validator_py.logic`
  - `strata_fit_v6_data_validator_py.schema`

## Diagrams

![app](docs/app.png)
