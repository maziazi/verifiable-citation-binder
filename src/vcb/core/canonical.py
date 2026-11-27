from __future__ import annotations

import hashlib
import json
import math
import unicodedata
from collections.abc import Mapping
from typing import Any


def canonicalize(text: str) -> bytes:
    """Return UTF-8 bytes with stable Unicode, line endings, and whitespace."""
    if not isinstance(text, str):
        raise TypeError("canonicalize expects text")
    normalized = unicodedata.normalize("NFC", text)
    normalized = normalized.replace("\r\n", "\n").replace("\r", "\n")
    normalized = "\n".join(line.rstrip() for line in normalized.split("\n"))
    return normalized.encode("utf-8")


def _normalize_json(value: Any) -> Any:
    if isinstance(value, str):
        return unicodedata.normalize("NFC", value)
    if isinstance(value, Mapping):
        return {key: _normalize_json(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_normalize_json(item) for item in value]
    if isinstance(value, tuple):
        return [_normalize_json(item) for item in value]
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError("non-finite numbers are not supported")
        raise TypeError("float values are not supported")
    if value is None or isinstance(value, (bool, int)):
        return value
    raise TypeError(f"unsupported JSON value: {type(value).__name__}")


def serialize(
    value: Mapping[str, Any],
    *,
    exclude_record_hash: bool = False,
) -> bytes:
    """Serialize a record using the normative canonical JSON representation."""
    normalized = _normalize_json(value)
    if exclude_record_hash:
        normalized.pop("record_hash", None)
    return json.dumps(
        normalized,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def digest(data: bytes) -> str:
    if not isinstance(data, bytes):
        raise TypeError("digest expects bytes")
    return f"sha256:{hashlib.sha256(data).hexdigest()}"
