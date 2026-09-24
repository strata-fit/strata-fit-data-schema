from __future__ import annotations

import io
import json
import logging

import pandas as pd
from fastapi import File, HTTPException, UploadFile
from fastapi import FastAPI, Response
from fastapi.responses import StreamingResponse

from .logic import get_model, iter_csv_errors, load_data_models_from_settings
from .logs import setup_logging
from .schema import PandasDelimeter
from .settings import resolve_config_file, settings

logger = logging.getLogger(__name__)
setup_logging(level=settings.logging.level)

app = FastAPI(
    title=settings.openapi.title,
    description=settings.openapi.description,
    version=settings.openapi.version,
    contact=settings.openapi.contact,
)


def _yaml_response(path_value: str, missing_message: str) -> Response:
    path = resolve_config_file(path_value)
    if path.is_file():
        logger.info("Config file retrieved: %s", path)
        return Response(content=path.read_text(encoding="utf-8"), media_type="application/x-yaml")
    logger.warning("Config file not found at: %s", path)
    return Response(content=missing_message, status_code=404)


@app.get("/settings", tags=["Settings"])
def get_settings():
    return _yaml_response(settings.openapi.settings_path, "Settings file not found.")


@app.get("/schema", tags=["Settings"])
def get_schema():
    return _yaml_response(settings.openapi.schema_path, "Data Schema file not found.")


@app.post("/validate", tags=["Validation"])
async def validate(
    file: UploadFile = File(...),
    delimeter: PandasDelimeter = PandasDelimeter.COMMA,
):
    filename = file.filename or ""
    if not filename.lower().endswith(".csv"):
        logger.error("Rejected non-CSV upload: %s", filename)
        raise HTTPException(status_code=400, detail="Please upload a CSV file.")
    try:
        raw = await file.read()
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        logger.exception("CSV decoding failed")
        raise HTTPException(status_code=400, detail=f"File must be UTF-8 encoded: {exc}") from exc

    try:
        pd.read_csv(io.StringIO(text), delimiter=delimeter.value, nrows=0)
    except Exception as exc:
        logger.exception("CSV header parse failed")
        raise HTTPException(status_code=400, detail=f"CSV parse error: {exc}") from exc

    model = get_model()
    load_data_models_from_settings()
    logger.info("Data models loaded: %s", ", ".join(load_data_models_from_settings()))
    chunksize = settings.app.data.chunksize
    max_errors_to_report = settings.app.errors.max_to_collect or None

    def stream_array():
        yield "["
        first = True
        try:
            for detail in iter_csv_errors(
                io.StringIO(text),
                model=model,
                delimiter=delimeter.value,
                chunksize=chunksize,
                max_errors=max_errors_to_report,
            ):
                if not first:
                    yield ","
                yield detail.model_dump_json()
                first = False
        except Exception as exc:
            err_obj = {
                "error": "Validation stream failed",
                "detail": str(exc),
            }
            if not first:
                yield ","
            yield json.dumps(err_obj)
        finally:
            yield "]"

    return StreamingResponse(stream_array(), media_type="application/json")
