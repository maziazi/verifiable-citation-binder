import json
import struct
from pathlib import Path

from vcb.surface.report_figures import (
    CommandResult,
    CommandRunner,
    generate_report_figures,
)


class FixtureRunner(CommandRunner):
    def run_required(
        self, command: list[str], *, cwd: Path | None = None
    ) -> CommandResult:
        if "verify" in command:
            output = '{"status":"valid","reasons":["L00"],"record_count":1}'
        else:
            output = (
                '{"status":"complete","reasons":["L03"],"cases":'
                '[{"class":"edit","detected":true,"localized":true,"code":"L03"}]}'
            )
        return CommandResult(tuple(command), 0, output, "")


def _write_ledger(path: Path) -> None:
    path.write_text(
        json.dumps(
            {
                "seq": 0,
                "source_hash": "source",
                "prev_hash": "genesis",
                "entry_hash": "entry",
                "claim": "Revenue rose.",
                "score": 70,
                "band": "AMBER",
                "reasons": ["S02", "N01"],
            }
        ),
        encoding="utf-8",
    )


def test_generate_report_figures_writes_six_deterministic_assets(tmp_path: Path) -> None:
    ledger = tmp_path / "ledger.json"
    output = tmp_path / "figures"
    _write_ledger(ledger)

    first = generate_report_figures(ledger, output, runner=FixtureRunner())
    first_svg = (output / "figure-1-system-architecture.svg").read_bytes()
    second = generate_report_figures(ledger, output, runner=FixtureRunner())

    assert len(first) == 6
    assert {path.name for path in first} == {path.name for path in second}
    assert first_svg == (output / "figure-1-system-architecture.svg").read_bytes()
    png = (output / "figure-1-system-architecture.png").read_bytes()
    assert png[:8] == b"\x89PNG\r\n\x1a\n"
    width, height = struct.unpack(">II", png[16:24])
    assert (width, height) == (2400, 1240)
