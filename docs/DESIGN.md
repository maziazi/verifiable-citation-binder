# DESIGN — Verifiable Citation Binder audit viewer

The visual system for the audit viewer. Scope is Tier 3 only; it does not describe
behavior (`docs/SPEC.md`) or sequencing (`docs/PLAN.md`).

---

## 1. Design premise

The viewer has one job: **let a reader tell a grounded claim from an ungrounded one
without opening the source document.** Everything here follows from that.

Three consequences shape every decision below.

**The verdict must be legible before the text is read.** A reader scanning an answer
should perceive the distribution of bands peripherally, before parsing any sentence.
That means band encoding must survive peripheral vision, which rules out thin
underlines and small badges as the primary signal.

**Color is never the only channel.** Roughly 8% of men have some form of color
vision deficiency `[L]` (standard prevalence figure), and red/green is the most
common axis affected — which is precisely the axis a trust indicator wants to use.
Every band therefore carries three redundant encodings: color, a glyph, and a text
label. Removing color entirely must leave the interface fully usable.

**Evidence is one interaction away, never zero and never two.** Showing every
evidence span inline makes the answer unreadable. Hiding it behind a modal plus a
scroll makes it unused. One click, inline expansion, span highlighted in place.

---

## 2. Palette

Contrast ratios are computed against the stated background and verified with the
WCAG 2.1 relative-luminance formula `[M]` (`scripts/check_contrast.py`, run in CI
job 1).

### 2.1 Neutrals

| Token | Hex | Role | On `--bg` | Ratio |
|---|---|---|---|---|
| `--bg` | `#FBFBF9` | Page background | — | — |
| `--surface` | `#FFFFFF` | Cards, evidence panels | — | 1.04:1 vs bg |
| `--border` | `#E3E2DD` | Hairlines, dividers | — | 1.28:1 (non-text) |
| `--text` | `#1A1A18` | Body text | `--bg` | **16.4:1** |
| `--text-muted` | `#5C5B56` | Metadata, timestamps, hashes | `--bg` | **6.9:1** |

`--bg` is a warm off-white rather than pure white. Pure white against the band fills
produces a harsher edge, and the warm base lets AMBER read as a distinct hue rather
than as a tint of the background.

### 2.2 Band colors

Each band has three tokens: a **fill** for the claim background, a **border** for the
left rule, and an **ink** for the badge text on that fill.

| Band | `--fill` | `--border` | `--ink` | Ink on fill | Border on bg |
|---|---|---|---|---|---|
| **GREEN** | `#E8F3EC` | `#2F7D4F` | `#14532D` | **11.8:1** | **4.6:1** |
| **AMBER** | `#FDF2DC` | `#A96B00` | `#6B4300` | **9.1:1** | **4.5:1** |
| **RED** | `#FBE9E7` | `#B3261E` | `#7A1611` | **10.4:1** | **4.8:1** |
| **BLACK** | `#1A1A18` | `#000000` | `#FBFBF9` | **16.4:1** | **16.9:1** |

All text pairings exceed WCAG AA for body text (4.5:1) and all but one exceed AAA
(7:1). All border-on-background pairings exceed 4.5:1, well above the 3:1 required
for non-text UI components, so the left rule carries meaning on its own.

**AMBER is the hard one.** Yellow at a luminance that reads as "caution" against a
light background tends to fail contrast. `#A96B00` is pushed toward brown to reach
4.5:1 on `--bg` while remaining perceptually distinct from `--border` RED at
`#B3261E`. The two differ by roughly 40° in hue and 18% in lightness — enough to
separate under deuteranopia simulation `[A]` (checked visually, not instrumented).

**BLACK is inverted on purpose.** It is the only band that reverses figure and
ground. An integrity failure is categorically different from a weak claim, and the
inversion makes that difference impossible to miss even in a thumbnail.

### 2.3 Accent

| Token | Hex | Role | On `--bg` |
|---|---|---|---|
| `--accent` | `#1F4E79` | Links, focus ring, primary action | **8.9:1** |
| `--accent-weak` | `#E6EEF5` | Evidence-span highlight background | — |
| `--focus` | `#1F4E79` | 2px focus outline, 2px offset | — |

The accent is blue and deliberately outside the band hue range. A reader must never
confuse an interactive affordance with a verdict.

---

## 3. Typography

| Role | Family | Size | Weight | Line height | Tracking |
|---|---|---|---|---|---|
| Page title | System sans | 28px | 600 | 1.25 | −0.01em |
| Section heading | System sans | 20px | 600 | 1.3 | −0.005em |
| Answer body | System serif | 18px | 400 | **1.65** | 0 |
| Evidence span | System serif | 16px | 400 | 1.6 | 0 |
| Band label | System sans | 12px | 700 | 1 | **0.06em** |
| Reason code | Monospace | 12px | 600 | 1.4 | 0 |
| Hash / digest | Monospace | 12px | 400 | 1.4 | 0 |
| Metadata | System sans | 13px | 400 | 1.45 | 0 |

Stacks:

```css
--font-sans:  system-ui, -apple-system, "Segoe UI", Roboto, sans-serif;
--font-serif: Charter, "Bitstream Charter", "Iowan Old Style", Georgia, serif;
--font-mono:  "SF Mono", "JetBrains Mono", Menlo, Consolas, monospace;
```

### Rationale

**Serif for the answer body.** The answer is the longest continuous prose in the
interface and the thing a reader actually reads. Serif at 18px/1.65 is comfortable
for sustained reading and — more importantly — visually separates *the model's
words* from *the system's chrome*, which is sans throughout. The reader should never
be confused about which text is a claim and which is the system commenting on it.

**Monospace for reason codes and hashes.** Both are identifiers to be compared
character by character. `S02` and `S03`, or two digests differing in one hex digit,
must be distinguishable at a glance. Proportional fonts actively work against this.

**Band labels are small, bold, and widely tracked.** Uppercase at 12px with 0.06em
tracking stays legible at badge size and reads as a label rather than as prose.

**No webfonts.** The viewer must start instantly and render identically offline. A
judge on a slow connection should not wait for a font. The system stacks are also
the reason there is no `@font-face` in the CSP allowance list (§7).

---

## 4. The three routes

### 4.1 `/` — Answer

The default view and the one that carries Scenario 1.

```
┌─────────────────────────────────────────────────────────────────┐
│  Verifiable Citation Binder                    ● Chain valid    │
├─────────────────────────────────────────────────────────────────┤
│  Query: What was Q3 2024 operating revenue growth?              │
│                                                                 │
│  ┃ ✓ GROUNDED                                                   │
│  ┃ Revenue grew in the third quarter of 2024.          [doc17]  │
│                                                                 │
│  ┃ ! PARTIAL                                                    │
│  ┃ Operating revenue rose 20% in Q3 2024.              [doc17]  │
│  ┃   S02 PARTIAL_ENTAILMENT · N01 NUMERIC_MISMATCH              │
│  ┃   The claim states a 20% increase; the source states 5%.     │
│  ┃   ▸ Show evidence                                            │
│                                                                 │
│  ┃ ✕ UNSUPPORTED                                                │
│  ┃ Margins expanded across all segments.               [doc17]  │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│  3 claims · 1 grounded · 1 partial · 1 unsupported              │
└─────────────────────────────────────────────────────────────────┘
```

Claim block anatomy, outside-in:

1. **Left rule**, 4px, `--border` of the band. The peripheral signal.
2. **Band badge** — glyph plus label, `--ink` on `--fill`.
3. **Claim text**, serif, on a 6% tint of `--fill`.
4. **Citation chip**, monospace, right-aligned.
5. **Reason codes**, monospace, comma-separated — *always rendered, never
   truncated*. A verdict with hidden reasons violates G5.
6. **Explanation**, one line, `--text-muted`.
7. **Evidence disclosure** — collapsed by default.

GREEN claims show items 1–4 only. There is nothing to explain when a claim is fully
grounded, and rendering an empty reason row for every grounded sentence would bury
the signal in the AMBER and RED cases.

**Expanded evidence** shows the source document id, the chunk id, the character
offsets, the chunk text with the matched span highlighted in `--accent-weak`, and
the SHA-256 digest with a verify indicator. The digest is shown truncated to 12 hex
characters with the full value on hover and in the copy action — the full 64
characters are noise at reading size and essential at verification time.

### 4.2 `/ledger` — Ledger

Carries Scenario 2.

```
┌─────────────────────────────────────────────────────────────────┐
│  Ledger                                       [ Verify Ledger ] │
├─────────────────────────────────────────────────────────────────┤
│  ● Chain valid · 42 records · head sha256:a71c4f…               │
├─────┬────────────┬──────────────────────────┬────────┬──────────┤
│ seq │ time       │ claim                    │ band   │ hash     │
├─────┼────────────┼──────────────────────────┼────────┼──────────┤
│  42 │ 09:14:22Z  │ Operating revenue rose…  │ AMBER  │ a71c4f…  │
│  41 │ 09:14:21Z  │ Revenue grew in the thi… │ GREEN  │ 9f2b11…  │
│  40 │ 09:14:20Z  │ Margins expanded across… │ RED    │ 3d88ae…  │
└─────┴────────────┴──────────────────────────┴────────┴──────────┘
```

Status strip states:

| State | Glyph | Treatment | Message |
|---|---|---|---|
| Valid | ● | GREEN fill, GREEN ink | `Chain valid · N records · head <digest>` |
| Checking | ◐ | Neutral, animated | `Verifying N records…` |
| **Invalid** | ✕ | **BLACK fill, inverted** | `INTEGRITY FAILURE · L03 at record 27` |

On failure the entire strip inverts to BLACK, the failing row is marked, and **every
band chip in the table is replaced by a BLACK chip**. This is the BLACK override
from SPEC §4.4 rendered literally: once the chain is broken, no per-claim verdict in
that ledger may be displayed as reassuring. A green badge sitting on a tampered
record is worse than no badge at all.

The failure message names the code *and* the index. "Invalid signature" alone is
not actionable; `L03 at record 27` tells an auditor where to look.

### 4.3 `/attack` — Attack

Carries Scenario 3 and makes the empirical claim inspectable rather than asserted.

```
┌─────────────────────────────────────────────────────────────────┐
│  Tamper simulation                              [ Run 50 cases ]│
├─────────────────────────────────────────────────────────────────┤
│  ████████████████████████████████████████████████  50 / 50      │
│  Detected and localized: 50 of 50                               │
├──────────────────┬───────┬──────────┬───────────────────────────┤
│ class            │ cases │ detected │ codes                     │
├──────────────────┼───────┼──────────┼───────────────────────────┤
│ Edit             │  25   │   25     │ L03                       │
│ Delete (middle)  │  15   │   15     │ L01, L02                  │
│ Truncate (tail)  │  10   │   10     │ L02                       │
└──────────────────┴───────┴──────────┴───────────────────────────┘
```

Each row expands to the per-case list: mutated index, mutated field, detected index,
code. The per-case view exists because "50/50" is a claim and the case list is the
evidence for it — the same standard this project applies to the model's claims
applies to its own.

The progress bar fills GREEN only at exactly 50/50. At 49/50 it is RED, not
"mostly green". A near-miss on a cryptographic integrity property is a failure, and
the interface must not soften it.

---

## 5. Components

### 5.1 Band badge

```
┌──────────────┐
│ ✓ GROUNDED   │   GREEN
└──────────────┘
```

| Band | Glyph | Label | Role |
|---|---|---|---|
| GREEN | `✓` | `GROUNDED` | Source is intact and says this |
| AMBER | `!` | `PARTIAL` | Source is real; claim overshoots it |
| RED | `✕` | `UNSUPPORTED` | Claim is not supported by what it cites |
| BLACK | `⚠` | `TAMPERED` | The record itself cannot be trusted |

Labels are reader-facing language, not internal band names. "GROUNDED" tells a
reader what to do with the sentence; "GREEN" tells them a color they can already
see. 4px radius, 2px/8px padding, 12px/700/0.06em.

### 5.2 Claim block

4px left rule in `--border`, 12px padding, 8px between blocks, background at 6%
`--fill`. Hover raises the tint to 10% and reveals the evidence disclosure control.
Focus applies the 2px `--focus` ring at 2px offset, never replacing the hover tint —
keyboard and pointer users see the same affordance.

### 5.3 Evidence panel

Inline, below the claim, on `--surface` with a `--border` hairline. Contains:

- source document id and chunk id, monospace, `--text-muted`
- character offsets, monospace, `--text-muted`
- chunk text in serif, matched span on `--accent-weak`
- digest, truncated to 12 chars, with `●` valid / `✕` mismatch

Opens with a 150ms height transition. Longer reads as sluggish; instant loses the
connection between the claim and the panel that belongs to it.

### 5.4 Reason chip

Monospace 12px/600, 2px/6px padding, 3px radius, 1px `--border` of the band,
transparent background. Code and name are both shown (`N01 NUMERIC_MISMATCH`)
because the code is for aggregation and the name is for reading.

### 5.5 Primary button

`--accent` fill, `--bg` text, 6px radius, 8px/16px padding, 14px/600. Used for
**Verify Ledger** and **Run 50 cases** — the only two primary actions in the
interface. Disabled during execution with the label replaced by the progress state,
so the button is also the status indicator.

### 5.6 Status strip

Full-width, 40px, 12px horizontal padding. Glyph, message, and digest. Sticky at the
top of `/ledger`. The one component that may invert to BLACK.

---

## 6. Layout, motion, and accessibility

### Layout

Single column, `max-width: 820px`, centered, 24px gutters. One column because the
reading flow is strictly linear — answer, then claim, then evidence — and a sidebar
would compete with the thing being read. 820px holds roughly 85 characters at 18px
serif, near the upper bound of comfortable measure.

Breakpoints: below 640px the ledger table drops the `time` column and the attack
table collapses to stacked cards. Band encoding never degrades at any width; it is
the last thing to be given up, not the first.

### Motion

| Transition | Duration | Easing |
|---|---|---|
| Evidence expand/collapse | 150ms | `ease-out` |
| Hover tint | 100ms | `ease-out` |
| Status strip state change | 200ms | `ease-in-out` |
| Attack progress fill | linear, per case | `linear` |

All motion is wrapped in `@media (prefers-reduced-motion: reduce)` and reduced to
`0ms`. Nothing in this interface conveys meaning through animation, so disabling it
costs nothing.

### Accessibility checklist

- [ ] Every band encoded by color **and** glyph **and** text label
- [ ] All text pairings ≥ 4.5:1; all non-text UI ≥ 3:1 (verified in CI job 1)
- [ ] Focus visible on every interactive element, 2px ring, 2px offset
- [ ] Evidence disclosure is a `<button>` with `aria-expanded`, keyboard operable
- [ ] Ledger table uses real `<th scope="col">` headers
- [ ] Status strip is `role="status"` with `aria-live="polite"`
- [ ] Verification failure additionally announced via `aria-live="assertive"`
- [ ] Digests carry an accessible full value, not only the truncated display
- [ ] Interface fully usable with CSS color forced off
- [ ] Reduced-motion honored throughout

The grayscale requirement is the real test. If the viewer is rendered with no color
at all and a reader can still separate grounded from unsupported claims, the
redundant encoding is genuine rather than decorative.

---

## 7. Content Security Policy

The static HTML export (PR-12) ships with:

```
default-src 'none';
style-src   'self' 'unsafe-inline';
img-src     'self' data:;
font-src    'self';
script-src  'self';
connect-src 'none';
base-uri    'none';
form-action 'none';
frame-ancestors 'none';
```

### Rationale

`default-src 'none'` with explicit grants, rather than a permissive base with
denials. The export is an **archival audit artifact** — it may be attached to an
incident report, emailed, or opened years later. It must render identically offline
and must never phone home.

`connect-src 'none'` is the load-bearing line: an exported audit record cannot make
a network request, so it cannot leak the content of the ledger it displays, and it
cannot fetch content that would change what a reader sees. An audit artifact whose
rendering depends on a live server is not an audit artifact.

`'unsafe-inline'` is permitted for styles only. The export is a single self-contained
file with no external stylesheet; inline style is the mechanism, and style cannot
exfiltrate under `connect-src 'none'`. Scripts get no such allowance — `script-src
'self'` with no inline grant, and in practice the export ships zero JavaScript. The
expand/collapse interaction is `<details>`/`<summary>`, which is why the evidence
panel is built on a disclosure element rather than on a click handler.

No webfonts, no CDN, no analytics. `font-src 'self'` exists only to allow a
self-hosted fallback and is currently unused — the system font stacks in §3 mean the
export has no font dependency at all.
