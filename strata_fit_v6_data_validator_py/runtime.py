from __future__ import annotations

import base64
import binascii
import json
import os

from functools import wraps
from importlib.metadata import EntryPoint, entry_points
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping


RUN_CONTEXT_ENTRYPOINT_GROUP = "run_context"
STRING_ENCODING = "utf-8"
ENV_VAR_EQUALS_REPLACEMENT = "!"
_NEEDS_CONTEXT_ATTR = "__run_context_needs_context__"


def decode_env_value(value: str) -> str:
    encoded = value.replace(ENV_VAR_EQUALS_REPLACEMENT, "=").encode(STRING_ENCODING)
    try:
        return base64.b32decode(encoded).decode(STRING_ENCODING)
    except binascii.Error:
        return value


def get_env_var(var_name: str, default: str | None = None) -> str | None:
    if var_name not in os.environ:
        return default
    return decode_env_value(os.environ[var_name])


class RunContext:
    def __init__(self, source: Path, payload: Mapping[str, Any]) -> None:
        self.source = source
        self.payload = payload

    @classmethod
    def from_path(cls, path: str | Path) -> "RunContext":
        source = Path(path)
        with source.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
        if not isinstance(payload, dict):
            raise ValueError("Run context must be a JSON object")
        return cls(source=source, payload=payload)

    @classmethod
    def from_env(cls) -> "RunContext":
        run_context_file = get_env_var("RUN_CONTEXT_FILE")
        if not run_context_file:
            raise RuntimeError("RUN_CONTEXT_FILE is not set")
        return cls.from_path(run_context_file)

    @property
    def entrypoint(self) -> Any:
        return self.payload.get("entrypoint")

    @property
    def arguments(self) -> Any:
        return self.payload.get("arguments")

    @property
    def inputs(self) -> Any:
        return self.payload.get("inputs")

    @property
    def outputs(self) -> Any:
        return self.payload.get("outputs")

    def entrypoint_name(self) -> str:
        if not isinstance(self.entrypoint, dict):
            raise ValueError("Run context field 'entrypoint' must be an object")
        name = self.entrypoint.get("name")
        if not isinstance(name, str) or not name:
            raise ValueError("Run context field 'entrypoint.name' must be a non-empty string")
        return name

    def named_args(self) -> dict[str, Any]:
        if not isinstance(self.arguments, dict):
            return {}
        named = self.arguments.get("named")
        return named if isinstance(named, dict) else {}

    def _uris(self, field: str) -> list[Path]:
        items = self.inputs if field == "inputs" else self.outputs
        if not isinstance(items, list):
            raise ValueError(f"Run context {field} must be a list")
        uris: list[Path] = []
        for idx, item in enumerate(items):
            if not isinstance(item, dict):
                raise ValueError(f"Run context {field}[{idx}] must be an object")
            uri = item.get("uri")
            if not isinstance(uri, str) or not uri:
                raise ValueError(f"Run context {field}[{idx}].uri must be a non-empty string")
            uris.append(Path(uri))
        return uris

    def input_uris(self) -> list[Path]:
        return self._uris("inputs")

    def output_uris(self) -> list[Path]:
        return self._uris("outputs")


def _normalize_named_arguments(value: str | Iterable[str] | None) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, str):
        return (value,)
    return tuple(item for item in value if isinstance(item, str) and item)


def _mark_wants_context(func: Callable[..., Any]) -> None:
    setattr(func, _NEEDS_CONTEXT_ATTR, True)


def run_context(
    func: Callable[..., Any] | None = None,
    *,
    input_uris: str | None = None,
    named_arguments: str | Iterable[str] | None = None,
    output_uris: str | None = None,
    include_context: bool = False,
) -> Callable[..., Any]:
    normalized_named_args = _normalize_named_arguments(named_arguments)

    def decorator(inner: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(inner)
        def wrapper(*args, **kwargs):
            context = kwargs.pop("run_context", None)
            if context is None:
                return inner(*args, **kwargs)
            if not isinstance(context, RunContext):
                raise TypeError("'run_context' must be a RunContext instance")

            if input_uris:
                values = context.input_uris()
                if len(values) != 1:
                    raise ValueError(
                        f"Expected exactly 1 run-context inputs URI value(s), found {len(values)}"
                    )
                kwargs[input_uris] = values[0]

            if output_uris:
                values = context.output_uris()
                if len(values) != 1:
                    raise ValueError(
                        f"Expected exactly 1 run-context outputs URI value(s), found {len(values)}"
                    )
                kwargs[output_uris] = values[0]

            if normalized_named_args:
                named = context.named_args()
                for name in normalized_named_args:
                    if name in named:
                        kwargs[name] = named[name]

            if include_context:
                kwargs["run_context"] = context
            return inner(*args, **kwargs)

        _mark_wants_context(wrapper)
        return wrapper

    if func is not None:
        return decorator(func)
    return decorator


def _entrypoint_distribution_name(entry_point: EntryPoint) -> str:
    dist = getattr(entry_point, "dist", None)
    name = getattr(dist, "name", None)
    if not isinstance(name, str) or not name:
        raise ValueError(
            f"run-context entrypoint '{entry_point.name}' is missing distribution metadata"
        )
    return name


def _raise_if_multiple_distributions(entry_points_: list[EntryPoint]) -> None:
    distributions = {_entrypoint_distribution_name(ep) for ep in entry_points_}
    if len(distributions) > 1:
        found = ", ".join(sorted(distributions))
        raise ValueError(
            "run-context entrypoints must come from exactly 1 distribution when "
            f"require_single_distribution=True. Found distributions: {found}"
        )


def _resolve_entrypoint_callable(
    name: str,
    *,
    require_single_distribution: bool = True,
) -> Callable[..., Any]:
    available = list(entry_points(group=RUN_CONTEXT_ENTRYPOINT_GROUP))
    if require_single_distribution:
        _raise_if_multiple_distributions(available)
    matches = [item for item in available if item.name == name]
    if not matches:
        allowed = ", ".join(sorted(item.name for item in available)) or "<none>"
        raise ValueError(
            f"Unsupported run-context entrypoint '{name}'. Allowed entrypoints: {allowed}"
        )
    if len(matches) > 1:
        raise ValueError(f"Duplicate run-context entrypoint '{name}'")
    return matches[0].load()


def dispatch_run_context(*, require_single_distribution: bool = True) -> Any:
    context = RunContext.from_env()
    requested = context.entrypoint_name()
    func = _resolve_entrypoint_callable(
        requested,
        require_single_distribution=require_single_distribution,
    )
    kwargs: dict[str, Any] = {}
    if getattr(func, _NEEDS_CONTEXT_ATTR, False):
        kwargs["run_context"] = context
    return func(**kwargs)


def main() -> Any:
    if os.environ.get("RUN_CONTEXT_FILE"):
        return dispatch_run_context()
    raise RuntimeError("No supported runtime context found. Expected RUN_CONTEXT_FILE.")
