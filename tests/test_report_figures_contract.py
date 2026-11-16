from pathlib import Path

import pytest

from vcb.surface.report_figures import (
    CommandResult,
    CommandRunner,
    FigureEvidence,
    LedgerReceipt,
    ReportFigureError,
    capture_cli_evidence,
)


def test_figure_evidence_requires_status_and_reason_codes() -> None:
    with pytest.raises(ValueError, match="status"):
        FigureEvidence.from_mapping({"attack_cases": []})


def test_ledger_receipt_requires_chain_fields() -> None:
    with pytest.raises(ValueError, match="entry_hash"):
        LedgerReceipt.from_mapping({"seq": 0, "source_hash": "abc", "prev_hash": "0"})


def test_ledger_receipt_requires_semantic_fields() -> None:
    with pytest.raises(ValueError, match="claim"):
        LedgerReceipt.from_mapping(
            {
                "seq": 0,
                "source_hash": "abc",
                "prev_hash": "0",
                "entry_hash": "entry",
                "score": 70,
                "band": "AMBER",
                "reasons": ["S02"],
            }
        )


def test_command_runner_returns_process_result_without_swallowing_failure(
    tmp_path: Path,
) -> None:
    runner = CommandRunner()
    result = runner.run(["python", "-c", "import sys; print('out'); print('err', file=sys.stderr); sys.exit(3)"])

    assert result.returncode == 3
    assert result.stdout == "out\n"
    assert result.stderr == "err\n"

    with pytest.raises(ReportFigureError, match="exit code 3"):
        runner.run_required(["python", "-c", "import sys; sys.exit(3)"], cwd=tmp_path)


class QueueRunner(CommandRunner):
    def __init__(self, results: list[CommandResult]) -> None:
        self.results = iter(results)

    def run_required(self, command: list[str], *, cwd: Path | None = None) -> CommandResult:
        return next(self.results)


def test_capture_cli_evidence_requires_valid_verification_and_attack_output(
    tmp_path: Path,
) -> None:
    runner = QueueRunner(
        [
            CommandResult(
                ("uv", "run", "vcb", "verify"),
                0,
                '{"status":"valid","reasons":["L00"],"record_count":3}',
                "",
            ),
            CommandResult(
                ("uv", "run", "vcb", "attack"),
                0,
                (
                    '{"status":"complete","reasons":["L03","L01","L02"],'
                    '"cases":[{"class":"edit","detected":true,"localized":true,"code":"L03"},'
                    '{"class":"omission","detected":true,"localized":true,"code":"L01"}]}'
                ),
                "",
            ),
        ]
    )

    evidence = capture_cli_evidence(tmp_path / "ledger.json", runner)

    assert evidence.status == "valid"
    assert evidence.reasons == ("L03", "L01", "L02")
    assert len(evidence.attack_cases) == 2
    assert "[M]" in evidence.provenance


def test_capture_cli_evidence_rejects_missing_localization(tmp_path: Path) -> None:
    runner = QueueRunner(
        [
            CommandResult(("verify",), 0, '{"status":"valid","reasons":["L00"]}', ""),
            CommandResult(
                ("attack",),
                0,
                '{"status":"complete","reasons":["L03"],"cases":[{"class":"edit","detected":true}]}',
                "",
            ),
        ]
    )

    with pytest.raises(ReportFigureError, match="localized"):
        capture_cli_evidence(tmp_path / "ledger.json", runner)


def test_capture_cli_evidence_rejects_missing_verification_reasons(
    tmp_path: Path,
) -> None:
    runner = QueueRunner(
        [
            CommandResult(("verify",), 0, '{"status":"valid"}', ""),
            CommandResult(
                ("attack",),
                0,
                '{"status":"complete","reasons":["L03"],"cases":'
                '[{"class":"edit","detected":true,"localized":true,"code":"L03"}]}',
                "",
            ),
        ]
    )

    with pytest.raises(ReportFigureError, match="verification.*reasons"):
        capture_cli_evidence(tmp_path / "ledger.json", runner)


def test_capture_cli_evidence_rejects_missing_attack_class(tmp_path: Path) -> None:
    runner = QueueRunner(
        [
            CommandResult(("verify",), 0, '{"status":"valid","reasons":["L00"]}', ""),
            CommandResult(
                ("attack",),
                0,
                '{"status":"complete","reasons":["L03"],"cases":'
                '[{"detected":true,"localized":true,"code":"L03"}]}',
                "",
            ),
        ]
    )

    with pytest.raises(ReportFigureError, match="class"):
        capture_cli_evidence(tmp_path / "ledger.json", runner)
