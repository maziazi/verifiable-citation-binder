from __future__ import annotations

import json
from dataclasses import dataclass, replace
from pathlib import Path

from vcb.core.canonical import digest, serialize

GENESIS_HASH = digest(b"vcb-genesis-v1")


@dataclass(frozen=True)
class EvidenceRef:
    doc_id: str
    chunk_id: str
    start: int
    end: int
    text: str
    digest: str

    def to_dict(self) -> dict[str, object]:
        return {
            "doc_id": self.doc_id,
            "chunk_id": self.chunk_id,
            "start": self.start,
            "end": self.end,
            "digest": self.digest,
            "text": self.text,
        }


@dataclass(frozen=True)
class Claim:
    claim_id: str
    text: str
    cited_chunk_ids: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "claim_id": self.claim_id,
            "text": self.text,
            "cited_chunk_ids": list(self.cited_chunk_ids),
        }


@dataclass(frozen=True)
class PillarScores:
    support: int
    specificity: int
    coverage: int
    provenance: int

    def to_dict(self) -> dict[str, int]:
        return {
            "support": self.support,
            "specificity": self.specificity,
            "coverage": self.coverage,
            "provenance": self.provenance,
        }


@dataclass(frozen=True)
class Reason:
    code: str
    claim_span: tuple[int, int]
    evidence_span: tuple[int, int]
    explanation: str

    def to_dict(self) -> dict[str, object]:
        return {
            "code": self.code,
            "claim_span": list(self.claim_span),
            "evidence_span": list(self.evidence_span),
            "explanation": self.explanation,
        }


@dataclass(frozen=True)
class BindingRecord:
    timestamp: str
    query: str
    claim: Claim
    evidence: tuple[EvidenceRef, ...]
    pillars: PillarScores
    reasons: tuple[Reason, ...]
    score: int
    band: str
    adjudication_failed: bool
    seq: int = -1
    prev_hash: str = ""
    record_hash: str = ""

    def to_dict(self) -> dict[str, object]:
        return {
            "seq": self.seq,
            "prev_hash": self.prev_hash,
            "record_hash": self.record_hash,
            "timestamp": self.timestamp,
            "query": self.query,
            "claim": self.claim.to_dict(),
            "evidence": [item.to_dict() for item in self.evidence],
            "pillars": self.pillars.to_dict(),
            "reasons": [item.to_dict() for item in self.reasons],
            "score": self.score,
            "band": self.band,
            "adjudication_failed": self.adjudication_failed,
        }


class Ledger:
    def __init__(self, *, head_path: Path) -> None:
        self.records: list[BindingRecord] = []
        self.head_path = head_path

    def append(self, record: BindingRecord) -> BindingRecord:
        assigned = replace(
            record,
            seq=len(self.records),
            prev_hash=self.records[-1].record_hash if self.records else GENESIS_HASH,
        )
        record_hash = digest(serialize(assigned.to_dict(), exclude_record_hash=True))
        assigned = replace(assigned, record_hash=record_hash)
        self.records.append(assigned)
        self.head_path.parent.mkdir(parents=True, exist_ok=True)
        self.head_path.write_text(
            json.dumps(
                {"seq": assigned.seq, "record_hash": assigned.record_hash},
                separators=(",", ":"),
        ),
            encoding="utf-8",
        )
        return assigned
