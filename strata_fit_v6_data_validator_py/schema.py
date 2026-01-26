from enum import Enum
from pydantic import BaseModel, Field
from datetime import date
from typing import Optional, Union

class ValidationDetail(BaseModel):
    row: Union[int, str]
    field: str
    message: str
    error_type: str
    input_value: str

class PandasDelimeter(Enum):
    COMMA = ","
    SEMICOLON = ";"
    TAB = "\t"
    PIPE = "|"
    COLON = ":"
    SPACE = " "
