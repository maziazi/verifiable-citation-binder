from pathlib import Path

import pytest

from vcb.surface.report_figures import (
    CommandRunner,
    FigureEvidence,
    LedgerReceipt,
    ReportFigureError,
)


def test_figure_evidence_requires_status_and_reason_codes() -> None:
    with pytest.raises(ValueError, match="status"):
        FigureEvidence.from_mapping({"attack_cases": []})


def test_ledger_receipt_requires_chain_fields() -> None:
    with pytest.raises(ValueError, match="entry_hash"):
        LedgerReceipt.from_mapping({"seq": 0, "source_hash": "abc", "prev_hash": "0"})


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
