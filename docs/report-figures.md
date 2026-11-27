# Report Figure Regeneration

The report figures use a hybrid evidence boundary:

- **Figure 1 — System Architecture** is derived `[D]` from
  [`docs/SPEC.md`](SPEC.md) and [`README.md`](../README.md).
- **Figure 2 — Execution & Attack Detection** is measured `[M]` from the
  offline `vcb verify` and `vcb attack` JSON command outputs.
- **Figure 3 — Digital Audit Receipt** is rendered `[M]` from the shared
  deterministic fixture ledger.

No adjudication model or API key is used. The generator fails explicitly if the
offline verification/attack commands or ledger fixture are unavailable; it does
not substitute invented success output.

## Generate

```bash
uv sync
uv run vcb figures \
  --ledger tests/fixtures/demo_audit_ledger.json \
  --output-dir results/report-figures
```

The command writes:

- `figure-1-system-architecture.svg` and `.png`
- `figure-2-execution-attack-detection.svg` and `.png`
- `figure-3-audit-receipt.svg` and `.png`

SVG is the authoritative output. PNG is rendered at 2x for report and
presentation use. On macOS, the generator uses `sips`; other platforms use
CairoSVG when its native Cairo library is available.

## Evidence contract

The capture layer invokes:

```bash
uv run vcb verify <ledger> --json
uv run vcb attack <ledger> --json
```

The JSON must contain explicit statuses, non-empty reason codes, and
`detected: true` plus `localized: true` for every attack case. Malformed or
incomplete output is an error, not a degraded figure.
