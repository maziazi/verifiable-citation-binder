# Audit Report Figures Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a deterministic offline command that produces three report-ready
figures from the project's shared CLI and fixture-ledger evidence.

**Architecture:** Keep rendering in a report-assets module outside
`src/vcb/core/`. The command runs the existing offline verification/attack
commands through `subprocess`, parses their structured output, reads one record
from the shared fixture ledger, and passes typed data to a dependency-light SVG
renderer. SVG is authoritative; CairoSVG creates a 2x PNG companion.

**Tech Stack:** Python 3, standard-library `subprocess`/`json`/`xml` handling,
SVG, CairoSVG for PNG export, pytest.

**Spec:** [`docs/superpowers/specs/2026-11-16-audit-report-figures-design.md`](../specs/2026-11-16-audit-report-figures-design.md)

## Global Constraints

- `src/vcb/core/` must remain pure, deterministic, and offline.
- `vcb verify` and `vcb attack` must remain offline and deterministic.
- No API keys, `.env` values, or real user ledger state may enter generated assets.
- Every verdict must retain non-empty `reasons[]`.
- Every quantitative figure label must carry `[M]` or `[D]` provenance and name its source command/document.
- Generated assets must use the existing VCB palette and explicit text/glyph labels, not color alone.
- Do not weaken existing tests to make figure generation pass.

## Review Focus

- **Missing CLI:** the generator must fail loudly with the command and captured stderr, not render success-shaped placeholder evidence; test in Task 2.
- **Malformed CLI output:** the parser must reject missing status, code, or localization fields; test in Task 2.
- **Ledger record omission:** Figure 3 must report a missing required field rather than silently dropping it; test in Task 3.
- **Special characters in claims/JSON:** SVG text must be escaped so `<`, `&`, and quotes cannot corrupt the image; test in Task 3.
- **Reproducibility:** identical CLI/ledger inputs must produce equivalent SVG content and stable PNG dimensions; test in Task 4.

---

### Task 1: Establish the report-figure module and command contract

**Files:**
- Create: `pyproject.toml`
- Create: `src/vcb/__init__.py`
- Create: `src/vcb/surface/__init__.py`
- Create: `src/vcb/surface/report_figures.py`
- Create: `tests/test_report_figures_contract.py`

**Interfaces:**
- Consumes: the existing offline commands `uv run vcb verify <ledger>` and
  `uv run vcb attack <ledger>` once the core CLI is present.
- Produces:
  `FigureEvidence`, `LedgerReceipt`, `CommandRunner`, and
  `generate_report_figures(ledger_path: Path, output_dir: Path) -> list[Path]`.

- [ ] **Step 1: Write failing contract tests**

  Add tests for the typed evidence objects rejecting missing required fields,
  and for `CommandRunner` returning stdout/stderr/exit code without swallowing
  process failures.

- [ ] **Step 2: Run the focused tests**

  Run: `uv run pytest tests/test_report_figures_contract.py -v`

  Expected: FAIL because the report-figure module and package metadata do not
  yet exist.

- [ ] **Step 3: Implement the contract**

  Define dataclasses for command results and the two evidence payloads. Use
  `subprocess.run(..., check=False, text=True, capture_output=True)` and raise a
  report-specific error containing the command, exit code, and stderr when a
  required command fails. Do not import `vcb.adjudicate` or perform network I/O.

- [ ] **Step 4: Run the focused tests**

  Run: `uv run pytest tests/test_report_figures_contract.py -v`

  Expected: PASS.

- [ ] **Step 5: Commit**

  ```bash
  git add pyproject.toml src/vcb/__init__.py src/vcb/surface/__init__.py \
    src/vcb/surface/report_figures.py tests/test_report_figures_contract.py
  git commit -m "feat: add report figure evidence contract"
  ```

### Task 2: Capture and validate offline CLI evidence

**Files:**
- Modify: `src/vcb/surface/report_figures.py`
- Modify: `tests/test_report_figures_contract.py`
- Create: `tests/fixtures/report_cli_valid.json`
- Create: `tests/fixtures/report_cli_invalid.json`

**Interfaces:**
- Consumes: `CommandRunner` from Task 1 and the CLI result shape exposed by
  `vcb verify` and `vcb attack`.
- Produces:
  `capture_cli_evidence(ledger_path: Path, runner: CommandRunner) -> FigureEvidence`.

- [ ] **Step 1: Write failing parser tests**

  Pin valid evidence for one successful verification plus edit and omission
  detections, and pin failures for missing status, missing reason code, and
  missing localization.

- [ ] **Step 2: Run tests to verify they fail**

  Run: `uv run pytest tests/test_report_figures_contract.py -k cli -v`

  Expected: FAIL because CLI capture/parsing is not implemented.

- [ ] **Step 3: Implement CLI capture**

  Execute verification and attack through the runner, parse only the documented
  structured output, and validate the required statuses/codes before returning
  evidence. Include the exact command strings in `[M]` provenance metadata.
  Raise an explicit parsing error for malformed or incomplete output.

- [ ] **Step 4: Run tests to verify they pass**

  Run: `uv run pytest tests/test_report_figures_contract.py -k cli -v`

  Expected: PASS.

- [ ] **Step 5: Commit**

  ```bash
  git add src/vcb/surface/report_figures.py tests/test_report_figures_contract.py \
    tests/fixtures/report_cli_valid.json tests/fixtures/report_cli_invalid.json
  git commit -m "feat: capture offline verification evidence for figures"
  ```

### Task 3: Render architecture and audit receipt figures

**Files:**
- Modify: `src/vcb/surface/report_figures.py`
- Create: `tests/test_report_figures_rendering.py`

**Interfaces:**
- Consumes: `FigureEvidence` from Task 2 and a shared fixture ledger path.
- Produces: deterministic SVG strings/files for:
  `render_architecture_figure(...)`,
  `render_attack_figure(...)`, and
  `render_receipt_figure(...)`.

- [ ] **Step 1: Write failing rendering tests**

  Assert that each SVG contains its title, required stage labels or receipt
  fields, provenance text, explicit status labels, and escaped special
  characters. Assert that the receipt renderer rejects a record missing
  `seq`, `source_hash`, `prev_hash`, or `entry_hash`.

- [ ] **Step 2: Run tests to verify they fail**

  Run: `uv run pytest tests/test_report_figures_rendering.py -v`

  Expected: FAIL because the renderers are not implemented.

- [ ] **Step 3: Implement deterministic SVG renderers**

  Use a small internal SVG builder with XML escaping, fixed canvas sizes, and
  palette constants copied from [`docs/DESIGN.md`](../../DESIGN.md). Keep
  architecture labels aligned with README/SPEC terminology. Render Figure 2
  from captured statuses rather than hard-coded success claims. Render Figure 3
  from the shared ledger record and show all required chain fields.

- [ ] **Step 4: Run tests to verify they pass**

  Run: `uv run pytest tests/test_report_figures_rendering.py -v`

  Expected: PASS.

- [ ] **Step 5: Commit**

  ```bash
  git add src/vcb/surface/report_figures.py tests/test_report_figures_rendering.py
  git commit -m "feat: render architecture and audit receipt figures"
  ```

### Task 4: Add the generation command and PNG export

**Files:**
- Modify: `pyproject.toml`
- Modify: `src/vcb/surface/report_figures.py`
- Create: `scripts/generate_report_figures.py`
- Create: `tests/test_generate_report_figures.py`
- Modify: `.gitignore`

**Interfaces:**
- Consumes: `generate_report_figures(...)` and the shared deterministic fixture
  ledger.
- Produces: `figure-1-system-architecture.svg/.png`,
  `figure-2-execution-attack-detection.svg/.png`, and
  `figure-3-audit-receipt.svg/.png`.

- [ ] **Step 1: Write failing command tests**

  Invoke the generator with a temporary ledger/output directory and assert all
  six files exist, PNG dimensions are exactly 2x their SVG target dimensions,
  and a repeated run produces equivalent SVG content. Assert a failed CLI
  produces a non-zero command result with a useful error.

- [ ] **Step 2: Run tests to verify they fail**

  Run: `uv run pytest tests/test_generate_report_figures.py -v`

  Expected: FAIL because the script and PNG export are not implemented.

- [ ] **Step 3: Implement the command**

  Add `uv run vcb figures --ledger <path> --output-dir <path>` as the supported
  entry point, invoke the shared fixture/ledger mechanism, write authoritative
  SVG files, and convert each SVG to a 2x PNG using CairoSVG. Make output
  directories explicit and never write to the repository root implicitly.

- [ ] **Step 4: Run focused and offline validation**

  Run:

  ```bash
  uv run pytest tests/test_generate_report_figures.py -v
  uv run vcb figures --ledger tests/fixtures/demo_audit_ledger.json --output-dir results/report-figures
  ```

  Expected: tests pass and the command reports six generated files without API
  key access.

- [ ] **Step 5: Commit**

  ```bash
  git add pyproject.toml src/vcb/surface/report_figures.py \
    scripts/generate_report_figures.py tests/test_generate_report_figures.py .gitignore
  git commit -m "feat: add reproducible report figure generation"
  ```

### Task 5: Document regeneration and review the generated assets

**Files:**
- Modify: `README.md`
- Modify: `docs/WORKFLOW.md`
- Create: `docs/report-figures.md`

**Interfaces:**
- Consumes: the `vcb figures` command and the generated asset names from Task 4.
- Produces: documented, repeatable figure regeneration instructions and a
  provenance note for each figure.

- [ ] **Step 1: Document the command and evidence boundary**

  Explain that Figure 1 is derived from the architecture docs while Figures 2–3
  are measured/rendered from offline CLI and shared fixture-ledger outputs.
  Include the no-API-key constraint and the generated filenames.

- [ ] **Step 2: Run documentation-linked validation**

  Run: `uv run vcb figures --help`

  Expected: help text names the ledger and output directory arguments.

- [ ] **Step 3: Commit**

  ```bash
  git add README.md docs/WORKFLOW.md docs/report-figures.md
  git commit -m "docs: document report figure regeneration"
  ```

## Self-review

- **Spec coverage:** The plan covers the selected hybrid approach, CLI evidence
  source, shared fixture ledger, deterministic SVG/PNG outputs, visual tokens,
  provenance tags, and offline validation. It intentionally does not alter
  Tier 1 algorithms or implement a second ledger.
- **Step scan:** Each task has a failing test, a focused implementation, a
  passing validation, and a conventional commit.
- **Type consistency:** `CommandRunner` and `FigureEvidence` are introduced in
  Task 1, consumed by capture in Task 2, and passed to renderers in Tasks 3–4.
- **Review focus:** All five failure modes are pinned to tests in the owning
  tasks.
- **Proportion:** The plan stays limited to report-figure generation; core
  verification remains a prerequisite and is not duplicated here.
