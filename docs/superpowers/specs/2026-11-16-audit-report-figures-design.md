# Audit Report Figures Design

## Intent

Create the first report-ready visual evidence for Verifiable Citation Binder:

1. **Figure 1 — System Architecture:** the path from retrieved source chunks
   through evidence sealing, claim adjudication, hash-chained ledger append, and
   audit viewer output.
2. **Figure 2 — Execution and Attack Detection:** a terminal-style visual showing
   a valid ledger, a detected edit, and a detected middle-record omission.
3. **Figure 3 — Digital Audit Receipt:** a readable JSON excerpt showing one
   binding record and its cryptographic chain fields.

The figures are for a research report and a hackathon judge. They must be
understandable without opening the source code, while every factual status and
number must come from the executable project artifacts.

## Goals

- Produce reproducible, report-ready SVG and raster outputs.
- Keep Figure 1 visually clean and explanatory rather than pretending to be a
  runtime trace.
- Generate Figures 2 and 3 from real CLI/ledger fixtures so the displayed
  evidence is inspectable and regenerable.
- Preserve the existing visual language in [`docs/DESIGN.md`](../../DESIGN.md):
  warm off-white background, blue accent, monospace hashes/reason codes, and
  explicit GREEN/AMBER/RED/BLACK states.
- Add focused tests or validation checks for the figure generator's input/output
  contract without weakening core verification tests.

## Non-goals

- No change to the Tier 1 hashing, ledger, scoring, or attack algorithms.
- No adjudication model call and no API key requirement.
- No attempt to make the figures a general-purpose charting framework.
- No claim that a screenshot alone proves ledger integrity.

## Constraints

- The project currently contains the specifications and design language but not
  the implementation modules or generated evidence artifacts; the generator must
  be added in the smallest compatible surface.
- Figure 2 must show only statuses that the offline verification/attack commands
  actually produce.
- Figure 3 must redact or avoid secrets and must use a fixture/demo ledger, never
  a user's real audit state.
- Quantitative labels in the figures must carry a source/reference in the
  generator data or caption metadata, consistent with the verification-tag rule.
- Outputs should be deterministic: same source inputs produce byte-stable content
  apart from explicitly controlled metadata.

## Approaches

### A. All figures as generated diagrams

One renderer creates architecture, terminal output, and JSON receipt from static
data. This is easy to style consistently but weakens the connection between
Figures 2–3 and the executable ledger behavior.

### B. All figures as application screenshots

The Streamlit viewer supplies every image. This maximizes product authenticity but
is sensitive to browser dimensions, fonts, and UI state, and it makes the
architecture figure less precise.

### C. Hybrid — selected

Use a deterministic vector renderer for Figure 1. Capture or render the actual
offline CLI output for Figure 2 and select a real record from a generated fixture
ledger for Figure 3. Keep a single palette/typography configuration and emit
SVG plus a report-friendly raster format. This balances visual control with
evidence provenance and is the selected approach.

## Proposed design

### Inputs

- A small architecture data structure preserving the named stages from
  [`docs/SPEC.md`](../../SPEC.md) and [`README.md`](../../README.md): retrieval,
  evidence sealing, generation, claim segmentation/adjudication, binding
  append, ledger, and reader/audit viewer.
- Output from the offline verification and attack CLI commands. The generator
  will execute the commands rather than reimplement their behavior.
- A representative binding record read from the project's shared deterministic
  fixture ledger mechanism, never from a second figure-specific ledger builder,
  containing
  `seq`, `source_hash`, `prev_hash`, `entry_hash`, claim, score, band, and
  reasons.

### Outputs

Store generated report assets under a dedicated, documented report-assets
directory, with stable names:

- `figure-1-system-architecture.svg` and a PNG companion rendered at 2x.
- `figure-2-execution-attack-detection.svg` and a PNG companion rendered at 2x.
- `figure-3-audit-receipt.svg` and a PNG companion rendered at 2x.

SVG is the authoritative output; PNG is the portable report/presentation
companion. The exact output directory is an implementation call, provided it is
git-ignored when reproducible from source or explicitly tracked when the report
requires committed assets.

### Visual treatment

- Figure 1: left-to-right flow with clear Tier 1/Tier 2/Tier 3 boundaries,
  directional arrows, and a visibly distinct cryptographic sealing/ledger path.
- Figure 2: three vertically ordered terminal panels or one terminal panel with
  three labeled scenarios; valid output is neutral/green, tampering and omission
  use the BLACK integrity-failure treatment with red warning accents only for
  attention.
- Figure 3: syntax-highlighted JSON with the chain fields visually grouped and
  a short caption identifying the receipt as a fixture-derived excerpt.
- All figures include a compact title and a provenance/caption line outside the
  main evidence area. Measured values and statuses use `[M]` and name the
  offline command that produced them; architecture/layout facts use `[D]` and
  name the source document.

### Validation

- Run the smallest figure-generation command and confirm all expected files exist.
- Run the relevant offline tests and verify that Figure 2 statuses/codes match
  the underlying command results.
- Confirm generated output contains no API keys, `.env` values, or real user
  ledger data.
- Confirm the generator does not import network-dependent adjudication modules
  when rendering Figures 2–3.

## Remaining builder calls

- Select the existing project language and dependency-free rendering mechanism
  where possible.
- Decide whether raster conversion is done during generation or as a documented
  optional export step.
- Choose the exact report-assets path and whether generated files are tracked,
  based on the repository's eventual report workflow.
