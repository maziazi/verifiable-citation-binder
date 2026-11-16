# Verifiable Citation Binder

**A citation that cannot be checked is decoration. A log that can be edited is not
evidence.**

VCB is a middleware layer for retrieval-augmented generation that does two things:
it binds every claim in an answer to the evidence that claim cites, and it seals the
record of that binding in a hash-chained, append-only ledger.

Built for the Apart Research hackathon. Research artifact, not a product.

> **Claim discipline.** Every number below carries a tag: `[M]` measured,
> `[D]` derived, `[L]` literature, `[A]` assumption, `[F]` future work.
> Each `[M]` names the command that produces it. The legend is
> [`docs/SPEC.md` §9](docs/SPEC.md#9-claim-verification-legend).
> Where results are not yet measured, this README says so rather than estimating.

---

## The problem

### Decorative citations

RAG systems attach citations to their answers. Often the cited source is real, was
genuinely retrieved, and does not support the sentence it is attached to. The
citation functions as a trust signal rather than as evidence.

The reader cannot tell the difference without opening the source — which means the
cost of verification falls entirely on the person least equipped to pay it. The
system that produced the claim had the evidence in memory microseconds earlier.

### Unaccountable logs

When an agentic system makes a consequential mistake, the investigation depends on
its activity log. That log is an ordinary file, held by the operator of the system —
the party with the strongest interest in its contents. An entry can be edited. An
entry can be deleted. Neither leaves a trace in a plain file.

"Append-only by convention" is not append-only.

These two failures compose: a system can cite decoratively, be wrong, and then erase
the record of having been wrong.

---

## How it works

```
  query
    │
    ▼
┌──────────────┐     ┌─────────────────────────────────────────┐
│  Retrieval   │────►│ 1. Seal evidence                        │
└──────────────┘     │    SHA-256 each retrieved chunk at      │
    │                │    retrieval time                       │
    ▼                └─────────────────────────────────────────┘
┌──────────────┐     ┌─────────────────────────────────────────┐
│  Generation  │────►│ 2. Segment into claims                  │
└──────────────┘     │    one assertive sentence = one claim   │
    │                └─────────────────────────────────────────┘
    ▼                ┌─────────────────────────────────────────┐
┌──────────────┐     │ 3. Adjudicate each claim                │
│     VCB      │────►│    4 pillars → score 0–100 + reasons[]  │
└──────────────┘     └─────────────────────────────────────────┘
    │                ┌─────────────────────────────────────────┐
    ▼                │ 4. Append binding record                │
┌──────────────┐     │    prev_hash + seq → tamper-evident     │
│  audit_      │◄────│                                         │
│  ledger.json │     └─────────────────────────────────────────┘
└──────────────┘     ┌─────────────────────────────────────────┐
    │                │ 5. Band the result                      │
    ▼                │    GREEN / AMBER / RED / BLACK          │
  reader ◄───────────└─────────────────────────────────────────┘
```

Step 1 happens *before* generation, which is what makes step 4 meaningful: the
evidence fingerprint predates the answer, so the answer cannot have been written to
fit a retroactively edited source.

---

## Two axes, not one

Most work in this space picks a side. The claim here is that neither side is
sufficient alone, and that the combination is cheap.

### Axis 1 — Semantic binding (probabilistic)

Does the cited evidence actually support the claim? Four pillars, measured
independently:

| Pillar | Weight | Question |
|---|---|---|
| **Support** | 0.40 | Does the evidence entail the claim? |
| **Specificity** | 0.25 | Do the numbers, dates, and entities match? |
| **Coverage** | 0.20 | How much of the claim does the evidence address? |
| **Provenance** | 0.15 | Is the cited chunk hash-valid and actually retrieved? |

Specificity exists because entailment judgments are lenient about magnitude.
"Revenue rose 20%" and "revenue rose" are both loosely "supported" by a source
saying 5% — but only one of them is a usable sentence. Separating the pillars is
what lets the system say *which* part failed.

### Axis 2 — Record integrity (cryptographic)

Can the record of that judgment be altered afterwards? Each binding record carries
`prev_hash` and a monotonic `seq`. An edit breaks the hash. A deletion breaks both
the hash chain and the sequence. A tail truncation — the attack with the clearest
motive, since it erases the most recent actions — is caught by the sequence check
plus a sidecar head commitment.

**The two axes have opposite cost and opposite certainty.** Axis 1 costs money per
claim and is probabilistic. Axis 2 is **free** `[D]` — local SHA-256, no model call —
and is provable. A system with only axis 1 can be quietly rewritten; a system with
only axis 2 seals a judgment nobody checked.

---

## Example response

Query: *What was Q3 2024 operating revenue growth?*

```
✓ GROUNDED
  Revenue grew in the third quarter of 2024.                    [doc17#c4]

! PARTIAL                                                       [doc17#c4]
  Operating revenue rose 20% in Q3 2024.
    S02 PARTIAL_ENTAILMENT · N01 NUMERIC_MISMATCH
    The claim states a 20% increase; the cited span states 5%.

    ▾ Evidence  doc17#c4  chars 1840–1976  sha256:4e0a2f… ●
      "Operating revenue increased by 5 percent during the
       third quarter of 2024."

✕ UNSUPPORTED                                                   [doc17#c9]
  Margins expanded across all segments.
    S03 NO_OVERLAP · N05 QUANTIFIER_INFLATION
    The cited span discusses revenue, not margins, and makes no
    claim about all segments.

─────────────────────────────────────────────────────────────────
3 claims · 1 grounded · 1 partial · 1 unsupported
Chain valid · 42 records · head sha256:a71c4f…
```

The AMBER case is the one worth sitting with. The citation is real. The source was
genuinely retrieved. The direction of the claim is correct. The number is wrong by a
factor of four. A reader skimming citation markers sees three sourced sentences; a
reader using VCB sees one sentence that needs checking and one that is not supported
at all.

Scoring for that claim: `0.40(55) + 0.25(50) + 0.20(100) + 0.15(100) = 69.5 → 70`
→ AMBER. Full worked example in [`docs/SPEC.md` §4.5](docs/SPEC.md).

---

## Quickstart

```bash
git clone https://github.com/maziazi/verifiable-citation-binder
cd verifiable-citation-binder
uv sync                        # or: pip install -e ".[dev]"
```

### Verify the sealed ledger — no API key required

```bash
uv run vcb verify audit_ledger.json
```

Then break it on purpose:

```bash
# Scenario 2 — edit one character anywhere in the file, then:
uv run vcb verify audit_ledger.json
#   ✕ INTEGRITY FAILURE · L03 SIGNATURE_INVALID at record 27

# Scenario 3 — delete one record from the middle, then:
uv run vcb verify audit_ledger.json
#   ✕ INTEGRITY FAILURE · L01 CHAIN_BREAK, L02 SEQUENCE_GAP at record 18
```

### Run the full tamper simulation — no API key required

```bash
uv run vcb attack audit_ledger.json
# 25 edits · 15 middle deletions · 10 tail truncations
```

### Run the pipeline and the viewer — API key required

```bash
export ANTHROPIC_API_KEY=sk-ant-...
uv run vcb demo
uv run streamlit run app.py
```

**Half of this system is verifiable with no credentials and no network.** That is a
deliberate architectural property, not a convenience: the cryptographic guarantees
live in a tier that cannot import a network client, and CI enforces it
([`docs/WORKFLOW.md` §6](docs/WORKFLOW.md), job 4).

---

## Results

Measured values are written by the evaluation harness into `results/` and are
committed. **Until the harness has run, this section states the measurement plan,
not results.** An empty cell is an honest cell.

| # | Metric | Value | Tag | Command |
|---|---|---|---|---|
| E1 | Detection precision | *pending* | `[M]` | `uv run vcb eval` → `results/metrics.json` |
| E2 | Detection recall | *pending* | `[M]` | `uv run vcb eval` → `results/metrics.json` |
| E3 | Tamper detection + localization | *pending* | `[M]` | `uv run vcb attack` → `results/attack.json` |
| E4 | Reason coverage | *pending* | `[M]` | `uv run vcb eval` → `results/metrics.json` |
| — | Cost per adjudicated claim | *pending* | `[M]` | `uv run vcb eval` → `results/cost.json` |

**E1 and E2 are reported, not targeted.** Setting a precision goal in advance and
then meeting it is how a project becomes a demonstration of its own test set. The
useful artifact is the measured number together with the error analysis of what it
missed.

**E3 and E4 are hard gates.** Both are deterministic properties of the
implementation: 50/50 detected *and* localized, and 100% of scored claims carrying a
valid reason code. Missing either is a bug, not a result. CI fails on anything less
([`docs/WORKFLOW.md` §6](docs/WORKFLOW.md), job 5).

### Cost

| Item | Estimate | Tag |
|---|---|---|
| Per adjudicated claim | ≈ $0.0024 | `[D]` from Claude Haiku 4.5 pricing `[L]` |
| Per answer (≈6 claims) | ≈ $0.015 | `[D]` |
| Integrity layer (hashing, chaining, verification) | **$0.00** | `[D]` |

The strongest economic point in the design: the half of the system that is
cryptographically provable is also the half that is free. Derivation in
[`docs/SPEC.md` §10](docs/SPEC.md).

---

## Verification table

What a reviewer can check, and how.

| Claim | How to verify | Needs a key? |
|---|---|---|
| Editing a record is detected | Edit `audit_ledger.json`, run `vcb verify` | No |
| Deleting a record is detected | Delete a middle record, run `vcb verify` | No |
| Truncating the tail is detected | Delete the last record, run `vcb verify` | No |
| Mutating a source document is detected | Edit a file in `corpus/`, run `vcb verify` | No |
| Detection localizes the failure | Compare the reported index to the one you broke | No |
| All 50 attack cases are caught | `uv run vcb attack` | No |
| Tier 1 performs no network I/O | `uv run lint-imports` (CI job 4) | No |
| Scoring is deterministic | Run `vcb eval` twice; diff `results/metrics.json` | Cached |
| The worked example scores 70 / AMBER | `uv run pytest -k worked_example` | No |
| Every claim carries a reason code | `uv run vcb eval`; E4 must be 100% | Cached |
| Adjudication quality (E1, E2) | `uv run vcb eval` against `corpus/` | **Yes** |
| Cost per claim | `uv run vcb eval`; read `results/cost.json` | **Yes** |

Ten of twelve rows are checkable offline. That ratio is the point.

---

## What this does *not* do

Stated up front, because a limitation a reader discovers themselves discounts
everything else.

1. **It verifies attribution, not truth.** A claim faithfully grounded in a false
   document scores GREEN. VCB measures claim ↔ cited-evidence, never claim ↔ reality.
2. **A wholesale ledger replacement is not detected.** A self-consistent forged
   chain is indistinguishable from an authentic one. Closing this needs an external
   commitment — a timestamping service or a transparency log. `[F]`
3. **Bypass is not detected.** VCB records what is submitted to it. An answer served
   around the binder leaves no trace, and absence of a record is invisible from
   inside the ledger. `[F]`
4. **The adjudicator is the trust anchor for 85% of the score weight.** Pillars 1–3
   rest on a model's judgment, and its stated reason is a claim about its reasoning,
   not a proof of it.
5. **The evaluation corpus is synthetic.** Authored for this project with clean
   ground-truth labels. Results **do not** transfer to AVeriTeC, RAGTruth, or
   production traffic without re-measurement. The loader interface exists; it is
   unexercised. `[F]`
6. **The pillar weights are untuned.** `[A]` No sweep was run. Different weights
   move the band boundaries and therefore every number in the results table.
7. **Prompt injection through retrieved content is only partially mitigated.**
   Provenance is computed outside the model, so a hash cannot be forged — but
   pillars 1–3 read attacker-influenceable text and no injection test suite exists.

Full list, with threat model: [`docs/SPEC.md` §8 and §11](docs/SPEC.md).

---

## Why this matters for AI safety

**It inverts who pays for verification.** Today the reader checks, or more often
does not. VCB moves the cost to the system that already has the evidence in hand,
and makes the result machine-readable — which means it can be aggregated, monitored,
and regressed against, not just read.

**It makes auditability a property rather than a promise.** Regulatory frameworks
increasingly require AI systems to be auditable after an incident. An audit log held
by the party being audited is not evidence. A hash chain is checkable by anyone who
has the file, with no trust in the operator and no secret.

**It is foundational for autonomous agents.** An agent that sends email, moves
money, or edits code needs a forensic trail that survives the agent's own incentive
to prune it. The ledger here is small and cheap, and it costs nothing per record —
which is the only way a safety mechanism actually gets deployed at scale.

---

## Repository

| Path | Contents |
|---|---|
| [`AGENTS.md`](AGENTS.md) | Entry point and working rules for contributors and agents |
| [`docs/PLAN.md`](docs/PLAN.md) | Scope, milestones, success criteria, cut scope |
| [`docs/SPEC.md`](docs/SPEC.md) | Guarantees, scoring, architecture, taxonomy, threat model |
| [`docs/WORKFLOW.md`](docs/WORKFLOW.md) | Development order, 16-PR map, CI/CD |
| [`docs/DESIGN.md`](docs/DESIGN.md) | Visual system for the audit viewer |
| `src/vcb/core/` | Tier 1 — pure, deterministic, offline |
| `src/vcb/adjudicate/` | Tier 2 — retrieval and claim adjudication |
| `src/vcb/surface/` | Tier 3 — CLI, viewer, exporters |
| `corpus/` | Synthetic evaluation corpus with ground-truth labels |
| `results/` | Generated metrics, cost accounting, attack results |

---

## License

[PolyForm Noncommercial License 1.0.0](LICENSE.md).

The source is public and you may read it, run it, modify it, and share it for
research, teaching, and personal use. **Commercial use is not permitted.** If you
want a commercial license, open an issue.

This is a deliberate choice for a research artifact: open enough that every claim in
this README is independently checkable, closed enough that the work is not simply
absorbed into a product.

---

## Citation

```bibtex
@software{vcb2026,
  title  = {Verifiable Citation Binder: Cryptographically Sealed
            Claim-Evidence Binding for Retrieval-Augmented Generation},
  author = {Muhamad Azis},
  year   = {2026},
  url    = {https://github.com/maziazi/verifiable-citation-binder}
}
```
