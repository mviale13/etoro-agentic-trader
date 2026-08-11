# Investor Assessment

**Status: accepted, built, decision-neutral.** The layer between a
committee judgment and an eventual recommendation.

It asks one question of whatever is held:

> What is the strongest useful statement MOVRvest can responsibly make
> from the information available?

---

## 1. Why it was earned

PR #116 made independent committee judgments visible and, in doing so,
showed internal epistemic vocabulary leaking to the surface *as though
it were an investment conclusion*. It is not one. `CONFLICTED` is a fact
about two readings; *"we cannot tell you anything"* is a fact about the
investor's question, and they are different sentences.

Three layers now stay separate:

```text
evidence     what was observed — every reading, with provenance,
             including readings that disagree
judgment     what the owning committee concluded about its own remit,
             in its own vocabulary
assessment   what is useful to tell an investor, given all of it
```

Only the third is allowed to decide that a disagreement does not matter.

---

## 2. The measurement, before the type

**The ETH forcing case.** Its Supply Governance judgment is
`evidence_insufficient`, and that is correct *for that committee's
remit*. What is held about ETH is not nothing:

- three circulating estimates agreeing to 0.00% — a precise figure
- an emitted total from CoinGecko
- Fee Capture answering `mechanism_evidenced`, whose own reason names
  the mechanism: *"amount of ETH burned — base fees plus blob fees"*
- **no maximum-supply figure at all**

So the useful statement is much stronger than the committee's state, and
the assessment now says all four things — including naming the maximum
as a subject it is silent about.

**One mismatch found and not papered over.** The ruling's illustrative
example was that ETH "has no fixed maximum supply". **That is not
currently supportable from stored evidence.** The CoinGecko adapter maps
a null `max_supply` to `None`, so *the vendor states there is no cap* and
*the field was absent* are indistinguishable in the store. S5.1 research
found a `max_supply_infinite` flag and it was never acquired. The
assessment therefore reports the maximum as unknown rather than as
absent-by-design, and closing that gap is an acquisition question.

**The HYPE forcing case.** Fee Capture became `execution_unavailable`
because the drafted sentence used the word *buy* and the validator
refused the draft. Reading the flow showed the boundary precisely: the
verdict is checked against the committee's vocabulary and every ref
against the supplied evidence — **the structural judgment is complete**
— and only then is the prose inspected. A prose failure was discarding a
finished analysis.

**Where disagreement actually lives.** Measured across the corpus:

| asset | spread | what it is |
|---|---:|---|
| TAO | 9.9% | two credible circulating estimates |
| ADA | 2.2% | two credible circulating estimates |
| ADA | 13.8% | a max/emitted substitution |
| HYPE | 77.6% | one reading exceeds the protocol maximum |
| ARB | 80.7% | one vendor frozen at the TGE float |

Two of these bound an answer; three do not. The evidence layer already
draws that line with `Comparison.CORROBORATED` / `COEXIST` /
`CONFLICTED`, so this layer reads it rather than forming a second
opinion about the same numbers.

---

## 3. The type the measurement produced

`StatementShape` — **six, and not ordered**. Each was observed in the
live corpus before it was declared:

```text
PRECISE       Maximum supply is 21.00 million, agreed by 2 sources
RANGE         Circulating supply is approximately 8.64 to 9.60 million
              across 2 available estimates
STRUCTURAL    This question is the wrong instrument for this asset
QUALIFIED     the answer stands; its drafted explanation was refused
UNCERTAIN     estimates run from 336.69 million to 1.50 billion,
              a spread of 78%
INSUFFICIENT  this platform holds too little to answer this question
```

**`DIRECTIONAL` was specified and not built.** A comparison the evidence
settles without settling a level — *"new issuance exceeds what is
burned"* — is a legitimate investor statement, and nothing currently
produces one: ETH's burn is held and its reward side is not read. It
will be added when something produces it.

`PRECISE` is not "better" than `UNCERTAIN`. There is no rank, no
ordering and no comparison operator, because a precise answer to a
question the investor is not asking is worth less than an honest bound
on one they are.

The corpus distribution:

```text
1INCH   precise x2, range x1, structural x2
ADA     insufficient x1, precise x1, qualified x1, range x1, structural x1
ARB     insufficient x1, precise x1, qualified x1, structural x1, uncertain x1
BTC     precise x3, structural x2
ETH     insufficient x1, precise x2, structural x1
HYPE    insufficient x1, precise x2, structural x1, uncertain x1
SOL     precise x2, structural x2
TAO     precise x1, qualified x1, range x1
```

---

## 4. What it refuses

**No canonical figure is ever invented.** Two sources 50m apart produce
a bound naming both, never a midpoint. Averaging disagreeing sources
into a number nobody published is the plausible-figure failure Invariant
1 exists to prevent, and a test asserts the midpoint appears nowhere —
not in the sentence, not in the readings, not in any method.

**No verdict is reinterpreted.** A committee's answer is quoted, never
translated: the sentence a reader sees is the committee's own
`verdict_stated` and the reason is its own `because`. What this layer
adds is the decision to *say it at all*.

**Nothing about the asset.** No score, rank, recommendation, aggregate,
agreement, favourable, adverse, positive, negative, good or bad —
checked over the surfaces and over the source of both modules, because
the next verdict would arrive as a helper rather than a field.

---

## 5. Two boundary fixes

**A prose failure is a presentation failure.** The validator is
untouched — every out-of-remit word is still refused and the rejected
sentence still reaches no reader — but the refusal is now recorded in
`wording_refused` and the committee falls back to its own deterministic
account. HYPE's Fee Capture answers `mechanism_evidenced` where it
previously answered nothing.

**One guard the corpus forced.** *"Tokens in existence is 21.00
million"* for Bittensor is faithful to the evidence and irresponsible to
print: the same vendor puts the maximum at 21 million, and S5 measured
that a vendor's total **is** the cap for 83 of 145 capped assets. Exact
equality is a reason to qualify and not to reject — Arbitrum genuinely
is fully emitted — so the figure stands and the statement says what else
it could be. That is the difference between reporting a number and
vouching for it.

---

## 6. Recorded, unsolved

- **`max_supply: null` and "field absent" are indistinguishable.** A
  positively stated absence of a cap is real evidence and is not
  acquired. Acquisition question.
- **`MATERIAL_SPREAD` is one constant**, set from the corpus at 25%. It
  is a boundary on *what can responsibly be said*, not a quality band,
  but it is a single number doing work across every quantity. Two
  committees' worth of corpus is not enough to say whether circulating
  supply and market capitalisation deserve the same threshold.
- **Asset Quality's absolute bands are untouched.** S5's
  `market-significance-floor@1` ($10bn / $500m) still forces a value
  across a threshold. This layer would express the same evidence as a
  range or a rank; the mismatch is recorded and not resolved, and
  whether market significance belongs in relative share, percentile or
  descriptive evidence is deliberately not decided here.

---

## 7. Surfaces

`movrvest assessment [SYMBOL]` — one block per subject with the shape
printed beside it, or the corpus as a shape distribution. No headline,
no summary, no ordering by importance: deciding which of an investor's
questions matters most is the recommendation layer, and it does not
exist.

No frontend work, for the same reason as PR #116.
