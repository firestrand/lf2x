"""Secret detection helpers for LF2X flows."""

from __future__ import annotations

from dataclasses import dataclass

from ..ir import IntermediateRepresentation
from ..naming import slugify

_SECRET_HINTS = (
    "api_key",
    "apikey",
    "token",
    "secret",
    "password",
    "auth",
    "key",
)


@dataclass(frozen=True, slots=True)
class DetectedSecret:
    """Represents a secret value detected within a flow configuration."""

    env_var: str
    attribute: str
    source_node: str
    field: str
    raw_value: str | None


def detect_secrets(ir: IntermediateRepresentation) -> tuple[DetectedSecret, ...]:
    """Return a collection of secrets detected in the IR."""

    secrets: list[DetectedSecret] = []
    seen: set[str] = set()
    for node in ir.nodes:
        for field, value in node.data.items():
            if not _looks_like_secret(field, value):
                continue
            env_var = _env_var_name(ir.flow_id, node.node_id, field)
            if env_var in seen:
                continue
            seen.add(env_var)
            secrets.append(
                DetectedSecret(
                    env_var=env_var,
                    attribute=_attribute_name(env_var),
                    source_node=node.node_id,
                    field=field,
                    raw_value=value if isinstance(value, str) else None,
                )
            )
    return tuple(secrets)


def _looks_like_secret(field: str, value: object) -> bool:
    if not isinstance(value, str):
        return False
    if not value.strip():
        return False
    lower_field = field.lower()
    return any(hint in lower_field for hint in _SECRET_HINTS)


def _env_var_name(flow_id: str, node_id: str, field: str) -> str:
    slug = slugify(f"{flow_id}_{node_id}_{field}", default="lf2x_secret")
    return slug.upper()


def _attribute_name(env_var: str) -> str:
    return slugify(env_var.lower(), default="secret")


__all__ = ["DetectedSecret", "detect_secrets"]
