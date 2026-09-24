from __future__ import annotations

import logging
from datetime import date
from functools import lru_cache
from pathlib import Path
from types import UnionType
from typing import IO, Any, Iterator, Union, get_args, get_origin

import pandas as pd
from pydantic import BaseModel, Field, ValidationError, create_model

from .schema import ValidationDetail
from .settings import settings

logger = logging.getLogger(__name__)

_TYPE_MAP: dict[str, type] = {
    "str": str,
    "int": int,
    "float": float,
    "bool": bool,
    "date": date,
    "datetime.date": date,
}

_FIELD_CONSTRAINTS = ("ge", "le", "min_length", "max_length", "pattern", "regex")

_ERROR_TYPE_ALIASES = {
    "value_error.number.not_ge": "greater_than_equal",
    "value_error.number.not_le": "less_than_equal",
    "value_error.invalid_format": "string_pattern_mismatch",
}


def _parse_field_type(type_name: str) -> Any:
    name = str(type_name).strip()
    optional = False
    if name.startswith("Optional[") and name.endswith("]"):
        optional = True
        name = name[len("Optional[") : -1].strip()
    if name not in _TYPE_MAP:
        raise ValueError(f"Unsupported schema type: {type_name}")
    parsed = _TYPE_MAP[name]
    if optional:
        return parsed | None
    return parsed


def _field_constraints(field: Any) -> dict[str, Any]:
    constraints: dict[str, Any] = {}
    for key in _FIELD_CONSTRAINTS:
        if key not in field:
            continue
        constraints["pattern" if key == "regex" else key] = field[key]
    return constraints


@lru_cache(maxsize=1)
def load_data_models_from_settings() -> dict[str, type[BaseModel]]:
    models: dict[str, type[BaseModel]] = {}
    for model_name, fields in settings.schema.pydantic.items():
        logger.debug('Fields to be uploaded for "%s":\n%s\n', model_name, fields)
        model_fields: dict[str, Any] = {}
        for field_name, field in fields.items():
            field_type = _parse_field_type(field["type"])
            constraints = _field_constraints(field)
            model_fields[field_name] = (field_type, Field(..., **constraints))
        logger.debug('Uploaded model fields for "%s":\n%s\n', model_name, model_fields)
        models[model_name] = create_model(model_name, **model_fields)
    return models


def get_model(model_name: str | None = None) -> type[BaseModel]:
    models = load_data_models_from_settings()
    target = model_name or settings.app.data.model_name
    try:
        return models[target]
    except KeyError as exc:
        available = ", ".join(sorted(models.keys())) or "<none>"
        raise RuntimeError(
            f"Configured model {target!r} not found. Available models: {available}"
        ) from exc


def get_date_fields(model: type[BaseModel]) -> list[str]:
    names: list[str] = []
    for field_name, field_info in model.model_fields.items():
        annotation = field_info.annotation
        origin = get_origin(annotation)
        args = get_args(annotation)
        if annotation is date or (origin in (Union, UnionType) and date in args):
            names.append(field_name)
    return names


def validate_csv(
    df: pd.DataFrame, model: type[BaseModel]
) -> tuple[bool, list[ValidationDetail]]:
    working = df
    date_fields = get_date_fields(model)
    if date_fields:
        working = df.copy()
        for field in date_fields:
            if field in working.columns:
                working[field] = pd.to_datetime(working[field], errors="coerce")
                working[field] = working[field].apply(
                    lambda value: value if pd.notnull(value) else None
                )

    errors: list[ValidationDetail] = []
    for index, row in working.iterrows():
        try:
            row_dict = row.where(pd.notnull(row), None).to_dict()
            model(**row_dict)
        except ValidationError as exc:
            errors.extend(translate_errors(exc.errors(), index))
    return len(errors) > 0, errors


def iter_csv_errors(
    source: str | Path | IO[str],
    *,
    model: type[BaseModel] | None = None,
    model_name: str | None = None,
    delimiter: str = ",",
    chunksize: int | None = None,
    max_errors: int | None = None,
) -> Iterator[ValidationDetail]:
    target_model = model or get_model(model_name)
    emitted = 0
    if chunksize:
        for chunk in pd.read_csv(source, delimiter=delimiter, chunksize=chunksize):
            _, errors = validate_csv(chunk, target_model)
            for error in errors:
                yield error
                emitted += 1
                if max_errors is not None and emitted >= max_errors:
                    return
        return

    frame = pd.read_csv(source, delimiter=delimiter)
    _, errors = validate_csv(frame, target_model)
    if max_errors is not None:
        errors = errors[:max_errors]
    yield from errors


def _error_types_match(configured: str, actual: str) -> bool:
    if configured == actual:
        return True
    if _ERROR_TYPE_ALIASES.get(configured) == actual:
        return True
    if _ERROR_TYPE_ALIASES.get(actual) == configured:
        return True
    return False


def _lookup_error_message(field: str, error_type: str, fallback: str) -> str:
    try:
        error_messages = settings.schema.error_messages
    except AttributeError:
        error_messages = {}

    for error_msg in error_messages.get(field, []):
        configured_type = error_msg.get("type")
        if configured_type and _error_types_match(str(configured_type), error_type):
            return error_msg.get("message", fallback)
    return fallback


def translate_errors(errors: list[dict[str, Any]], row: Any) -> list[ValidationDetail]:
    readable_errors: list[ValidationDetail] = []
    for error in errors:
        field = str(error["loc"][0])
        error_type = error["type"]
        input_value = str(error.get("input", "N/A"))
        message = _lookup_error_message(field, error_type, error["msg"])
        readable_errors.append(
            ValidationDetail(
                row=row,
                field=field,
                message=message,
                error_type=error_type,
                input_value=input_value,
            )
        )
    return readable_errors
