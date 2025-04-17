from functools import lru_cache
from fastapi import (
    FastAPI, Response, UploadFile,
    File, HTTPException, Depends,
)
from fastapi.responses import StreamingResponse
import pandas as pd
import numpy as np
import io
import json
import os
import logging

from config.config import settings
from api.schema import  PandasDelimeter
from api.logic import (
    validate_csv,
    load_data_models_from_settings
)
from api.logs import setup_logging
from api.utils import pretty_format_model

# Setup the logging
logger = logging.getLogger(__name__)
setup_logging(level=settings.logging.level)

# Initialize the Validator App
app = FastAPI(
    title=settings.openapi.title,
    description=settings.openapi.description,
    version=settings.openapi.version,
    contact=settings.openapi.contact
)

@app.get("/settings", tags=["Settings"])
def get_settings():
    settings_file_path = settings.openapi.settings_path
    if os.path.exists(settings_file_path):
        logger.info(f"Settings file retrieved: {settings_file_path}")
        with open(settings_file_path, 'r') as settings_file:
            return Response(content=settings_file.read(), media_type="application/x-yaml")
    else:
        logger.warning(f"Settings file not found at: {settings_file_path}")
        return Response(content="Settings file not found.", status_code=404)
    
@app.get("/schema", tags=["Settings"])
def get_schema():
    schema_file_path = settings.openapi.schema_path
    if os.path.exists(schema_file_path):
        logger.info(f"Schema file retrieved: {schema_file_path}")
        with open(schema_file_path, 'r') as schema_file:
            return Response(content=schema_file.read(), media_type="application/x-yaml")
    else:
        logger.warning(f"Schema file not found at: {schema_file_path}")
        return Response(content="Data Schema file not found.", status_code=404)

@lru_cache
def get_models():
    models = load_data_models_from_settings()
    pretty_models = "\n".join(
        pretty_format_model(model_name, model) for model_name, model in models.items()
    )
    logger.info(f"Data models loaded:{pretty_models}")
    return models

@app.post("/validate", tags=["Validation"])
async def validate(
    file: UploadFile = File(...),
    delimeter: PandasDelimeter = PandasDelimeter.COMMA,
    models: dict = Depends(get_models),
):
    # 1) Basic file checks
    if not file.filename.lower().endswith(".csv"):
        logger.error(f"Rejected non-CSV upload: {file.filename}")
        raise HTTPException(status_code=400, detail="Please upload a CSV file.")
    # 2) Read bytes & decode
    try:
        raw = await file.read()
        text = raw.decode("utf-8")
    except UnicodeDecodeError as e:
        logger.exception("CSV decoding failed")
        raise HTTPException(status_code=400, detail=f"File must be UTF-8 encoded: {e}")

    # 3) Quick header‑only parse to catch delimiters / malformed CSV
    try:
        pd.read_csv(io.StringIO(text), delimiter=delimeter.value, nrows=0)
    except Exception as e:
        logger.exception("CSV header parse failed")
        raise HTTPException(status_code=400, detail=f"CSV parse error: {e}")

    model = models[settings.app.data.model_name]
    chunksize = settings.app.data.chunksize
    max_errors_to_report = (
        settings.app.errors.max_to_collect
        if settings.app.errors.max_to_collect
        else np.inf
    )

    def stream_array():
        yield "["  
        first = True
        buf = io.StringIO(text)
        error_count = 0
        try:
            for chunk in pd.read_csv(
                buf,
                delimiter=delimeter.value,
                chunksize=chunksize
            ):
                _, errs = validate_csv(chunk, model)
                for e in errs:
                    if error_count >= max_errors_to_report:
                        break
                    if not first:
                        yield ","
                    yield e.json()
                    first = False
                    error_count += 1
                if error_count >= max_errors_to_report:
                    break
        except Exception as e:
            # If something goes wrong mid‑stream, emit a terminal error object
            err_obj = {
                "error": "Validation stream failed",
                "detail": str(e)
            }
            if not first:
                yield ","
            yield json.dumps(err_obj)
        finally:
            yield "]"

    return StreamingResponse(
        stream_array(),
        media_type="application/json"
    )