from __future__ import annotations

from importlib import import_module
from typing import TYPE_CHECKING, Any

__all__ = ["validate_data"]


if TYPE_CHECKING:
    from .algorithm import validate_data


def __getattr__(name: str) -> Any:
    if name == "validate_data":
        algorithm_module = import_module(".algorithm", __name__)
        return getattr(algorithm_module, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
