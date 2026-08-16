# `provider-quality@1`: coverage is being read as performance

**Status: research. No production behaviour changed. Stopped for
ruling.**

The blocker found while measuring the #136→#139 stack: Apple scores
**every factor the platform could read** — a dividend — and bands
**LOW**, voting `−1`. Withdrawing an unestablished market cap did not
make quality *unknown*; it made quality *adverse*.

Six blocking specimens: AAPL, GOOG, PG, PLTR, SBUX, TSLA. Under the
stack the platform issues SELL on all six.

---

## 1–3. What the three terms actually mean

**`earned`** — how many intended quality factors *passed their test*.
A count of passes among tests actually run. Not a measure of the
business.

**`available`** — how many intended factors the platform could read.
Its own docstring settles this: *"counts only the factors this
company's data allowed a look at, so it is **a statement about the
reading rather than about the business**."*

**The band** — ambiguous, and measurably so. Over the live corpus:

| earned/available | count | band | ratio | vote | representatives |
|---|---|---|---|---|---|
| 0/0 | 21 | UNKNOWN | — | — | BA, BTC-USD, 1INCH-USD … |
| **0/1** | **9** | **LOW** | **0.00** | **−1** | CLNE, CPNG, H2O.DE … |
| **1/1** | **33** | **LOW** | **1.00** | **−1** | **AAPL, GOOG, AMZN, META …** |
| 1/2 | 2 | LOW | 0.50 | −1 | F, SYENS.BR |
| 2/2 | 12 | MEDIUM | 1.00 | 0 | AIR.PA, DAL, DIS … |

Two conflations, in opposite directions, both live:

- **Performance is invisible.** `1/1` and `0/1` — passing everything
  readable and *failing* everything readable — produce the **same
  band and the same vote**. 33 securities against 9.
- **Coverage is read as performance.** `1/1` and `2/2` both score
  100% of what was readable, and band LOW versus MEDIUM: `−1` versus
  `0`. The only difference between them is how much the platform could
  see.

No live security reaches `3/3`, because `market-cap-input-eligibility@1`
makes the size factor inadmissible for every one of them.

## 4. Is a band allowed on a subset?

**The platform already answered no — and only in the explanation
layer.** `ScoreDerivation.is_capped_by_unreadable_factors` is true
exactly when `earned == available` and `available < required`, and it
words the result *"{band} is as far as {available} factors reach"*.
The test that pins it says so outright:

> *"The bands are absolute, so a company whose dividend could not be
> read cannot reach HIGH however good it is. Without this the investor
> reads MEDIUM as a verdict on the business."*

So the platform knows a capped band is not a verdict, built a
predicate for precisely the AAPL state, and words it honestly — **and
the vote consumes the band as a verdict anyway.** The explanation
layer was repaired; the decision layer never was.

## 5. Minimum evidence for a directional band

Measured, not argued. The invariant: *replacing an established factor
with ignorance must never make the assessment more adverse or more
favourable — only less authoritative.*

| Candidate | more-adverse | more-favourable | |
|---|---|---|---|
| **C0** fixed absolute (current) | 3 | 0 | violated |
| **C1** relative `earned/available` | 1 | 2 | violated |
| **C2** relative + min coverage | 1 | 1 | violated |
| **C3** relative + min breadth | 1 | 1 | violated |
| **C4** performance + authority | **0** | **0** | **holds** |

The failing transitions are concrete: C0 turns `2/2 MEDIUM` into
`1/1 LOW` when a *passed* factor is deleted; C1 turns `1/2 LOW` into
`1/1 HIGH` when a *failed* factor is deleted — the opposite defect,
exactly as predicted. C2 and C3 both still allow `2/3 MEDIUM → 2/2
HIGH` on deleting a failed factor.

Only C4 holds, and it holds **structurally rather than by tuning**:
requiring full coverage of the applicable factor set means any
deletion drops below it, so the band becomes UNKNOWN and has no
direction to move. This is the same mechanism `decision-authority@1`
uses one layer up, and it is the answer to question 5: **the minimum
is every applicable factor.**

## 6. NOT_APPLICABLE versus applicable-but-unavailable, inside Quality

**Not distinguished at all today.** The signal refuses the entire
factor set for a no-company asset (F1, correct), but *within* a
company every unread factor is treated identically: an inadmissible
market cap, an absent dividend field and an unread EPS all simply fail
to increment `available`.

`market-cap-input-eligibility@1` introduced the first factor that is
**applicable and inadmissible** — in #139's vocabulary,
`EXPECTED_ABSENT` rather than `NOT_APPLICABLE` — and Quality has no
vocabulary for the distinction. A company that genuinely pays no
dividend reads `dividend_yield = 0.0`, which *is* a reading and counts;
a company whose dividend field is missing does not. The two are
already handled differently by accident of the data rather than by
declaration.

## 7. Do the existing objects already separate the three?

**Yes, and the ruler collapses them.** The domain carries performance
(`earned`), coverage (`available`), the capped-authority predicate
(`is_capped_by_unreadable_factors`) and even the shortfall
(`next_band_needs`) — four separate facts — and `BANDS` reduces all of
them to one absolute comparison of `earned` against `3`.

This is #138's finding, one layer down and independently arrived at:
the objects grew a vocabulary for absence, and the consumer that turns
them into a decision never learned it.

## The history: shortcut, not policy

The original signal (`9772761`, 29 July) was a bare integer counter —
three `if` blocks, `score >= 3 → HIGH`, `>= 2 → MEDIUM`, else LOW —
with **no concept of availability at all**. The denominator is
implicit in those two thresholds, written when the code had no way to
know how many factors it had read.

`available` arrived eleven days later (`cf8a925`, 9 August) in a commit
about *explaining* scores — "why 80, in arithmetic the investor can
check" — and the band was never revisited. **No test asserts that a
partially-covered company should band LOW as a judgement**; the only
test touching the case documents the cap as a limitation to disclose.

**Verdict: an implementation shortcut inherited from a time when all
three factors were assumed present.** It was never investment policy,
and nothing in the repository defends it as one.

## The six specimens under every candidate

| | e/a | C0 | C1 | C2 | C3 | C4 |
|---|---|---|---|---|---|---|
| AAPL | 1/1 | **LOW** | **HIGH** | UNKNOWN | UNKNOWN | UNKNOWN |
| GOOG | 1/1 | **LOW** | **HIGH** | UNKNOWN | UNKNOWN | UNKNOWN |
| PG | 1/1 | **LOW** | **HIGH** | UNKNOWN | UNKNOWN | UNKNOWN |
| PLTR | 1/1 | **LOW** | **HIGH** | UNKNOWN | UNKNOWN | UNKNOWN |
| SBUX | 1/1 | **LOW** | **HIGH** | UNKNOWN | UNKNOWN | UNKNOWN |
| TSLA | 1/1 | **LOW** | **HIGH** | UNKNOWN | UNKNOWN | UNKNOWN |

Semantically: C0 says *one passed factor out of one is poor quality*.
C1 says *one passed factor out of one is excellent quality* — the
opposite defect, and it is why `earned / available` alone was refused
before it was measured. C2, C3 and C4 all say *one factor is not
enough to judge a business*, which is the only defensible reading of a
single dividend.

## Stack consequences (consequence, not criterion)

Over the 77-security corpus with #136→#139 applied:

| Candidate | BUY | HOLD | SELL | quality bands |
|---|---|---|---|---|
| C0 (current) | 3 | 64 | **10** | LOW 44, MEDIUM 12, UNKNOWN 21 |
| C1 | **22** | 52 | 3 | **HIGH 45**, LOW 11, UNKNOWN 21 |
| C2 | 5 | 72 | 0 | HIGH 12, LOW 2, UNKNOWN 63 |
| C3 | 5 | 72 | 0 | HIGH 12, LOW 2, UNKNOWN 63 |
| C4 | 0 | 77 | 0 | UNKNOWN 77 |

C2 and C3 are **identical on this corpus** — with a three-factor set,
"two thirds of the intended set" and "at least two factors" select the
same states. They would diverge only on a factor set of four or more.

**C4's zero is not permanent and should not be read as one.** Quality
abstains for all 77 because `market-cap-input-eligibility@1` currently
makes the size factor inadmissible for every security, so `available`
never reaches 3. Establishing the market cap's denomination — the
repair #136 already names as its obvious successor — restores `3/3`
and with it normal banding. **C4's severity is a measurement of the
open provider defect, not of C4.**

## What this slice recommends, and does not build

The invariant admits exactly one candidate, and it is the one that
mirrors the kernel repair: **Quality expresses a direction only where
every applicable factor was established, and otherwise abstains** —
performance and coverage kept apart, authority decided separately,
exactly as `decision-authority@1` does for the vote.

**Open for the owner, deliberately not decided here:**

- whether C4's abstention should be conditional on repairing the
  currency crossing first, so the two land together and quality does
  not go silent corpus-wide in between;
- whether Quality should gain a per-factor `NOT_APPLICABLE` (§6) so
  that a factor a company structurally cannot have stops counting
  against its coverage, as #139 did at the signal level;
- whether `earned/available` should be *reported* as performance even
  where no band is authorised — the platform would then be able to say
  *"passed the one factor we could read, which is not enough to judge
  the business"*, which is true and currently unsayable.

**No production behaviour changed. #136–#139 are untouched.**
