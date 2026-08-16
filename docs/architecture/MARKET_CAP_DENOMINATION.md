# Market-cap denomination: the provider never states it

**Status: acquisition audit. No implementation. Stopped for ruling.**

`quality-authority@1` left the platform honestly silent: Quality is
authorised for 0 of 77 securities because the size factor is
inadmissible, and it is inadmissible because
`market-cap-input-eligibility@1` requires an established denomination
that nothing supplies. This audit asks what evidence could establish
one.

The central question, as set: *what evidence establishes that a
provider market-cap magnitude is expressed in a denomination that
makes the existing absolute large-cap threshold valid?*

**The short answer: no provider field states the market cap's
denomination, and the field that looks like it does is demonstrably
wrong for a live security.**

---

## `CompanyFacts.currency` has no recorded intent

It is a bare field — `currency: str | None = None` — added on 29 July
in a broad pipeline refactor (`09af6f8`), **with no docstring, no
assignment anywhere, and no commit message describing it**. #140 found
it unassigned; this audit adds that it was never given a meaning to
begin with. It cannot be adopted as the market-cap denomination
because nothing says it is anything.

## Four different currencies, and they are not the same concept

Measured live over the 64 equities and funds holding a market cap:

| Concept | Provider field | What it is |
|---|---|---|
| quote currency | `currency` | the unit the **price** ticks in |
| statement currency | `financialCurrency` | the unit the **accounts** are reported in |
| market-cap denomination | **none** | never stated |
| threshold denomination | **none** | `LARGE_CAP_THRESHOLD` names no currency |

**`financialCurrency` differs from `currency` for 4 of 64.** They are
different questions, and neither is the third one.

## Is the magnitude pre-converted, or local?

**Local.** Proven by arithmetic rather than assumed: where
`marketCap == price × sharesOutstanding` the market cap is
unambiguously in the listing's own currency.

| Security | quote / statement | cap ÷ (price × shares) |
|---|---|---|
| AAPL | USD / USD | 1.000 |
| NESN.SW | CHF / CHF | **1.000** — the cap is CHF, not USD |
| ORSTED.CO | DKK / DKK | **1.000** — DKK |
| AIR.PA, BNP.PA, LDO.MI, VIE.PA … | EUR / EUR | 1.000 |

Yahoo does **not** convert. A `marketCap` of 208bn for Nestlé is 208bn
Swiss francs, and it is currently compared against a bare `10_000_000_000`.

So both of the owner's two problems are live: the denomination must be
established **and** a conversion is required. They are separate, and
the second deserves its own rule — a converted magnitude carries an FX
rate with its own source, its own timestamp and its own warrant, none
of which belong inside market-cap acquisition.

## The decisive counterexample: BP.L

| | |
|---|---|
| quote currency | **GBp** — pence, the *minor* unit |
| statement currency | **USD** |
| cap ÷ (price × shares) | **exactly 0.010** |

The ratio proves the market cap is stated in **pounds** while the
price ticks in **pence**. So for one instrument the platform sees
three different currencies, and **the quote currency is not the
market-cap denomination**. Any rule of the form *inherit the
instrument's currency* is falsified by a security the platform already
holds — and falsified by a factor of 100, which is exactly the size of
error `market-cap-input-eligibility@1` was built to refuse.

BP.L also disposes of the tempting shortcut: had the platform
inherited `currency = GBp` and converted, it would have divided a
correct pounds figure by 100 and then applied an FX rate, producing an
error it could not detect.

## Other counterexamples to a simple identity

**ADRs** — DIDIY quotes in USD and reports in CNY (ratio 1.072); SRAD
quotes USD, reports EUR (1.361). The quote currency says nothing about
the underlying.

**Dual share classes** — GOOG 2.213, VOW3.DE 2.431, NOVO-B.CO 1.325.
The market cap spans every class while `sharesOutstanding` covers one,
so the arithmetic identity simply does not hold. **This is not a
denomination problem**, and a method that treated a failed
reconciliation as a currency doubt would refuse Alphabet for the wrong
reason.

## The corpus, counted

64 securities hold a market cap (equities and funds; crypto and
futures excluded). All 64 return a quote currency.

| | count |
|---|---|
| market caps with an **explicitly stated denomination** | **0** |
| quote currency USD | 47 |
| quote currency non-USD | 17 (EUR 12, DKK 3, CHF 1, GBp 1) |
| `financialCurrency` ≠ quote currency | 4 |

Reconciliation `cap == price × shares`, as **corroboration** of the
listing currency:

| Outcome | count |
|---|---|
| corroborated (ratio ≈ 1.000) | **42** |
| minor-unit trap caught (ratio ≈ 0.010) | 1 — BP.L |
| unreconciled (dual class / ADR) | 19 |

**Of the 42 corroborated, 29 are USD-quoted and 13 are not.**

## What that makes possible, and what it does not

**29 securities could have a denomination established today with no FX
at all** — quote currency USD, corroborated by an independent
arithmetic identity from two other provider figures. That is
provenance, not conversion, and it is the cheapest honest win
available.

**13 more are corroborated in a known non-USD currency** and would
additionally need a conversion with its own warrant.

**19 are unreconciled** — the identity does not hold for structural
reasons that have nothing to do with currency. They need a different
corroboration or they stay silent.

**1 (BP.L) is affirmatively flagged** as a minor-unit case: the
platform can *detect* it, which is worth more than guessing at it.

**And none of this is comparable to the threshold until the threshold
declares its own denomination.** `LARGE_CAP_THRESHOLD = 10_000_000_000`
carries no currency. Establishing that a magnitude is 208bn CHF does
not make it comparable to an unlabelled constant; the constant must
say it is dollars. That is a policy declaration and the owner's
ruling, not an acquisition problem — and it is the first step, because
without it a perfectly established magnitude still cannot be placed.

## The chain, and where knowledge would re-enter

```
market-cap claim            Yahoo marketCap, present for 64
  → denomination            NOT established for any (0/64)
  → market-cap admissible   refused for all 77
  → quality factor          size unreadable
  → quality authority       0/77 authorised
  → band                    withheld
  → kernel direction        quality abstains, coverage < 1.00
  → recommendation          HOLD, 77/77
```

Knowledge re-enters at step two, and only there. Nothing downstream
changes, no threshold moves, and no rule is weakened — which is the
property the arc was built for.

## What must not be done

**No inference from ticker suffix or exchange geography.** BP.L is the
proof: its suffix says London, its quote says pence, its statements
say dollars and its market cap is in pounds. Geography would have got
it wrong. Suffixes may direct an investigation and may never establish
a fact.

**No tolerance based on distance from the threshold.** #136 measured
and refuted that: a margin test bounds denomination error and is
silent about identity error, and it scored SPCX.

**No fallback for the unresolved.** The 19 unreconciled and any
security whose denomination stays unknown keep today's silence.

## Recommended scope for the implementation slice

Not built here, and stated as a sequence rather than a design:

1. **Declare the threshold's denomination** — a policy statement, and
   the precondition for everything else.
2. **Establish denomination where it can be corroborated**: the quote
   currency, checked against the `price × shares` identity. Two
   independent provider figures agreeing is the same corroboration
   standard #99 applies to crypto claims, and it catches BP.L rather
   than being fooled by it.
3. **Leave conversion to its own rule.** 29 securities need none. The
   13 that do introduce an FX rate with its own source, timestamp and
   warrant — a distinct magnitude transformation, and hiding it inside
   market-cap acquisition would repeat the conflation this whole arc
   has been unwinding.

Expected restoration, if all three land: **29 securities regain a
readable size factor without any FX**, and Quality regains authority
for those with all three factors readable. Every other security keeps
its current silence.

## Recorded, not solved

The one-factor degenerate Quality set stays documented as a future
guard, per the owner: when per-factor `NOT_APPLICABLE` starts being
populated live, that is the moment for `quality-breadth@1`, based on
observed archetypes rather than speculation.
