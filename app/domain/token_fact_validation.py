"""Judge token market claims into facts, deterministically.

The path a provider value takes before anything may consume it:

    provider claim
      → identity validation
      → semantic validation
      → internal consistency validation
      → cross-source corroboration where available
      → established fact

Every rule here is arithmetic or a stated identity check. No model
judges plausibility, no threshold is an investment opinion, and the
same claims always judge to the same facts. A claim that fails is
rejected *with its reason retained* — the Yahoo reading that priced a
token at $8,105 must not silently disappear; it must be visible as the
rejected claim it is.

Tolerances are timing allowances, not leniency: two observations of a
moving market taken at different instants are never exactly equal, and
demanding false exactness would reject every true figure. They are wide
enough for provider timing and narrow enough that a catastrophic error
— an order of magnitude, a wrong token — cannot pass.
"""

from __future__ import annotations

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

#: How far one source's own figures may disagree with each other.
#: price × circulating supply and the reported market value come from
#: the same snapshot, so 5% covers rounding and update lag while an
#: order-of-magnitude error cannot fit inside it.
INTERNAL_TOLERANCE = 0.05

#: How far two providers may disagree about the same fact and still
#: corroborate each other. They observe at different instants, so this
#: is wider — and a genuine conflict is not a matter of percent.
CROSS_TOLERANCE = 0.10

#: How far two providers may disagree about a supply *count*. Counts
#: are not prices: they move by issuance schedules, not by the minute.
COUNT_TOLERANCE = 0.01

#: What each fact is called to the investor. Worded here, beside the
#: judging, so a rejected reading and a served fact use the same name.
FACT_LABELS = {
    "market_cap": "Market value",
    "rank": "Market-value rank",
    "price": "Price",
    "price_change_24h": "Price change over 24 hours",
    "spot_volume_24h": "Tracked spot volume over 24 hours",
    "spot_volume_change_24h": "Spot-volume change over 24 hours",
    "circulating_supply": "Circulating supply",
    "total_supply": "Total supply",
    "max_supply": "Maximum supply",
    "fully_diluted_valuation": "Fully diluted valuation",
    "project_age": "Project age",
}


@dataclass(frozen=True, slots=True)
class NativeTokenClaims:
    """The crypto-native provider's claims, distilled and unjudged."""

    #: The symbol the provider says it answered about — the identity
    #: echo, checked again here even though the provider refuses a
    #: mismatch at read time.
    symbol: str

    provider_id: str
    source: str
    read: Provenance

    price: float | None = None
    market_cap: float | None = None
    circulating_supply: float | None = None
    max_supply: float | None = None
    fully_diluted_valuation: float | None = None
    rank: float | None = None
    spot_volume_24h: float | None = None

    #: Day-over-day changes, as fractions. Dated observations for a
    #: surface; never trend conclusions.
    spot_volume_change_24h: float | None = None
    price_change_24h: float | None = None


@dataclass(frozen=True, slots=True)
class GeneralistTokenClaims:
    """A generalist provider's token claims — Yahoo's, today.

    Only the fields whose *concepts* match the native ones are
    comparable. Its `volume_24h` is a broader concept than tracked spot
    volume and is deliberately not here: it never enters this judgment,
    and its consumption is gated by the market-cap corroboration flag
    instead.
    """

    source: str
    observed_at: datetime | None

    market_cap: float | None = None
    circulating_supply: float | None = None

    #: The provider's asset-inception field. Judged semantically, not
    #: arithmetically: what it measures for a token was never
    #: established, and it has claimed six years of history for a token
    #: that began trading in 2024.
    inception: datetime | None = None


def judge(
    symbol: str,
    native: NativeTokenClaims | None,
    generalist: GeneralistTokenClaims | None,
) -> TokenMarketFacts:
    """Every claim about one token, judged into facts with standings."""

    return _Judgment(symbol, native, generalist).outcome()


class _Judgment:
    """One pass of the gate, accumulating facts and the rejection ledger."""

    def __init__(
        self,
        symbol: str,
        native: NativeTokenClaims | None,
        generalist: GeneralistTokenClaims | None,
    ) -> None:
        self._symbol = symbol.upper().strip()
        self._identity_mismatch: str | None = None
        self._native = self._identity_checked(native)
        self._generalist = generalist
        self._rejected: list[RejectedReading] = []
        self._yahoo_market_cap_corroborated = False

        #: Whether the native triad — price × circulating ≈ market cap
        #: — held. Vouches all three fields at once, which is what lets
        #: a single-source figure become established at all.
        self._triad_vouched = False
        self._triad_rejected = False
        self._supply_rejected = False

    # ── identity ────────────────────────────────────────────────────

    def _identity_checked(
        self,
        native: NativeTokenClaims | None,
    ) -> NativeTokenClaims | None:
        """Refuse the whole native set when it answers about another token."""

        if native is None:
            return None

        answered = native.symbol.upper().strip()

        if answered and answered != self._symbol:
            # Recorded once the ledger exists — deferred to outcome()
            # via this marker so the rejection carries the fact labels.
            self._identity_mismatch = answered
            return None

        return native

    # ── the outcome ─────────────────────────────────────────────────

    def outcome(self) -> TokenMarketFacts:
        if self._identity_mismatch:
            self._rejected.append(
                RejectedReading(
                    fact="market_cap",
                    label="Reading",
                    stated=f"an answer about {self._identity_mismatch}",
                    source="TokenInsight",
                    observed_at=None,
                    because=(
                        f"the provider answered about {self._identity_mismatch} "
                        f"when asked about {self._symbol} — an identity "
                        "mismatch rejects every claim in the reading."
                    ),
                )
            )

        self._check_internal_consistency()

        facts = {
            "market_cap": self._market_cap(),
            "circulating_supply": self._circulating(),
            "max_supply": self._max_supply(),
            "total_supply": self._total_supply(),
            "fully_diluted_valuation": self._fdv(),
            "price": self._price(),
            "rank": self._bare_native("rank", "rank"),
            "spot_volume_24h": self._bare_native(
                "spot_volume_24h",
                "tracked spot-market volume — a narrower concept than "
                "total trading volume, and it is not mapped onto one",
            ),
            "spot_volume_change_24h": self._bare_native(
                "spot_volume_change_24h",
                "a day-over-day movement of tracked spot volume — a "
                "dated observation, not a trend conclusion",
            ),
            "price_change_24h": self._bare_native(
                "price_change_24h",
                "a day-over-day price movement — a dated observation, "
                "not a trend conclusion",
            ),
            "project_age": self._project_age(),
        }

        return TokenMarketFacts(
            symbol=self._symbol,
            provider_id=self._native.provider_id if self._native else None,
            facts=tuple(facts[name] for name in TOKEN_FACTS),
            rejected=tuple(self._rejected),
            yahoo_market_cap_corroborated=self._yahoo_market_cap_corroborated,
            read=self._native.read if self._native else None,
        )

    # ── internal consistency ────────────────────────────────────────

    def _check_internal_consistency(self) -> None:
        """The native source's figures must reproduce each other.

        price × circulating ≈ market cap vouches all three at once; a
        failure rejects all three, because arithmetic cannot say which
        of them lied. circulating ≤ maximum is a hard rule of what the
        words mean.
        """

        native = self._native

        if native is None:
            return

        price = native.price
        circulating = native.circulating_supply
        market_cap = native.market_cap

        if price and circulating and market_cap:
            implied = price * circulating

            if _within(implied, market_cap, INTERNAL_TOLERANCE):
                self._triad_vouched = True
            else:
                self._reject_native_triad(implied)

        if (
            self._native is not None
            and native.circulating_supply
            and native.max_supply
            and native.circulating_supply > native.max_supply * (1 + COUNT_TOLERANCE)
        ):
            self._reject_native_supply_pair()

    def _reject_native_triad(self, implied: float) -> None:
        native = self._native
        assert native is not None

        because = (
            f"its own price × circulating supply implies "
            f"{_money(implied)}, which does not reproduce the "
            f"{_money(native.market_cap or 0.0)} it reports — arithmetic "
            "inconsistency rejects all three figures."
        )

        for fact, stated in (
            ("market_cap", _money(native.market_cap or 0.0)),
            ("price", _money(native.price or 0.0)),
            ("circulating_supply", _count(native.circulating_supply or 0.0)),
        ):
            self._rejected.append(
                RejectedReading(
                    fact=fact,
                    label=FACT_LABELS[fact],
                    stated=stated,
                    source=native.source,
                    observed_at=native.read.observed_at,
                    because=because,
                )
            )

        self._triad_rejected = True

    def _reject_native_supply_pair(self) -> None:
        native = self._native
        assert native is not None

        because = (
            "it reports more tokens circulating than its own stated "
            "maximum — the pair cannot both be true, and arithmetic "
            "cannot say which one is."
        )

        for fact, value in (
            ("circulating_supply", native.circulating_supply),
            ("max_supply", native.max_supply),
        ):
            self._rejected.append(
                RejectedReading(
                    fact=fact,
                    label=FACT_LABELS[fact],
                    stated=_count(value or 0.0),
                    source=native.source,
                    observed_at=native.read.observed_at,
                    because=because,
                )
            )

        self._supply_rejected = True

    # ── the judged facts ────────────────────────────────────────────

    def _market_cap(self) -> TokenFact:
        native = self._native
        claim = self._generalist_market_cap()

        native_value = (
            native.market_cap
            if native is not None and not self._triad_rejected
            else None
        )

        if native_value and self._triad_vouched:
            return self._establish_market_cap(native_value, claim)

        if native_value:
            # Present but unvouched: nothing checked it, so it is the
            # provider's claim and no more.
            return self._claimed(
                "market_cap",
                native_value,
                "nothing this platform holds reproduces or contradicts it",
            )

        if claim is not None:
            return self._claimed_generalist("market_cap", claim)

        return self._absent(
            "market_cap",
            "no source this platform reads reports a market value it "
            "is willing to serve.",
        )

    def _establish_market_cap(
        self,
        native_value: float,
        claim: tuple[float, GeneralistTokenClaims] | None,
    ) -> TokenFact:
        native = self._native
        assert native is not None

        vouched = (
            "its price × circulating supply reproduces it within "
            f"{INTERNAL_TOLERANCE:.0%}"
        )

        if claim is None:
            return self._established(
                "market_cap",
                native_value,
                f"{vouched}. No second source reports one.",
            )

        value, generalist = claim

        if _within(value, native_value, CROSS_TOLERANCE):
            self._yahoo_market_cap_corroborated = True

            return self._established(
                "market_cap",
                native_value,
                f"{vouched}, and {generalist.source} independently "
                "reports the same value.",
            )

        # The generalist disagrees with a figure that reproduces its
        # own arithmetic. The coherent claim stands; the bare one is
        # rejected and retained — it must not silently disappear.
        self._rejected.append(
            RejectedReading(
                fact="market_cap",
                label=FACT_LABELS["market_cap"],
                stated=_money(value),
                source=generalist.source,
                observed_at=generalist.observed_at,
                because=(
                    f"it conflicts with the corroborated market value of "
                    f"{_money(native_value)} by a factor of "
                    f"{_factor(native_value, value)} and offers no "
                    "arithmetic of its own to check."
                ),
            )
        )

        return self._established(
            "market_cap",
            native_value,
            f"{vouched}. {generalist.source}'s conflicting figure failed "
            "validation and is retained below.",
        )

    def _generalist_market_cap(
        self,
    ) -> tuple[float, GeneralistTokenClaims] | None:
        generalist = self._generalist

        if generalist is None or not generalist.market_cap:
            return None

        return generalist.market_cap, generalist

    def _circulating(self) -> TokenFact:
        native = self._native

        native_value = (
            native.circulating_supply
            if native is not None
            and not self._triad_rejected
            and not self._supply_rejected
            else None
        )

        generalist = self._generalist
        other = (
            generalist.circulating_supply
            if generalist is not None and generalist.circulating_supply
            else None
        )

        if native_value and self._triad_vouched:
            if other is not None and not _within(other, native_value, COUNT_TOLERANCE):
                self._rejected.append(
                    RejectedReading(
                        fact="circulating_supply",
                        label=FACT_LABELS["circulating_supply"],
                        stated=_count(other),
                        source=generalist.source if generalist else "",
                        observed_at=(generalist.observed_at if generalist else None),
                        because=(
                            "it conflicts with the corroborated circulating "
                            f"supply of {_count(native_value)} — the count "
                            "that reproduces the market value."
                        ),
                    )
                )

                return self._established(
                    "circulating_supply",
                    native_value,
                    "it reproduces the market value with the price. The "
                    "conflicting count is retained below.",
                )

            corroborated = other is not None and _within(
                other, native_value, COUNT_TOLERANCE
            )

            return self._established(
                "circulating_supply",
                native_value,
                (
                    "it reproduces the market value with the price, and "
                    "the second source reports the same count."
                    if corroborated
                    else "it reproduces the market value with the price."
                ),
            )

        if native_value:
            return self._claimed(
                "circulating_supply",
                native_value,
                "nothing this platform holds reproduces or contradicts it",
            )

        if other is not None and self._generalist is not None:
            return self._claimed_generalist(
                "circulating_supply",
                (other, self._generalist),
            )

        return self._absent(
            "circulating_supply",
            "no source this platform reads reports one.",
        )

    def _max_supply(self) -> TokenFact:
        native = self._native

        native_value = (
            native.max_supply
            if native is not None and not self._supply_rejected
            else None
        )

        if native_value is None:
            return self._absent(
                "max_supply",
                "the token states no maximum supply, or no source "
                "reports one — with no cap there is no issuance "
                "schedule to measure.",
            )

        # A maximum supply is vouched by the fully diluted valuation
        # reproducing price × maximum: two further fields agreeing on
        # the same count.
        if self._fdv_coheres():
            return self._established(
                "max_supply",
                native_value,
                "price × maximum supply reproduces the fully diluted "
                f"valuation within {INTERNAL_TOLERANCE:.0%}.",
            )

        return self._claimed(
            "max_supply",
            native_value,
            "no second figure reproduces it",
        )

    def _total_supply(self) -> TokenFact:
        return self._absent(
            "total_supply",
            "the crypto-native provider's endpoint publishes no total "
            "supply, and no other source is read for one.",
        )

    def _fdv_coheres(self) -> bool:
        native = self._native

        if (
            native is None
            or self._triad_rejected
            or not native.price
            or not native.max_supply
            or not native.fully_diluted_valuation
        ):
            return False

        return _within(
            native.price * native.max_supply,
            native.fully_diluted_valuation,
            INTERNAL_TOLERANCE,
        )

    def _fdv(self) -> TokenFact:
        native = self._native

        value = native.fully_diluted_valuation if native is not None else None

        if not value:
            return self._absent(
                "fully_diluted_valuation",
                "no source this platform reads reports one.",
            )

        if self._fdv_coheres():
            return self._established(
                "fully_diluted_valuation",
                value,
                "price × maximum supply reproduces it within "
                f"{INTERNAL_TOLERANCE:.0%}.",
            )

        if (
            native is not None
            and native.price
            and native.max_supply
            and not self._triad_rejected
        ):
            # Checkable and failed: rejected, not merely unproven.
            assert native is not None
            self._rejected.append(
                RejectedReading(
                    fact="fully_diluted_valuation",
                    label=FACT_LABELS["fully_diluted_valuation"],
                    stated=_money(value),
                    source=native.source,
                    observed_at=native.read.observed_at,
                    because=(
                        "price × maximum supply implies "
                        f"{_money(native.price * native.max_supply)}, which "
                        "does not reproduce it — arithmetic inconsistency."
                    ),
                )
            )

            return self._absent(
                "fully_diluted_valuation",
                "the reported figure failed its own arithmetic and is retained below.",
            )

        return self._claimed(
            "fully_diluted_valuation",
            value,
            "the figures that would check it are not all reported",
        )

    def _price(self) -> TokenFact:
        native = self._native

        value = (
            native.price if native is not None and not self._triad_rejected else None
        )

        if not value:
            return self._absent(
                "price",
                "the crypto-native provider reports none this platform "
                "is willing to serve.",
            )

        if self._triad_vouched:
            return self._established(
                "price",
                value,
                "it reproduces the market value with the circulating supply.",
            )

        return self._claimed(
            "price",
            value,
            "nothing this platform holds reproduces or contradicts it",
        )

    def _project_age(self) -> TokenFact:
        """Project age is unknown until a source with established semantics exists.

        The generalist's inception field claimed six years of history
        for a token that began trading in 2024 — what that field
        measures for a token was never established, so a date read from
        it establishes nothing. The crypto-native provider publishes no
        project start date. An observed-price-history length is a
        different concept and is never presented as age.
        """

        generalist = self._generalist

        if generalist is not None and generalist.inception is not None:
            self._rejected.append(
                RejectedReading(
                    fact="project_age",
                    label=FACT_LABELS["project_age"],
                    stated=generalist.inception.date().isoformat(),
                    source=generalist.source,
                    observed_at=generalist.observed_at,
                    because=(
                        "what this field measures for a token was never "
                        "established — it has claimed six years of history "
                        "for a token that began trading in 2024 — so a "
                        "date read from it establishes nothing."
                    ),
                )
            )

            return self._absent(
                "project_age",
                "the one field that claimed a start date has "
                "unestablished semantics and was rejected; the "
                "crypto-native provider publishes none. Unknown is the "
                "honest answer.",
            )

        return self._absent(
            "project_age",
            "no source this platform reads publishes a project start "
            "date. Unknown is the honest answer.",
        )

    # ── constructors ────────────────────────────────────────────────

    def _established(self, fact: str, value: float, because: str) -> TokenFact:
        native = self._native
        assert native is not None

        return TokenFact(
            fact=fact,
            standing=TokenFactStanding.ESTABLISHED,
            value=value,
            source=native.source,
            observed_at=native.read.observed_at,
            because=because,
        )

    def _claimed(self, fact: str, value: float, because: str) -> TokenFact:
        native = self._native
        assert native is not None

        return TokenFact(
            fact=fact,
            standing=TokenFactStanding.CLAIMED,
            value=value,
            source=native.source,
            observed_at=native.read.observed_at,
            because=f"{native.source} reports it; {because}.",
        )

    def _claimed_generalist(
        self,
        fact: str,
        claim: tuple[float, GeneralistTokenClaims],
    ) -> TokenFact:
        value, generalist = claim

        return TokenFact(
            fact=fact,
            standing=TokenFactStanding.CLAIMED,
            value=value,
            source=generalist.source,
            observed_at=generalist.observed_at,
            because=(
                f"{generalist.source} reports it; nothing this platform "
                "holds reproduces or contradicts it."
            ),
        )

    def _bare_native(self, fact: str, meaning: str) -> TokenFact:
        """A figure only the native provider reports and nothing checks."""

        native = self._native

        value = getattr(native, fact, None) if native is not None else None

        if value is None:
            return self._absent(
                fact,
                "the crypto-native provider does not report it for this token.",
            )

        return self._claimed(fact, float(value), meaning)

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


def _factor(one: float, other: float) -> str:
    """How far apart two figures are, as a reader checks it."""

    if not one or not other:
        return "∞"

    ratio = max(one, other) / min(one, other)

    if ratio >= 1000:
        return f"{ratio:,.0f}"

    return f"{ratio:,.1f}"


def _money(value: float) -> str:
    """An amount at a unit that shows it — including a nonsense one."""

    if value >= 1_000_000_000:
        return f"${value / 1_000_000_000:,.1f}bn"

    if value >= 1_000_000:
        return f"${value / 1_000_000:,.0f}m"

    return f"${value:,.0f}"


def _count(value: float) -> str:
    return f"{value:,.0f}"
