# STRATA-FIT Data Validation

FastAPI service + CLI + Vantage6 algorithm to validate CSV files against the STRATA-FIT data schema (see `config/schema.yaml`). Configuration lives in `config/settings.yaml`/`config/schema.yaml`.

## Runtime modes (entrypoint)
Set `RUN_MODE` in the container (or call the commands directly):
- `RUN_MODE=api` — serve FastAPI: `uvicorn strata_fit_v6_data_validator_py.main:app --host 0.0.0.0 --port 8000`
- `RUN_MODE=cli` — run the CLI validator: `strata-fit-validate --input <file.csv> [--output out.json] [--delimiter ,|;|\t|...]`
- `RUN_MODE=algorithm` (default) — start the Vantage6 wrapper; exposes `validate_data` for federated runs. Errors returned to callers are coarse (counts only, no tracebacks).

Example docker run:
```bash
docker run --rm -p 8000:8000 \
  -e RUN_MODE=api \
  -v $(pwd)/config:/app/config \
  ghcr.io/mdw-nl/strata-fit-data-val:latest
```

## Local development
- Python `>=3.10,<3.13`.
- Install in editable mode: `pip install -e .`
- Run API: `RUN_MODE=api ./entrypoint.sh` or `uvicorn strata_fit_v6_data_validator_py.main:app --reload`
- Run CLI: `strata-fit-validate --input data/correct.csv`

## Datavalgen plugin mode
This package also exposes STRATA-FIT models as `datavalgen` plugins (similar to
`datavalgen-model-beach`), without replacing the existing API/CLI/algorithm flow.

After installing both packages in the same environment:
```bash
pip install -e .
pip install datavalgen
datavalgen validate --list
```

You should see:
- `strata_fit_patient_data`
- `strata_fit_default` (alias to `settings.app.data.model_name`)

Then validate a CSV with:
```bash
datavalgen validate -m strata_fit_patient_data -d /path/to/data.csv
```

For synthetic data generation, datavalgen uses `factories` (not `models`):
```bash
datavalgen generate --list
datavalgen generate -f strata_fit_patient_data -n 10 --show-df
```

Round-trip `generate & validate` check:
```bash
datavalgen generate -f strata_fit_patient_data -n 30 -o /tmp/strata_generated.csv --force
datavalgen validate -m strata_fit_patient_data -d /tmp/strata_generated.csv
```

## Configuration hints
`config/settings.yaml` controls chunk size, model name, and error cap:
```yaml
app:
  data:
    chunksize: 10
    model_name: PatientData
  errors:
    max_to_collect: 1000
```
Update the YAML files, then restart the process; no code changes needed.

## API endpoints (when in `api` mode)
- `/validate` — upload CSV for validation
- `/settings` — current settings YAML
- `/schema` — current schema YAML

## Diagrams
![app](docs/app.png)
