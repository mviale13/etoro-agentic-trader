# The first warrant consumer: Momentum

**Status: built. The first slice to change a decision deliberately.
Stopped for review.**

#134 gave the platform a boundary that says what a provider reported,
what translation was performed, and what warrant supports it — and
deliberately gave it no consumers. This slice makes exactly one
analytical consumer care, and repairs the measured path:

> unmeasured daily change → manufactured `0.0` → NEUTRAL@60 → vote →
> decision

The governing question was whether Momentum may express an analytical
opinion when the platform cannot establish its input. The answer is
no, and the argument is short: **neutral is an analytical conclusion,
and an acquisition failure is not one.** A signal that says *no
meaningful momentum is visible* has made a claim about the security; a
signal reading a manufactured zero has made that claim on the strength
of a number nobody measured.

---

## 1. The pre-change dependency path

Traced end to end before anything moved:

```
yf.download closes
  → _fetch_quote          three writes of 0.0 (yahoo_market_provider.py:248-259)
  → MarketQuote.change_percent : float          ← the type with no absence
  → CachedMarketProvider._restore               a fourth 0.0 (:226)
  → CompanyFacts.daily_change_pct : float|None  (company_facts_service.py:142)
  → MomentumSignalService.build                 bands ±0.5 / ±2.0
  → MomentumSignal(trend, confidence)
  → CompanyCommitteeService._momentum_score     ×0.25 in the weighted vote
  → CompanyRecommendation (BUY/HOLD/SELL)
  → DecisionEvidence.findings / analyst_veto
  → ArtificialCIO.decide()
```

Where absence became a number, exhaustively:

| Site | Cause | Wrote |
|---|---|---|
| `yahoo_market_provider.py:259` | fewer than two closes | `0.0` |
| `yahoo_market_provider.py:256` | previous close is zero | `0.0` |
| `cached_market_provider.py:226` | stored value not numeric | `0.0` |
| `market_snapshot_archive.py:288` | the duplicated restore | `0.0` |
| `company_facts_service.py:142` | no quote at all | `None` (honest) |

And the one that must survive: a security that genuinely moved 0.00%
produces `change_percent = 0.0` with **no** absence — a real
measurement that must keep reaching NEUTRAL.

**The vote was never the problem.** `_momentum_score` maps NEUTRAL and
UNKNOWN both to `0`, so the manufactured neutral did not move the
weighted score directly. What it moved was the *confidence* (60 versus
20), the *evidence sentences* an investor reads, and — where a real
BULLISH reading rested on an unwarranted translation — the vote itself.

## 2. The warrant requirement, and why

`momentum-input-eligibility@1`, stated as explicit membership in
`momentum_signal_service.py`:

```
ELIGIBLE_WARRANTS = {VERIFIED, VALIDATED, DECLARED, ASSUMED}
```

**No ordering.** There is no "at least DECLARED"; each member is
admitted for a reason and UNKNOWN is refused by name.

The interesting admission is ASSUMED, which is where the whole
registry sits and where a naive `warrant != VERIFIED → UNKNOWN` rule
would have silenced Momentum for every security on the platform. The
brief demanded the rule be proved rather than assumed, and the proof
is arithmetic:

> A daily change is not a provider figure. This platform computes it
> as `(latest − previous) / previous` over two closes of **one
> series**, and that ratio is **invariant under any linear rescaling
> of the series**. Whether Yahoo's closes are pence or pounds, dollars
> or a yield times ten, the change between two of them is the same
> number.

So the two things ASSUMED leaves open for a price — its unit and its
currency — *cannot corrupt this quantity*. Refusing ASSUMED here would
withhold an opinion to guard against an error that is arithmetically
impossible for a ratio.

The argument is deliberately narrow and **does not generalise**: it
works because this consumer needs a ratio. A consumer of magnitudes —
dividend yield, market capitalisation — gets no such protection, which
is precisely why this slice repairs one input and not the others.

UNKNOWN is refused because it means provenance is insufficient to say
why the mapping would be valid at all. That is not a weaker ASSUMED:
it is the state in which the platform cannot name what the number is,
and no invariance argument rescues a quantity whose identity is
unsettled.

**Three separate claims, kept separate.** The warrant for the
underlying closes (`MarketQuote.price`, ASSUMED); the warrant for the
calculation (this platform's own deterministic arithmetic, which is
not a provider translation at all); and the semantic validity of
calling the result *today's move* — which is a temporal claim, handled
below and not by the warrant.

## 3. Measured versus absent

`app/domain/daily_change.py`. `DailyChange` carries `percent | None`,
the `warrant`, the `basis`, and — where there is no measurement —
a `ClaimAbsence` reusing #134's vocabulary rather than inventing a
second one. Construction refuses a value with an absence beside it,
and refuses both being empty. **No sentinel numbers.**

The six input states the brief named are now distinguishable:
measured non-zero, measured zero, insufficient history, malformed
cached value, provider unavailable, and insufficient warrant — the
last being a measurement the consumer declines to read.

`admissible_under(warrants)` takes the membership as a **parameter**:
the input does not know which warrants are good enough, because that
is a property of the analysis, not of the number. *A consumer must
state what authority it requires from its inputs*, so the consumer
holds the set.

## 4. The temporal representation

`ChangeBasis` — `SAME_SESSION` / `LAST_AVAILABLE_SESSION` /
`UNKNOWN_SESSION` — with exactly one member yielding the word *today*.

#133 measured that the closing series' own last date was read for
alignment and then discarded, with the request time stamped in its
place. `MarketQuote.session_date` now keeps it, and
`CompanyFactsService._daily_change` decides the basis by comparing
**the only two dates in hand**: the last close's date and the date the
reading was taken. Equal establishes today; earlier establishes the
last session; either missing establishes neither.

**No trading calendar is consulted or invented**, and nothing else on
the platform reads `session_date`. A Friday close read on a Sunday now
renders *"declined −2.50% in its last session"* instead of *"today"*.

## 5. The rule version

**A new rule, `momentum-input-eligibility@1`, status ARGUED** — not
`momentum-bands@2`.

The bands did not move: ±0.5 and ±2.0 are untouched, and
`momentum-bands@1` keeps its fingerprint `2ef4de85d277` exactly.
Re-versioning it would claim the thresholds had changed, which is
false. Eligibility and banding are independently evolvable — admitting
a warrant and moving a threshold are different acts with different
evidence — so they are different rules.

The new rule's fingerprint is over the *membership* (sorted, since a
frozenset's iteration order is not stable), pinned at `03e3e0ae4ccf`.
Changing which warrants Momentum accepts now requires re-pinning, and
a test proves it. The ARGUED count moved 1 → 2 with the assertion
updated deliberately; `test_exactly_two_rules_are_argued` names why.

Momentum's abstention now carries this rule, so a reader can see which
rule decided the silence — where value and quality still carry `None`,
because nothing decided theirs.

## 6–8. Before → after

**Method correction, reported first.** The replay harness used in #134
ran the script from a path outside each worktree, and Python puts the
*script's* directory on `sys.path` rather than the cwd — so the
editable install won and **both sides imported the same code**. #134's
byte-identity claim was therefore vacuous as measured. Re-run with
`sys.path.insert(0, os.getcwd())`, the claim is **confirmed**:
`af726f9` and `fc5c2b6` both digest `426ccd06…`. The method was wrong;
the answer was right. Every figure below uses the corrected harness.

**Input-semantics corpus** — 6,804 trials, the seven input states
crossed with value, quality and risk:

| Input state | Before | After |
|---|---|---|
| measured non-zero (+) | BULLISH | BULLISH |
| measured non-zero (−) | BEARISH | BEARISH |
| **measured zero** | **NEUTRAL** | **NEUTRAL** |
| insufficient history | NEUTRAL | **UNKNOWN** |
| malformed cache | NEUTRAL | **UNKNOWN** |
| insufficient warrant | BULLISH | **UNKNOWN** |
| provider unavailable | UNKNOWN | UNKNOWN |

Momentum trends: BEARISH 972 → 972, BULLISH 1944 → **972**,
NEUTRAL 2916 → **972**, UNKNOWN 972 → **3888**.
Confidence: 60 × 2916 → 60 × 972; 20 × 972 → 20 × 3888; 70 and 85
unchanged.

**Downstream, the consequence the brief asked to see:**

| | Before | After |
|---|---|---|
| BUY | 225 | **144** |
| HOLD | 4,977 | **5,058** |
| SELL | 1,602 | 1,602 |

**81 BUY recommendations disappear.** Every one came from the
insufficient-warrant state: a numerically plausible +3.1% reading
whose translation the platform cannot justify contributed +0.25 to the
weighted vote, carrying a case over the 0.50 BUY threshold that value
and quality alone did not reach. Removing false evidence removed the
BUY. **No weight, threshold, veto or gate was touched** — this is the
existing decision philosophy applied to honest inputs.

SELL is unchanged, and that is structural rather than lucky: a
manufactured NEUTRAL and an UNKNOWN both score `0`, so nothing that
was being *held back* from a veto was released.

**Named securities on the live stored corpus: none.** All 85 stored
quotes produce identical trends before and after (BEARISH 19,
BULLISH 38, NEUTRAL 21, unavailable 6). The reason is worth stating
plainly rather than presenting as reassurance: **the stored records
predate the boundary.** They carry no `change_absence` and no
`session_date`, so a stored `0.0` is indistinguishable from a measured
one — ARB is the specimen, holding `change_percent: 0.0` on a record
whose price is 0.0006 and whose market cap is 0. The repair takes
effect **on acquisition**, when the adapter records what it did. Until
`movrvest acquire` runs, the cache replays its own blindness.

On the #134 grid (172,800 trials, bare floats only) the digest moves
`426ccd06…` → `d22166a7…`, and a component-level diff shows exactly
two changes: the abstention now names its rule, and every sentence
that said *"today"* without a session date now says *"in its most
recent reading"*. **No band, trend, strength or confidence moved on
that grid** — which is the temporal repair showing up on its own.

## 9–12. The proofs

`tests/test_momentum_warrant_consumer.py`, 40 tests:

- **Genuine zero still means neutral** — a measured `0.0` is NEUTRAL,
  WEAK, confidence 60, and a parametrised sweep pins all eleven band
  boundaries unchanged.
- **Absence no longer means neutral** — every `ClaimAbsence` member
  reaches UNKNOWN, individually and as a loop over the whole
  vocabulary, so a future member cannot quietly reach a band.
- **The two are different signals** from the same `0.0`.
- **Insufficient warrant cannot become an opinion** — a plausible
  +2.5% under UNKNOWN abstains, with the refusal naming why.
- **Eligibility is membership** — the set is asserted by value, and
  `admissible_under` is shown accepting under one membership and
  refusing under another, proving the consumer owns the requirement.
- **The wording cannot overstate** — only `SAME_SESSION` yields
  *today*; a request timestamp with no session date resolves to
  `UNKNOWN_SESSION`, which is the substitution #133 found.
- **Unrelated signals untouched** — value, quality and risk are
  asserted to contain no warrant vocabulary at all.

Plus the provenance harness: the new rule is pinned, and changing the
eligibility set without re-pinning fails.

## 13. The next warrant consumer, by measured causal authority

Ranked after this repair, from the generated inventory crossed with
what this slice measured:

1. **`ValuationSnapshot.market_cap` → the large-cap quality point.**
   The strongest remaining case. It gates a decision, it is ASSUMED,
   and — unlike a daily change — it is a **magnitude**, so no
   invariance argument protects it: a currency or unit error moves it
   across the $10bn line directly. SPCX's stored $1.75T clears that
   line today on a figure whose *identity* is unresolved (#134 §6),
   which is the two defects compounding.
2. `ValuationSnapshot.eps (substituted)` — already UNKNOWN in the
   registry, gates a decision through the positive-earnings point, and
   bites exactly on turnarounds.
3. `ValuationSnapshot.dividend_yield` — UNKNOWN, gates a decision, but
   read only for its sign, so the repair is cheap and the current
   exposure is latent rather than live.

**Not implemented**, per the brief.

## What this slice deliberately did not do

No other consumer reads a warrant. No generic "all ASSUMED facts are
unusable" rule — that policy would have silenced Momentum too, and the
measurement above is what shows why it would have been wrong. No
change to the 0.40/0.35/0.25 weights, the ±0.50 thresholds, the veto,
the gates, or any other signal. No repair of dividend yield, EPS,
forward P/E, currency, SPCX identity, `^TNX` or asset class.

**Recorded and unsolved:** `MarketQuote.change_percent` is still a
bare `float`, so the adapter still writes a compatibility `0.0`
beside the absence rather than declining to produce a number — the
absence is now recorded, but the legacy type still forces the
substitution. `market_snapshot_archive.py` still holds its duplicate
restore and does not set `change_absence`. And the stored corpus
cannot be retro-classified: what a pre-boundary `0.0` meant is not
recoverable from the record.
