"""Judge a pool of token market claims into facts, deterministically.

The path a provider value takes before anything may consume it:

    fact request
      → 0..N candidate claim sets (one per provider adapter)
      → identity validation, per set
      → semantic validation, per set
      → internal consistency validation, per set
      → cross-claim comparison, per fact
      → standing — and a canonical fact only where establishment
        criteria are satisfied

Two rules the corpus taught, now load-bearing:

**Agreement inside one provider is not corroboration.** A vendor's
market value reproduces its own price × circulating supply because the
vendor computes one from the other — Arbitrum's did, exactly, while its
circulating supply sat frozen at the 2023 launch float and its market
value was 4× wrong. Intra-source arithmetic is necessary (an incoherent
set is rejected) but never sufficient: a fact is ESTABLISHED only when
independent sources agree.

**When credible sources disagree materially, expose the uncertainty.**
Two coherent claimants put Hyperliquid's market value 33% apart because
they count circulating supply differently. That is a fact about the
asset's measurability, not noise to average away or resolve by hidden
precedence — the fact stands CONFLICTED, every claim retained and
attributed, until an explicit methodology rule exists.

Tolerances remain timing allowances, not methodology resolution: they
absorb the minutes between two observations of a moving market, and
nothing else. No model judges anything here, and the same claims always
judge to the same facts.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime

from app.domain.provenance import Provenance
from app.domain.token_facts import (
    TOKEN_FACTS,
    RejectedReading,
    TokenFact,
    TokenFactStanding,
    TokenMarketFacts,
)

#: The rule under which a pooled claim becomes an established fact,
#: versioned so a figure travelling upward can name what admitted it.
#:
#: One name for one rule: independent cross-source agreement inside the
#: tolerances below, over claim sets that already passed identity,
#: semantic and internal-coherence validation. A layer receiving a
#: number is entitled to say *which* gate let it through, and "the
#: crypto gate" is not checkable while `token-fact-establishment@1` is.
#: Change the rule, change the version — the tolerances below are part
#: of it.
ESTABLISHMENT_RULE = "token-fact-establishment@1"

#: How far one source's own figures may disagree with each other.
#: price × circulating supply and the reported market value come from
#: the same snapshot, so 5% covers rounding and update lag while an
#: order-of-magnitude error cannot fit inside it.
INTERNAL_TOLERANCE = 0.05

#: How far two providers may disagree about the same *value* and still
#: corroborate each other — observation timing, never methodology.
#:
#: Recorded and deliberately not acted on: the two price claimants do
#: not run the same kind of clock. CoinGecko states an observation time
#: that advances; TokenInsight states none, so its claim carries a
#: receipt time. This tolerance therefore cannot be checked against the
#: interval between two *stated* observations, because only one side
#: states one.
#:
#: What the corpus says about that gap is reassuring and is not a rule.
#: On 2026-08-21 the eight tokens' two claimants agreed to between
#: 0.004% and 0.32% — while the clocks they carried stood up to 16.47
#: hours apart. Pro-rated from each asset's own 24-hour move, a genuine
#: 16-hour separation implies a gap 6x to 53x larger than the one
#: measured. The figures are contemporaneous; it was the timestamp that
#: was wrong, which is why the repair was to the clock and not to this
#: number.
CROSS_TOLERANCE = 0.10

#: How far two providers may disagree about a supply *count*. Counts
#: move by issuance schedules, not by the minute; a gap past this is a
#: counting-methodology question and is surfaced as one.
COUNT_TOLERANCE = 0.01

#: A claim that is this many times away from every arithmetically
#: coherent claim, while carrying no arithmetic of its own, is not a
#: conflicting methodology — it is a defective reading, rejected with
#: its reason retained. Yahoo's $8,105 for an $18bn token is the class.
OUTLIER_FACTOR = 10.0

#: What each fact is called to the investor. Worded here, beside the
#: judging, so a rejected reading and a served fact use the same name.
FACT_LABELS = {
    "market_cap": "Market value",
    "rank": "Market-value rank",
    "price": "Price",
    "price_change_24h": "Price change over 24 hours",
    "spot_volume_24h": "Tracked spot volume over 24 hours",
    "spot_volume_change_24h": "Spot-volume change over 24 hours",
    "market_volume_24h": "Reported market volume over 24 hours",
    "circulating_supply": "Circulating supply",
    "total_supply": "Total supply",
    "max_supply": "Maximum supply",
    "fully_diluted_valuation": "Fully diluted valuation",
    "project_age": "Project age",
}

#: The facts whose claims are pooled and compared across sources.
#: Values compare at CROSS_TOLERANCE, counts at COUNT_TOLERANCE.
_POOLED_VALUES = ("price", "market_cap", "fully_diluted_valuation")
_POOLED_COUNTS = ("circulating_supply", "total_supply", "max_supply")

#: Facts served as claims and never pooled: their semantics are scoped
#: to the vendor that publishes them. A rank is relative to a listing
#: universe (the same token measured #116 and #233 on the same day),
#: and each volume figure counts a different venue universe — treating
#: agreement between them as corroboration would manufacture a fact
#: out of a coincidence of methodologies.
_SCOPED_CLAIMS = (
    "rank",
    "spot_volume_24h",
    "spot_volume_change_24h",
    "price_change_24h",
    "market_volume_24h",
)

_SCOPED_MEANINGS = {
    "rank": (
        "a position in its source's own listing universe — vendors "
        "rank different universes, so ranks are never pooled"
    ),
    "spot_volume_24h": (
        "tracked spot-market volume — a narrower concept than total "
        "trading volume, and it is not mapped onto one"
    ),
    "spot_volume_change_24h": (
        "a day-over-day movement of tracked spot volume — a dated "
        "observation, not a trend conclusion"
    ),
    "price_change_24h": (
        "a day-over-day price movement — a dated observation, not a trend conclusion"
    ),
    "market_volume_24h": (
        "volume across the venues its source tracks — a "
        "vendor-defined universe, distinct from tracked spot volume, "
        "and neither is total market activity"
    ),
}


@dataclass(frozen=True, slots=True)
class TokenClaimSet:
    """One provider's claims about one token, distilled and unjudged.

    A set rather than loose per-fact claims because intra-source
    arithmetic is a property of the set: a triad check across two
    vendors' figures would be meaningless.

    Every adapter terminates here — nothing downstream of this object
    ever sees a provider response.
    """

    source: str
    read: Provenance

    #: The symbol the provider says it answered about, where it echoes
    #: one. Checked again at judgment even though adapters refuse a
    #: mismatch at read time.
    symbol_echo: str | None = None

    #: The provider's own identifier for the asset, where it has one.
    provider_id: str | None = None

    price: float | None = None
    market_cap: float | None = None
    circulating_supply: float | None = None
    total_supply: float | None = None
    max_supply: float | None = None
    fully_diluted_valuation: float | None = None
    rank: float | None = None
    spot_volume_24h: float | None = None
    market_volume_24h: float | None = None
    spot_volume_change_24h: float | None = None
    price_change_24h: float | None = None

    #: A claimed asset-inception date. Semantically inadmissible for a
    #: token — what such a field measures was never established, and it
    #: has claimed six years of history for a token that began trading
    #: in 2024 — so any set carrying one has it rejected into the
    #: ledger rather than judged.
    inception: datetime | None = None

    def value(self, fact: str) -> float | None:
        return getattr(self, fact, None)


def judge(
    symbol: str,
    claim_sets: Sequence[TokenClaimSet],
) -> TokenMarketFacts:
    """Every claim about one token, judged into facts with standings."""

    return _Judgment(symbol, claim_sets).outcome()


@dataclass
class _JudgedSet:
    """One claim set with its per-set verdicts attached."""

    claims: TokenClaimSet

    #: price × circulating reproduced the market value: the triad —
    #: price, circulating supply, market value — is coherent.
    triad_vouched: bool = False

    #: price × maximum reproduced the fully diluted valuation.
    fdv_vouched: bool = False

    #: Facts this set may no longer claim (failed intra-set checks).
    withdrawn: frozenset[str] = frozenset()

    def offers(self, fact: str) -> float | None:
        if fact in self.withdrawn:
            return None

        return self.claims.value(fact)

    def vouches(self, fact: str) -> bool:
        """Whether this set's own arithmetic reproduces this fact."""

        if fact in ("price", "market_cap", "circulating_supply"):
            return self.triad_vouched

        if fact in ("max_supply", "fully_diluted_valuation"):
            return self.fdv_vouched

        return False


class _Judgment:
    """One pass of the gate, accumulating facts and the ledger."""

    def __init__(
        self,
        symbol: str,
        claim_sets: Sequence[TokenClaimSet],
    ) -> None:
        self._symbol = symbol.upper().strip()
        self._rejected: list[RejectedReading] = []
        self._sets = [
            _JudgedSet(claims=claims)
            for claims in claim_sets
            if self._identity_holds(claims)
        ]

        for judged in self._sets:
            self._check_internal_consistency(judged)

    # ── identity ────────────────────────────────────────────────────

    def _identity_holds(self, claims: TokenClaimSet) -> bool:
        """Refuse a whole set that answers about another token."""

        echo = (claims.symbol_echo or "").upper().strip()

        if echo and echo != self._symbol:
            self._rejected.append(
                RejectedReading(
                    fact="market_cap",
                    label="Reading",
                    stated=f"an answer about {echo}",
                    source=claims.source,
                    observed_at=claims.read.observed_at,
                    because=(
                        f"the provider answered about {echo} when asked "
                        f"about {self._symbol} — an identity mismatch "
                        "rejects every claim in the reading."
                    ),
                )
            )

            return False

        return True

    # ── intra-set integrity ─────────────────────────────────────────

    def _check_internal_consistency(self, judged: _JudgedSet) -> None:
        """One source's figures must reproduce each other.

        Necessary, never sufficient: a coherent set earns the right to
        be compared, not the standing of a fact.
        """

        claims = judged.claims
        withdrawn: set[str] = set()

        price = claims.price
        circulating = claims.circulating_supply
        market_cap = claims.market_cap

        if price and circulating and market_cap:
            implied = price * circulating

            if _within(implied, market_cap, INTERNAL_TOLERANCE):
                judged.triad_vouched = True
            else:
                because = (
                    f"its own price × circulating supply implies "
                    f"{_money(implied)}, which does not reproduce the "
                    f"{_money(market_cap)} it reports — arithmetic "
                    "inconsistency rejects all three figures."
                )

                for fact, stated in (
                    ("market_cap", _money(market_cap)),
                    ("price", _money(price)),
                    ("circulating_supply", _count(circulating)),
                ):
                    withdrawn.add(fact)
                    self._reject(judged, fact, stated, because)

        supply_pairs = (
            ("circulating_supply", "total_supply"),
            ("total_supply", "max_supply"),
            ("circulating_supply", "max_supply"),
        )

        for smaller, larger in supply_pairs:
            low = claims.value(smaller)
            high = claims.value(larger)

            if (
                low
                and high
                and smaller not in withdrawn
                and low > high * (1 + COUNT_TOLERANCE)
            ):
                because = (
                    f"it reports more {FACT_LABELS[smaller].lower()} than "
                    f"its own {FACT_LABELS[larger].lower()} — the pair "
                    "cannot both be true, and arithmetic cannot say "
                    "which one is."
                )

                for fact in (smaller, larger):
                    if fact not in withdrawn:
                        withdrawn.add(fact)
                        self._reject(
                            judged,
                            fact,
                            _count(claims.value(fact) or 0.0),
                            because,
                        )

        price_ok = claims.price and "price" not in withdrawn
        diluted = claims.fully_diluted_valuation
        cap = claims.max_supply

        if price_ok and diluted and cap and "max_supply" not in withdrawn:
            assert claims.price is not None

            if _within(claims.price * cap, diluted, INTERNAL_TOLERANCE):
                judged.fdv_vouched = True
            else:
                withdrawn.add("fully_diluted_valuation")
                self._reject(
                    judged,
                    "fully_diluted_valuation",
                    _money(diluted),
                    (
                        "price × maximum supply implies "
                        f"{_money(claims.price * cap)}, which does not "
                        "reproduce it — arithmetic inconsistency."
                    ),
                )

        judged.withdrawn = frozenset(withdrawn)

    def _reject(
        self,
        judged: _JudgedSet,
        fact: str,
        stated: str,
        because: str,
    ) -> None:
        self._rejected.append(
            RejectedReading(
                fact=fact,
                label=FACT_LABELS[fact],
                stated=stated,
                source=judged.claims.source,
                observed_at=judged.claims.read.observed_at,
                because=because,
            )
        )

    # ── the outcome ─────────────────────────────────────────────────

    def outcome(self) -> TokenMarketFacts:
        facts: dict[str, TokenFact] = {}

        for fact in (*_POOLED_VALUES, *_POOLED_COUNTS):
            facts[fact] = self._pooled(fact)

        for fact in _SCOPED_CLAIMS:
            facts[fact] = self._scoped(fact)

        facts["project_age"] = self._project_age()

        native = self._native()

        return TokenMarketFacts(
            symbol=self._symbol,
            provider_id=(native.claims.provider_id if native else None),
            facts=tuple(facts[name] for name in TOKEN_FACTS),
            rejected=tuple(self._rejected),
            yahoo_market_cap_corroborated=self._yahoo_corroborated(facts["market_cap"]),
            read=(native.claims.read if native else self._any_read()),
        )

    def _native(self) -> _JudgedSet | None:
        """The crypto-native claimant, for display attribution only.

        Never an authority: it decides which agreeing figure is
        printed and whose reading dates the object, and nothing about
        standings.
        """

        for judged in self._sets:
            if judged.claims.provider_id is not None:
                return judged

        return self._sets[0] if self._sets else None

    def _any_read(self) -> Provenance | None:
        return self._sets[0].claims.read if self._sets else None

    # ── pooled facts ────────────────────────────────────────────────

    def _pooled(self, fact: str) -> TokenFact:
        tolerance = COUNT_TOLERANCE if fact in _POOLED_COUNTS else CROSS_TOLERANCE

        candidates = [
            (judged, value)
            for judged in self._sets
            if (value := judged.offers(fact)) is not None
        ]

        candidates = self._without_outliers(fact, candidates)

        if not candidates:
            return self._absent(
                fact,
                "no source this platform reads reports one it is willing to serve.",
            )

        if len(candidates) == 1:
            judged, value = candidates[0]

            vouched = judged.vouches(fact)

            return TokenFact(
                fact=fact,
                standing=TokenFactStanding.CLAIMED,
                value=value,
                source=judged.claims.source,
                observed_at=judged.claims.read.observed_at,
                observation_stated=judged.claims.read.observation_stated,
                because=(
                    f"{judged.claims.source} reports it"
                    + (", coherently with its own figures" if vouched else "")
                    + ", and no independent source corroborates it — "
                    "agreement inside one provider is not corroboration."
                ),
            )

        values = [value for _, value in candidates]

        agreed = all(
            _within(one, other, tolerance)
            for index, one in enumerate(values)
            for other in values[index + 1 :]
        )

        if agreed:
            return self._established(fact, candidates)

        return self._conflicted(fact, candidates, tolerance)

    def _without_outliers(
        self,
        fact: str,
        candidates: list[tuple[_JudgedSet, float]],
    ) -> list[tuple[_JudgedSet, float]]:
        """Reject a defective reading before conflict is even asked.

        A claim more than an order of magnitude from *every*
        arithmetically coherent claim, itself carrying no arithmetic,
        is not a methodology — it is the $8,105 class, rejected with
        its reason and removed from the pool.
        """

        vouched_values = [value for judged, value in candidates if judged.vouches(fact)]

        if not vouched_values:
            return candidates

        kept: list[tuple[_JudgedSet, float]] = []

        for judged, value in candidates:
            is_outlier = not judged.vouches(fact) and all(
                _factor_between(value, vouched) >= OUTLIER_FACTOR
                for vouched in vouched_values
            )

            if not is_outlier:
                kept.append((judged, value))
                continue

            nearest = min(vouched_values, key=lambda v: _factor_between(value, v))

            self._reject(
                judged,
                fact,
                _stated_value(fact, value),
                (
                    "it disagrees with every arithmetically coherent "
                    f"claim by a factor of at least "
                    f"{_factor(nearest, value)} and offers no "
                    "arithmetic of its own to check."
                ),
            )

        return kept

    def _established(
        self,
        fact: str,
        candidates: list[tuple[_JudgedSet, float]],
    ) -> TokenFact:
        served = self._served(fact, candidates)

        others = sorted(
            judged.claims.source for judged, _ in candidates if judged is not served[0]
        )

        vouched_note = (
            "coherent with its source's own arithmetic, and "
            if served[0].vouches(fact)
            else ""
        )

        return TokenFact(
            fact=fact,
            standing=TokenFactStanding.ESTABLISHED,
            value=served[1],
            source=served[0].claims.source,
            observed_at=served[0].claims.read.observed_at,
            # The served claimant's own clock, never a corroborator's.
            # Where one source states an observation time and the other
            # does not, agreement on the *value* is not permission to
            # date one source's figure by the other's reading — that
            # would let a claim borrow an authority it does not have,
            # which is the failure the whole gate exists to prevent.
            observation_stated=served[0].claims.read.observation_stated,
            because=(
                f"{vouched_note}independently corroborated by "
                f"{_and(others)} within observation-timing tolerance."
            ),
            # The same claimants the sentence names, carried as a list:
            # the served figure's source first, then the corroborators
            # in the order the sentence states them. A consumer that
            # must attribute the value reads this and never the prose.
            claimants=(served[0].claims.source, *others),
            rule=ESTABLISHMENT_RULE,
        )

    def _served(
        self,
        fact: str,
        candidates: list[tuple[_JudgedSet, float]],
    ) -> tuple[_JudgedSet, float]:
        """Which agreeing figure is printed.

        A display choice among corroborating claims, stated rather than
        hidden: the crypto-native claimant's figure where it is among
        them, else the first claimant whose own arithmetic vouches the
        fact. It selects a numeral inside the agreement corridor —
        never a winner of a conflict.
        """

        native = self._native()

        for judged, value in candidates:
            if judged is native:
                return judged, value

        for judged, value in candidates:
            if judged.vouches(fact):
                return judged, value

        return candidates[0]

    def _conflicted(
        self,
        fact: str,
        candidates: list[tuple[_JudgedSet, float]],
        tolerance: float,
    ) -> TokenFact:
        """Material disagreement, exposed rather than resolved.

        No value is served, no average is taken, no source wins by
        precedence. Every claim is named with its figure and its
        observation time — for a count, the honest reading is that the
        sources measure the concept differently, and which methodology
        this platform should adopt is a rule nobody has made yet.
        """

        accounts = "; ".join(
            f"{judged.claims.source} reports "
            f"{_stated_value(fact, value)} "
            f"({judged.claims.read.stated()})"
            for judged, value in sorted(candidates, key=lambda pair: -pair[1])
        )

        methodology = (
            " The sources appear to count the concept differently, and "
            "no methodology rule chooses between them."
            if fact in _POOLED_COUNTS or fact == "market_cap"
            else ""
        )

        return TokenFact(
            fact=fact,
            standing=TokenFactStanding.CONFLICTED,
            because=(
                f"credible sources disagree beyond observation-timing "
                f"tolerance ({tolerance:.0%}): {accounts}."
                f"{methodology} Uncertainty is exposed rather than a "
                "consensus manufactured."
            ),
        )

    # ── scoped claims ───────────────────────────────────────────────

    def _scoped(self, fact: str) -> TokenFact:
        """A vendor-scoped figure: served as its source's claim, always.

        Preference among sources is display order only — the
        crypto-native claimant first — never establishment.
        """

        ordered = sorted(
            self._sets,
            key=lambda judged: judged is not self._native(),
        )

        for judged in ordered:
            value = judged.offers(fact)

            if value is None:
                continue

            return TokenFact(
                fact=fact,
                standing=TokenFactStanding.CLAIMED,
                value=value,
                source=judged.claims.source,
                observed_at=judged.claims.read.observed_at,
                observation_stated=judged.claims.read.observation_stated,
                because=(
                    f"{judged.claims.source} reports it; {_SCOPED_MEANINGS[fact]}."
                ),
            )

        return self._absent(
            fact,
            "no source this platform reads reports it for this token.",
        )

    # ── project age ─────────────────────────────────────────────────

    def _project_age(self) -> TokenFact:
        """Unknown until a source with established semantics exists."""

        claimed = False

        for judged in self._sets:
            inception = judged.claims.inception

            if inception is None:
                continue

            claimed = True

            self._reject(
                judged,
                "project_age",
                inception.date().isoformat(),
                (
                    "what this field measures for a token was never "
                    "established, and it has been measured claiming six "
                    "years of history for a token that began trading in "
                    "2024, so no date read from it establishes anything "
                    "— including this one."
                ),
            )

        if claimed:
            return self._absent(
                "project_age",
                "the one field that claimed a start date has "
                "unestablished semantics and was rejected; no other "
                "source publishes one. Unknown is the honest answer.",
            )

        return self._absent(
            "project_age",
            "no source this platform reads publishes a project start "
            "date. Unknown is the honest answer.",
        )

    # ── the volume gate ─────────────────────────────────────────────

    def _yahoo_corroborated(self, market_cap: TokenFact) -> bool:
        """Whether Yahoo's market-cap claim agreed with the established one.

        The sibling-authority gate for Yahoo's broader volume concept:
        a source shown wrong about the instrument keeps no other
        claim's authority, and a conflicted market value corroborates
        nobody.
        """

        if market_cap.standing is not TokenFactStanding.ESTABLISHED:
            return False

        assert market_cap.value is not None

        for judged in self._sets:
            if judged.claims.source != "Yahoo Finance":
                continue

            claim = judged.offers("market_cap")

            return claim is not None and _within(
                claim, market_cap.value, CROSS_TOLERANCE
            )

        return False

    # ── constructors ────────────────────────────────────────────────

    def _absent(self, fact: str, because: str) -> TokenFact:
        return TokenFact(
            fact=fact,
            standing=TokenFactStanding.ABSENT,
            because=because,
        )


# ── arithmetic helpers ──────────────────────────────────────────────


def _within(value: float, target: float, tolerance: float) -> bool:
    """Whether two observations agree, allowing for observation timing."""

    if target == 0:
        return value == 0

    return abs(value - target) / abs(target) <= tolerance


def _factor_between(one: float, other: float) -> float:
    if not one or not other:
        return float("inf")

    return max(one, other) / min(one, other)


def _factor(one: float, other: float) -> str:
    """How far apart two figures are, as a reader checks it."""

    ratio = _factor_between(one, other)

    if ratio == float("inf"):
        return "∞"

    if ratio >= 1000:
        return f"{ratio:,.0f}"

    return f"{ratio:,.1f}"


def _stated_value(fact: str, value: float) -> str:
    if fact in _POOLED_COUNTS:
        return _count(value)

    if fact == "rank":
        return f"#{value:,.0f}"

    return _money(value)


def _money(value: float) -> str:
    """An amount at a unit that shows it — including a nonsense one."""

    if value >= 1_000_000_000:
        return f"${value / 1_000_000_000:,.1f}bn"

    if value >= 1_000_000:
        return f"${value / 1_000_000:,.0f}m"

    return f"${value:,.0f}"


def _count(value: float) -> str:
    return f"{value:,.0f}"


def _and(names: Sequence[str]) -> str:
    if not names:
        return "nothing"

    if len(names) == 1:
        return names[0]

    return ", ".join(names[:-1]) + f" and {names[-1]}"
