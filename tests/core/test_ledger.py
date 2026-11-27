from pathlib import Path

from vcb.core.canonical import digest
from vcb.core.ledger import (
    GENESIS_HASH,
    BindingRecord,
    Claim,
    EvidenceRef,
    Ledger,
    PillarScores,
    Reason,
)


def _record() -> BindingRecord:
    return BindingRecord(
        timestamp="2026-11-16T09:14:22Z",
        query="What changed?",
        claim=Claim("c1", "Revenue rose.", ("doc#c1",)),
        evidence=(
            EvidenceRef("doc", "doc#c1", 0, 12, "Revenue rose.", "sha256:evidence"),
        ),
        pillars=PillarScores(100, 100, 100, 100),
        reasons=(
            Reason("S01", (0, 7), (0, 7), "The evidence states the claim."),
        ),
        score=100,
        band="GREEN",
        adjudication_failed=False,
    )


def test_binding_record_serializes_to_documented_shape() -> None:
    record = _record()

    payload = record.to_dict()

    assert payload["claim"]["claim_id"] == "c1"
    assert payload["evidence"][0]["digest"] == "sha256:evidence"
    assert payload["pillars"]["provenance"] == 100
    assert payload["record_hash"] == ""


def test_ledger_append_assigns_sequence_prev_hash_and_record_hash(tmp_path: Path) -> None:
    ledger = Ledger(head_path=tmp_path / "ledger.head")

    first = ledger.append(_record())
    second = ledger.append(_record())

    assert first.seq == 0
    assert first.prev_hash == GENESIS_HASH
    assert first.record_hash.startswith("sha256:")
    assert second.seq == 1
    assert second.prev_hash == first.record_hash
    assert ledger.records == [first, second]
    assert ledger.head_path.read_text() == f'{{"seq":1,"record_hash":"{second.record_hash}"}}'


def test_genesis_hash_is_fixed() -> None:
    assert GENESIS_HASH == digest(b"vcb-genesis-v1")
