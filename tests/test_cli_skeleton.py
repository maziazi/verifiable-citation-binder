import sys
from subprocess import run


def test_vcb_help_lists_project_commands() -> None:
    result = run(
        [sys.executable, "-m", "vcb.cli", "--help"],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    for command in ("demo", "verify", "attack", "eval", "figures"):
        assert command in result.stdout
