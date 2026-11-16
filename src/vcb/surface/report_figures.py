from __future__ import annotations

from dataclasses import dataclass
from html import escape
import json
from pathlib import Path
import subprocess
from typing import Any, Mapping, Sequence


class ReportFigureError(RuntimeError):
    """Raised when report evidence cannot be captured or validated."""


_BG = "#FBFBF9"
_TEXT = "#1A1A18"
_MUTED = "#5C5B56"
_ACCENT = "#1F4E79"
_GREEN = "#E8F3EC"
_BLACK = "#1A1A18"
_AMBER = "#FDF2DC"


def _svg_start(title: str, width: int, height: int) -> list[str]:
    return [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}">',
        f'<rect width="{width}" height="{height}" fill="{_BG}"/>',
        f'<text x="40" y="52" font-family="system-ui, sans-serif" font-size="26" '
        f'font-weight="600" fill="{_TEXT}">{escape(title)}</text>',
    ]


def _text(lines: list[str], x: int, y: int, value: str, *, size: int = 16, fill: str = _TEXT, weight: str = "400") -> None:
    lines.append(
        f'<text x="{x}" y="{y}" font-family="system-ui, sans-serif" '
        f'font-size="{size}" font-weight="{weight}" fill="{fill}">{escape(value)}</text>'
    )


def _svg_end(lines: list[str]) -> str:
    lines.append("</svg>")
    return "\n".join(lines)


def render_architecture_figure() -> str:
    lines = _svg_start("System Architecture", 1200, 620)
    stages = [
        ("Retrieval", "Retrieved source chunks"),
        ("Seal evidence", "SHA-256 source fingerprint"),
        ("Claim adjudication", "Score + reasons[]"),
        ("Audit ledger", "prev_hash + seq"),
        ("Audit Viewer", "Claim bands + evidence"),
    ]
    x_positions = [40, 270, 500, 730, 960]
    for index, ((label, detail), x) in enumerate(zip(stages, x_positions)):
        fill = _GREEN if label in {"Seal evidence", "Audit ledger"} else "#FFFFFF"
        lines.append(
            f'<rect x="{x}" y="180" width="190" height="150" rx="10" '
            f'fill="{fill}" stroke="{_ACCENT}" stroke-width="2"/>'
        )
        _text(lines, x + 16, 220, label, size=17, weight="600")
        _text(lines, x + 16, 260, detail, size=14, fill=_MUTED)
        if index < len(stages) - 1:
            lines.append(
                f'<path d="M {x + 190} 255 H {x + 220}" stroke="{_ACCENT}" '
                f'stroke-width="3" marker-end="url(#arrow)"/>'
            )
    lines.insert(
        1,
        '<defs><marker id="arrow" markerWidth="10" markerHeight="10" refX="8" refY="3" '
        'orient="auto"><path d="M0,0 L0,6 L9,3 z" fill="#1F4E79"/></marker></defs>',
    )
    _text(lines, 40, 390, "Tier 1 · deterministic integrity", size=14, fill=_ACCENT, weight="600")
    _text(lines, 500, 390, "Tier 2 · model-dependent adjudication", size=14, fill=_MUTED, weight="600")
    _text(lines, 960, 390, "Tier 3 · surface", size=14, fill=_MUTED, weight="600")
    _text(lines, 40, 555, "[D] Derived from docs/SPEC.md §5 and README.md", size=13, fill=_MUTED)
    return _svg_end(lines)


def render_attack_figure(evidence: FigureEvidence) -> str:
    lines = _svg_start("Execution & Attack Detection", 1200, 620)
    status_fill = _GREEN if evidence.status == "valid" else _BLACK
    status_text = "VALID" if evidence.status == "valid" else evidence.status.upper()
    lines.append(
        f'<rect x="40" y="90" width="1120" height="68" rx="8" fill="{status_fill}"/>'
    )
    _text(lines, 64, 132, status_text, size=20, fill=_TEXT if evidence.status == "valid" else _BG, weight="700")
    _text(lines, 260, 132, "Offline verification complete", size=16, fill=_TEXT if evidence.status == "valid" else _BG)
    y = 210
    for case in evidence.attack_cases:
        case_label = str(case["class"]).upper()
        state = "DETECTED" if case["detected"] and case["localized"] else "NOT VERIFIED"
        lines.append(
            f'<rect x="40" y="{y - 30}" width="1120" height="64" rx="8" fill="{_AMBER if state == "DETECTED" else "#FFFFFF"}" stroke="{_MUTED}"/>'
        )
        _text(lines, 64, y + 8, case_label, size=16, weight="700")
        _text(lines, 460, y + 8, state, size=16, fill=_TEXT, weight="700")
        _text(lines, 820, y + 8, str(case["code"]), size=16, fill=_ACCENT, weight="700")
        y += 86
    _text(lines, 40, 555, evidence.provenance, size=13, fill=_MUTED)
    return _svg_end(lines)


def render_receipt_figure(
    receipt: LedgerReceipt | Mapping[str, Any],
    *,
    provenance: str = "[M] shared fixture ledger",
) -> str:
    if not isinstance(receipt, LedgerReceipt):
        try:
            receipt = LedgerReceipt.from_mapping(receipt)
        except ValueError as exc:
            raise ReportFigureError(f"invalid ledger receipt: {exc}") from exc
    lines = _svg_start("Digital Audit Receipt", 1200, 620)
    fields = (
        ("seq", str(receipt.seq)),
        ("source_hash", receipt.source_hash),
        ("prev_hash", receipt.prev_hash),
        ("entry_hash", receipt.entry_hash),
        ("claim", receipt.claim),
        ("score", str(receipt.score) if receipt.score is not None else ""),
        ("band", receipt.band),
        ("reasons", ", ".join(receipt.reasons)),
    )
    y = 110
    for key, value in fields:
        _text(lines, 64, y, key, size=15, fill=_ACCENT, weight="700")
        _text(lines, 270, y, value, size=15, fill=_TEXT)
        y += 48
    _text(lines, 40, 575, provenance, size=13, fill=_MUTED)
    return _svg_end(lines)


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
