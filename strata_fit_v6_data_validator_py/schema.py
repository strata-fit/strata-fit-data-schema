from enum import Enum

from pydantic import BaseModel


class ValidationDetail(BaseModel):
    row: int | str
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
