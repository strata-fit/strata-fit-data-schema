import logging
import pandas as pd
import numpy as np
from datetime import date
from pydantic import BaseModel, Field, create_model, ValidationError
from typing import Optional # needed for Optional schema fields, DO NOT REMOVE

from .schema import ValidationDetail
from config.config import settings

logger = logging.getLogger(__name__)

def load_data_models_from_settings():
    models = {}
    for model_name, fields in settings.schema.pydantic.items():
        logger.debug(f'Fields to be uploaded for "{model_name}":\n{fields}\n')
        model_fields = {}
        for field_name, field in fields.items():
            field_type = eval(field["type"])
            constraints = {}
            # Check and add constraints if they exist
            if "ge" in field:
                constraints["ge"] = field["ge"]
            if "le" in field:
                constraints["le"] = field["le"]
            if "min_length" in field:
                constraints["min_length"] = field["min_length"]
            if "max_length" in field:
                constraints["max_length"] = field["max_length"]
            if "regex" in field:
                constraints["regex"] = field["regex"]

            # Create a pydantic Field with constraints
            model_fields[field_name] = (field_type, Field(..., **constraints))
        
        logger.debug(f'Uploaded model fields for "{model_name}":\n{model_fields}\n')
        models[model_name] = create_model(model_name, **model_fields)
    return models

def get_date_fields(model: BaseModel) -> list[str]:
    """Retrieve a list of field names where the type is datetime.date."""
    return [field_name for field_name, field_type in model.__annotations__.items() if field_type == date]

def validate_csv(df: pd.DataFrame, model: BaseModel):
    date_fields = get_date_fields(model)
    for field in date_fields:
        if field in df.columns:
            df[field] = pd.to_datetime(df[field], errors='coerce')
            df[field] = df[field].apply(lambda x: x if pd.notnull(x) else None)

    errors = []
    for index, row in df.iterrows():
        try:
            row_dict = row.where(pd.notnull(row), None).to_dict()
            validated_data = model(**row_dict)
        except ValidationError as e:
            translated_errors = translate_errors(e.errors(), index)
            errors.extend(translated_errors)
    return len(errors) > 0, errors

def translate_errors(errors, row):
    error_messages = settings.schema.error_messages
    readable_errors = []
    for error in errors:
        field = error['loc'][0]
        error_type = error['type']
        input_value = str(error.get('input', 'N/A'))  # Ensure value is a string for Pydantic compatibility

        message = None
        if field in error_messages:
            for error_msg in error_messages[field]:
                if error_msg['type'] == error_type:
                    message = error_msg['message']
                    break

        if not message:
            message = error['msg']

        validation_detail = ValidationDetail(
            row=row,
            field=field,
            message=message,
            error_type=error_type,
            input_value=input_value
        )
        readable_errors.append(validation_detail)
    return readable_errors