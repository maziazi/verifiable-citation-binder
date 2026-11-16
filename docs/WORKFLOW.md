# WORKFLOW — Verifiable Citation Binder

How the work is sequenced, why in that order, what each PR contains, and what CI
enforces. `docs/PLAN.md` says *what* and *when*; this document says *how*.

---

## Table of contents

1. [Development order and its rationale](#1-development-order-and-its-rationale)
2. [The 16-PR map](#2-the-16-pr-map)
3. [Dependency graph](#3-dependency-graph)
4. [Branch and PR conventions](#4-branch-and-pr-conventions)
5. [Commit conventions](#5-commit-conventions)
6. [CI — eight jobs](#6-ci--eight-jobs)
7. [CD — release and deploy](#7-cd--release-and-deploy)
8. [Definition of done](#8-definition-of-done)
9. [Running under the 120-minute budget](#9-running-under-the-120-minute-budget)

---

## 1. Development order and its rationale

The order is not arbitrary and it is not "easiest first". It is derived from three
properties of the project.

### Property 1 — the provable part must exist before the probabilistic part

Tier 1 (hashing, chaining, verification) is deterministic and offline. Tier 2
(adjudication) depends on a model and is probabilistic. If Tier 2 is built first,
every subsequent integrity bug is debugged through a non-deterministic layer, and
every integrity test needs an API key.

Building Tier 1 first means:

- Integrity tests are fast, offline unit tests from PR-02 onward.
- The attack simulation — the strongest single claim in the submission — is
  complete and provable before any model has been called.
- A reviewer can validate half the system without credentials.

**Consequence:** PR-01 through PR-05 touch no model and need no API key.

### Property 2 — the attack simulation is the schema's acceptance test

The tamper simulation does not merely test the verifier. It tests the *record
schema* and the *canonical serialization* — the two things that are expensive to
change later because every committed fixture ledger depends on them.

Running the attack simulation at PR-04, before the record schema is used anywhere
else, surfaces serialization bugs while exactly one module depends on them. The
same bug found after the viewer, the corpus, and the eval harness are built costs
a regeneration of every fixture.

**Consequence:** PR-04 (attack) comes before PR-06 (retrieval), not after.

### Property 3 — the demo path is an integration risk, not a feature risk

Each piece works in isolation long before they work together. The classic failure
is three green test suites and a demo that does not run.

**Consequence:** PR-09 is a deliberately thin end-to-end walking skeleton —
retrieve → segment → adjudicate → bind → print — built *before* the viewer, the
evaluation harness, or the polish. From PR-09 onward, `uv run vcb demo` must work
on every merge to `main`. CI enforces this (job 6).

### Resulting phases

| Phase | PRs | Depends on a model? | What exists at the end |
|---|---|---|---|
| **A — Foundation** | 01–05 | No | A provable, offline integrity layer with a passing 50-case attack suite |
| **B — Adjudication** | 06–09 | Yes | A working end-to-end pipeline that produces real ledgers |
| **C — Surface** | 10–12 | Yes | The three demo scenarios, runnable by a judge |
| **D — Evidence** | 13–16 | Yes | Measured results, report, CI/CD, release |

---

## 2. The 16-PR map

Each PR is one capability. Each adds tests. Each merges green.

### Phase A — Foundation (offline, no API key)

**PR-01 — `chore: project skeleton`**
Package layout (`src/vcb/{core,adjudicate,surface}`), `pyproject.toml`, `vcb` CLI
entry point with stub subcommands, `.gitignore`, `.env.example`, ruff + mypy config.
*Done when:* `uv run vcb --help` lists `demo`, `verify`, `attack`, `eval`.
*Tests:* CLI smoke test.

**PR-02 — `feat(core): canonical serialization and digest`**
`canonicalize()`, `digest()`, the normative serialization rules from SPEC §7.2.
*Done when:* serialization is stable across key order, whitespace, and Unicode form.
*Tests:* property tests — key permutation invariance, NFC idempotence,
`record_hash` exclusion from its own preimage.

**PR-03 — `feat(core): binding record model and append`**
`EvidenceRef`, `Claim`, `PillarScores`, `Reason`, `BindingRecord`, `Ledger`;
`append()` with `seq`, `prev_hash`, genesis constant, sidecar head write.
*Done when:* appending N records produces a chain whose links recompute.
*Tests:* chain construction for N ∈ {0, 1, 2, 50}.

**PR-04 — `feat(core): chain verification with failure localization`**
`verify()` returning `VerificationResult` with `first_failure_index` and typed
`L01`/`L02`/`L03` failures, including the sidecar truncation check.
*Done when:* a hand-corrupted fixture reports the correct index and code.
*Tests:* one test per failure class, each asserting the index.

**PR-05 — `feat(core): tamper simulation`**
The 50-case suite: 25 edits, 15 middle deletions, 10 tail truncations, seeded.
`vcb attack` CLI wiring. Writes `results/attack.json`.
*Done when:* 50/50 detected **and** 50/50 correctly localized.
*Tests:* the simulation itself, asserted at 50/50 — a hard CI gate (job 5).

### Phase B — Adjudication

**PR-06 — `feat(adjudicate): corpus loading, chunking, retrieval`**
Document loader, chunker with stable offsets, in-memory embedding index,
`retrieve(query, k)` returning hashed `EvidenceRef`s.
*Done when:* retrieval returns the planted evidence for every corpus query.
*Tests:* retrieval hit-rate on the fixture corpus; chunk offsets round-trip.

**PR-07 — `feat(adjudicate): claim segmentation`**
`segment(answer)` → `list[Claim]`, citation-marker parsing, assertive-sentence
detection, known-limitation handling for abbreviations.
*Done when:* 10 hand-labelled answers segment correctly.
*Tests:* golden-file segmentation tests.

**PR-08 — `feat(adjudicate): model adjudication with strict parsing`**
Adjudication prompt, Claude Haiku 4.5 call, structured response parsing against the
closed 18-code enum, one retry, `adjudication_failed` fallback, response cache.
*Done when:* an unknown reason code raises rather than passing through.
*Tests:* parser tests on recorded fixtures (offline); one `live`-marked test.

**PR-09 — `feat: end-to-end walking skeleton`**
`vcb demo`: retrieve → segment → adjudicate → score → append → print. Thin by
design; no viewer, no formatting.
*Done when:* one command produces a valid ledger that `vcb verify` accepts.
*Tests:* end-to-end test against the cached adjudication fixtures — **offline**.

### Phase C — Surface

**PR-10 — `feat(core): four-pillar scoring and bands`**
`compose()`, `band_of()`, the BLACK override, the specificity penalty table.
*Done when:* the SPEC §4.5 worked example reproduces exactly 70 / AMBER.
*Tests:* a table-driven test per band boundary; the worked example as a fixture.

**PR-11 — `feat(surface): audit viewer`**
Streamlit app, three routes (Answer / Ledger / Attack), per-claim bands, evidence
expansion, the **Verify Ledger** button. Applies `docs/DESIGN.md`.
*Done when:* all three demo scenarios are reachable in under 30 seconds each.
*Tests:* smoke test that each route renders without raising.

**PR-12 — `feat(surface): exporters`**
`results/` JSON writers and a static HTML audit export for archival.
*Done when:* the exported HTML renders the same bands as the live viewer.
*Tests:* round-trip export/parse.

### Phase D — Evidence

**PR-13 — `feat: synthetic evaluation corpus`**
100 labelled items spanning supported, partially-supported, numerically-wrong,
entity-swapped, and unsupported claims. Generator script plus committed output.
*Done when:* label distribution is printed and balanced; the canonical AMBER case
is present.
*Tests:* schema validation; distribution assertion.

**PR-14 — `feat: evaluation harness`**
Arm A (bare RAG) vs Arm B (RAG + VCB), E1–E4 metric computation, cost accounting
from real `usage`, writes `results/metrics.json` and `results/cost.json`.
*Done when:* both arms run and metrics are written with per-case breakdowns.
*Tests:* metric functions tested on synthetic confusion matrices.

**PR-15 — `ci: pipeline`**
The eight CI jobs (§6) plus the CD workflow (§7).
*Done when:* all eight jobs green on a PR.
*Tests:* CI is the test.

**PR-16 — `docs: submission package`**
README numbers tagged per the SPEC §9 legend, report figures generated from
`results/`, error analysis, release notes, `v0.1.0` tag.
*Done when:* every number in the README carries a tag and every `[M]` names its
command.
*Tests:* a docs linter that fails on an untagged numeral in README/SPEC.

---

## 3. Dependency graph

```
PR-01 skeleton
  └─► PR-02 serialization
        └─► PR-03 record + append
              └─► PR-04 verify
                    └─► PR-05 attack ──────────────────┐
                                                       │
PR-01 ──► PR-06 retrieval                              │
            └─► PR-07 segmentation                     │
                  └─► PR-08 adjudication               │
                        └─► PR-09 walking skeleton ◄── PR-03
                              │                        │
                              ├─► PR-10 scoring ◄── PR-03
                              │     └─► PR-11 viewer ◄─┤  (attack route)
                              │           └─► PR-12 exporters
                              │
                              └─► PR-13 corpus
                                    └─► PR-14 evaluation
                                          └─► PR-16 submission
PR-01 ──► PR-15 CI ──────────────────────────────────► PR-16
```

Critical path: **01 → 02 → 03 → 04 → 05**. Everything downstream can slip; this
chain cannot, because PR-05 is the hard checkpoint in `docs/PLAN.md` §2.

Parallelizable once PR-03 lands: the `06 → 07 → 08` chain and the `13` corpus work
are independent of `04 → 05`.

---

## 4. Branch and PR conventions

### Branch naming

```
<type>/pr-<nn>-<slug>

feat/pr-05-tamper-simulation
fix/pr-11-black-override-not-applied
docs/pr-16-tag-readme-numbers
```

### Rules

1. **Never commit to `main`.** `main` is protected; merges arrive only via PR.
2. **One PR, one capability.** If the PR description needs "and", split it.
3. **No branch outlives its milestone.** Under a two-hour budget, a long-lived
   branch is an unmerged rewrite.
4. **Every PR adds or extends tests.** A PR with no test delta needs an explicit
   justification in the description.
5. **Squash on merge.** One commit per PR on `main`; the history reads as the
   16-PR map.
6. **Tier 1 diffs are read line by line.** `src/vcb/core/` is ~400 lines total;
   this is affordable and non-negotiable (`docs/PLAN.md` §5).

### PR description template

```markdown
## What
One sentence.

## Why
Which PLAN milestone and which SPEC section this implements.

## Verification
The exact command a reviewer runs, and the expected output.

## Claims
Any number this PR introduces into docs, with its tag ([M]/[D]/[L]/[A]/[F]).
```

The **Claims** section is why the legend survives contact with time pressure. It is
cheap at PR time and expensive to retrofit.

---

## 5. Commit conventions

Conventional Commits, enforced by CI (job 8).

```
<type>(<scope>): <subject>

[optional body]
[optional footer]
```

### Types

| Type | Use for |
|---|---|
| `feat` | New capability |
| `fix` | Bug fix |
| `docs` | Documentation only |
| `test` | Tests only |
| `refactor` | Behavior-preserving restructuring |
| `perf` | Performance |
| `ci` | CI/CD configuration |
| `chore` | Tooling, dependencies, scaffolding |

### Scopes

`core`, `adjudicate`, `surface`, `corpus`, `eval`, `docs`, `ci`

### Examples

```
feat(core): add sidecar head check for tail truncation
fix(core): exclude record_hash from its own preimage
test(core): assert localization index on all 50 attack cases
docs: tag every README number per the SPEC §9 legend
refactor(adjudicate): invert Tier-1 dependency in the cache key
```

### Rules

- Subject in imperative mood, lower case, no trailing period, ≤72 characters.
- Body explains *why*, not *what* — the diff already says what.
- Breaking changes use `!` and a `BREAKING CHANGE:` footer. Any change to canonical
  serialization is breaking, because it invalidates every committed ledger.

---

## 6. CI — eight jobs

`.github/workflows/ci.yml`, triggered on every push and PR. Jobs 1–5 are
**offline** — they require no API key and no network beyond installing packages.

| # | Job | Runs | Fails on | Offline |
|---|---|---|---|---|
| 1 | **lint** | `ruff check .` and `ruff format --check .` | Any lint or format violation | ✅ |
| 2 | **typecheck** | `mypy src/` | Any type error in `src/` | ✅ |
| 3 | **test-core** | `pytest tests/core -m "not live"` | Any Tier-1 test failure | ✅ |
| 4 | **architecture** | `lint-imports` contract check | `core/` importing from `adjudicate/` or `surface/`, or any network import in `core/` | ✅ |
| 5 | **attack** | `vcb attack --assert 50/50` | Fewer than 50 detected, or any detection not correctly localized | ✅ |
| 6 | **demo** | `vcb demo --offline` against cached fixtures | The end-to-end path raising, or producing a ledger that fails `verify` | ✅ |
| 7 | **test-full** | `pytest` including `live`-marked tests | Any test failure; skipped on forks with no secret | ❌ |
| 8 | **conventions** | commitlint on the PR title and commits; docs linter for untagged numerals | A non-conforming commit, or an untagged number in README/SPEC | ✅ |

### Why job 4 exists

The Tier-1 purity rule (SPEC §5.2) is the foundation of every reproducibility claim
in the submission. A rule enforced only by code review is a rule that breaks at
minute 100 under time pressure. The import contract makes it mechanical:

```toml
[[tool.importlinter.contracts]]
name = "Tier 1 is independent"
type = "forbidden"
source_modules = ["vcb.core"]
forbidden_modules = ["vcb.adjudicate", "vcb.surface", "anthropic", "httpx", "requests"]
```

### Why job 5 is separate from job 3

Job 3 is "the unit tests pass". Job 5 is "the central empirical claim of the
submission still holds". They fail differently and they mean different things. A
reviewer reading the CI badge list should see the attack gate by name.

### Why job 8 lints documentation

The claim-verification legend (SPEC §9) is the main defense against overclaiming,
and it is exactly the kind of discipline that erodes at the deadline. A linter that
flags a bare numeral in `README.md` costs seconds and preserves it.

### Matrix

Jobs 1–6 run on `ubuntu-latest` with Python 3.11 and 3.12. The dual version is not
ceremony: canonical serialization must be stable across interpreter versions, and
that is a correctness property of G3.

---

## 7. CD — release and deploy

`.github/workflows/cd.yml`.

### Trigger

Push of a tag matching `v*.*.*`.

### Stages

**1 — Gate.** Re-run CI jobs 1–6 on the tagged commit. The release does not trust
an earlier green run on a different tree.

**2 — Artifacts.** Build:
- the Python wheel and sdist
- `audit_ledger.json` — a freshly generated, sealed example ledger
- `results/` — `metrics.json`, `cost.json`, `attack.json`
- the static HTML audit export
- the report PDF

**3 — Verify artifacts.** The pipeline runs `vcb verify` against the freshly
generated `audit_ledger.json` *in a clean container with no API key*. A release
whose own example ledger does not verify is blocked. This is the CD equivalent of
the submission's core claim.

**4 — Release.** Create the GitHub release, attach every artifact, generate notes
from the Conventional Commits since the previous tag.

**5 — Deploy viewer.** Deploy the Streamlit app to Streamlit Community Cloud from
the tag. Secrets are injected from repository secrets; **no key is ever written to
the repository or baked into an artifact.**

**6 — Post-deploy smoke.** Hit the deployed `/ledger` route and assert the chain
status renders as valid. Failure here rolls back to the previous deployment and
leaves the GitHub release intact — a broken demo should not retract a valid release.

### Secrets

| Secret | Used by | Never |
|---|---|---|
| `ANTHROPIC_API_KEY` | CI job 7, CD stage 2 | In the repo, in a log, in an artifact, in a committed ledger |
| `STREAMLIT_DEPLOY_TOKEN` | CD stage 5 | Anywhere else |

Forked PRs do not receive secrets. Job 7 is skipped on forks; jobs 1–6 still run and
are sufficient to validate every integrity claim. This is a direct, practical
benefit of the Tier-1 purity rule.

---

## 8. Definition of done

A PR is done when **all** of these hold:

- [ ] All eight CI jobs green
- [ ] Tests added or extended, and they fail without the change
- [ ] If Tier 1 was touched: the diff was read line by line
- [ ] If a number entered any document: it carries a tag, and `[M]` names its command
- [ ] If the record schema or serialization changed: fixtures regenerated, and the
      commit is marked breaking
- [ ] PR description filled in, including the Claims section
- [ ] `uv run vcb demo` still works (from PR-09 onward)

---

## 9. Running under the 120-minute budget

The 16-PR map is the structure. Under a two-hour agent-driven budget it is executed
in **five batches**, each batch opening one branch and one PR.

| Batch | PRs | Milestones | Minutes |
|---|---|---|---|
| B1 | PR-01 … PR-05 | M1–M3 | 0–45 |
| B2 | PR-06 … PR-09 | M4–M5 | 45–80 |
| B3 | PR-10 … PR-12 | M6–M7 | 80–105 |
| B4 | PR-13 … PR-14 | M8 | 105–115 |
| B5 | PR-15 … PR-16 | M9 | 115–120 |

Batching changes the review granularity, not the structure: the PR boundaries
survive as commits inside the batch, so the history still reads as the 16-PR map
and each capability remains individually revertible.

**What batching does not relax:**

- Tier 1 is still read line by line (B1 and the PR-10 portion of B3).
- The attack gate is still 50/50, still at the 45-minute checkpoint.
- Every number is still tagged at the moment it is written.
- CI jobs 1–6 still gate every batch merge.

**What batching does relax:** per-PR descriptions collapse into one batch
description, and the branch-per-PR rule becomes branch-per-batch. Both are
bookkeeping, and bookkeeping is the correct thing to trade when the alternative is
trading verification.
