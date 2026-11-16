from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import subprocess
from typing import Any, Mapping, Sequence


class ReportFigureError(RuntimeError):
    """Raised when report evidence cannot be captured or validated."""


@dataclass(frozen=True)
class CommandResult:
    command: tuple[str, ...]
    returncode: int
    stdout: str
    stderr: str


class CommandRunner:
    def run(
        self,
        command: Sequence[str],
        *,
        cwd: Path | None = None,
    ) -> CommandResult:
        completed = subprocess.run(
            list(command),
            cwd=cwd,
            check=False,
            text=True,
            capture_output=True,
        )
        return CommandResult(
            command=tuple(command),
            returncode=completed.returncode,
            stdout=completed.stdout,
            stderr=completed.stderr,
        )

    def run_required(
        self,
        command: Sequence[str],
        *,
        cwd: Path | None = None,
    ) -> CommandResult:
        result = self.run(command, cwd=cwd)
        if result.returncode != 0:
            rendered_command = " ".join(result.command)
            raise ReportFigureError(
                f"command {rendered_command!r} failed with exit code "
                f"{result.returncode}: {result.stderr.strip()}"
            )
        return result


@dataclass(frozen=True)
class FigureEvidence:
    status: str
    reasons: tuple[str, ...]
    attack_cases: tuple[Mapping[str, Any], ...]
    provenance: str

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> FigureEvidence:
        status = value.get("status")
        if not isinstance(status, str) or not status:
            raise ValueError("status is required")
        reasons = value.get("reasons")
        if not isinstance(reasons, list) or not all(
            isinstance(reason, str) and reason for reason in reasons
        ):
            raise ValueError("reasons must be a non-empty list of strings")
        attack_cases = value.get("attack_cases", [])
        if not isinstance(attack_cases, list) or not all(
            isinstance(case, Mapping) for case in attack_cases
        ):
            raise ValueError("attack_cases must be a list of mappings")
        provenance = value.get("provenance", "[M] offline CLI")
        if not isinstance(provenance, str) or not provenance:
            raise ValueError("provenance is required")
        return cls(status, tuple(reasons), tuple(attack_cases), provenance)


@dataclass(frozen=True)
class LedgerReceipt:
    seq: int
    source_hash: str
    prev_hash: str
    entry_hash: str
    claim: str = ""
    score: int | float | None = None
    band: str = ""
    reasons: tuple[str, ...] = ()

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> LedgerReceipt:
        required = ("seq", "source_hash", "prev_hash", "entry_hash")
        missing = [field for field in required if field not in value]
        if missing:
            raise ValueError(f"{missing[0]} is required")
        seq = value["seq"]
        if not isinstance(seq, int) or isinstance(seq, bool) or seq < 0:
            raise ValueError("seq must be a non-negative integer")
        fields = {field: value[field] for field in required[1:]}
        if not all(isinstance(item, str) and item for item in fields.values()):
            raise ValueError("chain fields must be non-empty strings")
        reasons = value.get("reasons", [])
        if not isinstance(reasons, list) or not all(isinstance(item, str) for item in reasons):
            raise ValueError("reasons must be a list of strings")
        return cls(
            seq=seq,
            source_hash=fields["source_hash"],
            prev_hash=fields["prev_hash"],
            entry_hash=fields["entry_hash"],
            claim=str(value.get("claim", "")),
            score=value.get("score"),
            band=str(value.get("band", "")),
            reasons=tuple(reasons),
        )


def load_ledger_receipt(path: Path) -> LedgerReceipt:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(payload, list):
        if not payload:
            raise ReportFigureError("ledger contains no records")
        payload = payload[0]
    if not isinstance(payload, Mapping):
        raise ReportFigureError("ledger root must be an object or record list")
    try:
        return LedgerReceipt.from_mapping(payload)
    except ValueError as exc:
        raise ReportFigureError(f"invalid ledger receipt: {exc}") from exc


def _parse_cli_json(result: CommandResult, label: str) -> Mapping[str, Any]:
    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise ReportFigureError(f"{label} command returned invalid JSON") from exc
    if not isinstance(payload, Mapping):
        raise ReportFigureError(f"{label} command must return a JSON object")
    return payload


def capture_cli_evidence(
    ledger_path: Path,
    runner: CommandRunner,
) -> FigureEvidence:
    verify_command = ["uv", "run", "vcb", "verify", str(ledger_path), "--json"]
    attack_command = ["uv", "run", "vcb", "attack", str(ledger_path), "--json"]
    verify_payload = _parse_cli_json(
        runner.run_required(verify_command),
        "verify",
    )
    attack_payload = _parse_cli_json(
        runner.run_required(attack_command),
        "attack",
    )

    verify_status = verify_payload.get("status")
    if verify_status != "valid":
        raise ReportFigureError("verify output must have status 'valid'")
    attack_status = attack_payload.get("status")
    if attack_status != "complete":
        raise ReportFigureError("attack output must have status 'complete'")
    reasons = attack_payload.get("reasons")
    if not isinstance(reasons, list) or not reasons:
        raise ReportFigureError("attack output must include non-empty reasons")
    cases = attack_payload.get("cases")
    if not isinstance(cases, list) or not cases:
        raise ReportFigureError("attack output must include cases")
    for index, case in enumerate(cases):
        if not isinstance(case, Mapping):
            raise ReportFigureError(f"attack case {index} must be an object")
        if case.get("detected") is not True or case.get("localized") is not True:
            raise ReportFigureError(
                f"attack case {index} must include detected and localized=true"
            )
        if not isinstance(case.get("code"), str) or not case["code"]:
            raise ReportFigureError(f"attack case {index} must include a reason code")

    return FigureEvidence.from_mapping(
        {
            "status": verify_status,
            "reasons": reasons,
            "attack_cases": cases,
            "provenance": (
                f"[M] uv run vcb verify {ledger_path} --json; "
                f"uv run vcb attack {ledger_path} --json"
            ),
        }
    )


def generate_report_figures(ledger_path: Path, output_dir: Path) -> list[Path]:
    raise ReportFigureError(
        "figure generation requires the CLI capture and renderer tasks"
    )
