import pytest

from vcb.surface.report_figures import (
    FigureEvidence,
    LedgerReceipt,
    ReportFigureError,
    render_architecture_figure,
    render_attack_figure,
    render_receipt_figure,
)


def test_architecture_figure_contains_documented_stage_labels_and_provenance() -> None:
    svg = render_architecture_figure()

    assert "System Architecture" in svg
    for label in ("Retrieval", "Seal evidence", "Claim adjudication", "Audit ledger", "Audit Viewer"):
        assert label in svg
    assert "[D]" in svg


def test_attack_figure_renders_statuses_and_escapes_case_text() -> None:
    evidence = FigureEvidence(
        status="valid",
        reasons=("L03", "L01"),
        attack_cases=(
            {"class": "edit <score>", "detected": True, "localized": True, "code": "L03"},
            {"class": "omission", "detected": True, "localized": True, "code": "L01"},
        ),
        provenance="[M] test command",
    )

    svg = render_attack_figure(evidence)

    assert "Execution &amp; Attack Detection" in svg
    assert "VALID" in svg
    assert "EDIT &lt;SCORE&gt;" in svg
    assert "DETECTED" in svg
    assert "[M] test command" in svg


def test_receipt_figure_renders_chain_fields_and_escapes_claim() -> None:
    receipt = LedgerReceipt(
        seq=7,
        source_hash="source-123",
        prev_hash="prev-456",
        entry_hash="entry-789",
        claim='Revenue <rose> & "grew"',
        score=70,
        band="AMBER",
        reasons=("S02", "N01"),
    )

    svg = render_receipt_figure(receipt, provenance="[M] fixture ledger")

    assert "Digital Audit Receipt" in svg
    for field in ("seq", "source_hash", "prev_hash", "entry_hash"):
        assert field in svg
    assert "Revenue &lt;rose&gt; &amp; &quot;grew&quot;" in svg
    assert "[M] fixture ledger" in svg


def test_receipt_figure_rejects_missing_chain_field() -> None:
    with pytest.raises(ReportFigureError, match="entry_hash"):
        render_receipt_figure(
            {"seq": 7, "source_hash": "source-123", "prev_hash": "prev-456"}
        )
