import hashlib

import pytest

from vcb.core.canonical import canonicalize, digest, serialize


def test_canonicalize_normalizes_unicode_line_endings_and_trailing_whitespace() -> None:
    assert canonicalize("Cafe\u0301\r\nvalue  \rnext\t") == "Café\nvalue\nnext".encode()


def test_serialize_is_invariant_to_object_key_order() -> None:
    left = serialize({"z": 1, "a": {"b": 2, "a": 1}})
    right = serialize({"a": {"a": 1, "b": 2}, "z": 1})

    assert left == right


def test_serialize_excludes_record_hash_from_preimage() -> None:
    record = {"record_hash": "old", "seq": 0, "claim": "ok"}

    assert serialize(record, exclude_record_hash=True) == b'{"claim":"ok","seq":0}'
    assert serialize(record, exclude_record_hash=True) == serialize(
        {**record, "record_hash": "changed"},
        exclude_record_hash=True,
    )


def test_digest_uses_sha256_prefixed_hex() -> None:
    payload = b"canonical"

    assert digest(payload) == f"sha256:{hashlib.sha256(payload).hexdigest()}"


def test_serialize_rejects_floats_and_non_finite_numbers() -> None:
    with pytest.raises(TypeError, match="float"):
        serialize({"score": 70.0})
    with pytest.raises(ValueError, match="non-finite"):
        serialize({"score": float("nan")})
