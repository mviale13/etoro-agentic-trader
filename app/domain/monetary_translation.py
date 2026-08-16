"""An established amount in one currency, carried across to another.

C6. The monetary comparison boundary (#143) left an honest gap: a
market cap established in CHF is *refused* against the USD threshold,
pending an authorised conversion this platform did not hold. This
module is that authorisation — and nothing more.

The governing rule:

    An established monetary amount in one currency becomes comparable
    with an established threshold in another currency only through an
    explicit, evidenced FX translation. The translation never alters
    the original fact: it creates a derived monetary claim that
    carries its own evidence, and the original remains the provider
    fact beside it.

Three properties this type enforces structurally rather than by
convention:

- **Direction is part of the rate, not a label around a float.**
  A `MonetaryTranslation` cannot be constructed from a rate whose base
  is not the original's currency — handing a USD→CHF rate to a CHF
  amount raises rather than producing a numerically plausible wrong
  answer. `ExchangeRate` already says how many units of `quote` one
  unit of `base` buys; this module refuses to let that sentence be
  read backwards.

- **A translated amount cannot exist without its evidence.** The
  derived USD figure is computed here, from the original and the rate,
  at construction — there is no constructor parameter through which an
  unevidenced number could arrive, and the derivation is printable:
  `CHF 208,375,545,856 × [CHF→USD 1.2402, Yahoo Finance, observed
  2026-08-16] = USD 258,427,301,900`.

- **Time is part of the evidence.** The temporal rule, chosen from
  what this platform actually stores rather than invented (see
  MONETARY_TRANSLATION.md §2): the rate observation and the market-cap
  observation must share a **UTC calendar day** — the acquisition
  cadence both stores already declare with `is_from_today()`. Neither
  stored record currently evidences its own market-effective instant
  (both carry the read time; the provider's `regularMarketTime` and
  the FX close's own date exist and are unread), so a finer rule would
  be about evidence this platform does not hold. A rate from another
  day — including a last-known rate served after a provider failure —
  makes the translation *unauthorised*, and the derived amount is
  withheld rather than computed from stale evidence. "Latest FX" is
  never silently applied to an older observation, in either direction.

Translation authority is a **fourth crossing**, separate from
identity, magnitude and denomination, and it can never rescue one of
them: the comparison conjunction consults it last, only where every
earlier crossing already holds and the currencies differ.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, date, datetime

from app.domain.exchange_rate import ExchangeRate
from app.domain.monetary import MonetaryAmount

#: The currencies this platform translates into USD, and the only
#: ones: the measured established-foreign population of the market-cap
#: corpus (#142/#143 — EUR, DKK, CHF, and BP.L's GBP). Not a universal
#: FX capability: a fifth currency joins by measurement and a re-pin,
#: not by an edit. Governed by `fx-translation@1`.
TRANSLATABLE_TO_USD: tuple[str, ...] = ("CHF", "DKK", "EUR", "GBP")


def _day(moment: datetime) -> date:
    """The UTC calendar day an observation belongs to."""

    if moment.tzinfo is None:
        # A naive timestamp is read as UTC rather than local: every
        # Provenance on this platform is written tz-aware in UTC, so a
        # naive one is a restored legacy record whose writer meant UTC.
        return moment.date()

    return moment.astimezone(UTC).date()


@dataclass(frozen=True, slots=True)
class MonetaryTranslation:
    """One amount, one directional rate, and whether they may combine.

    Constructible only from coherent evidence — the rate's base must be
    the original's currency — and *usable* only when authorised: the
    derived amount is exposed through `translated`, which answers
    nothing while the temporal rule fails. Both facts survive either
    way: the original amount untouched, and the rate with its own date,
    so a refusal can say exactly what was held and why it was not
    enough.
    """

    #: The provider fact, exactly as established. Never altered.
    original: MonetaryAmount

    #: The evidenced rate, direction and provenance included:
    #: `rate.rate` units of `rate.quote` per one `rate.base`.
    rate: ExchangeRate

    #: When the *subject* of the translation was observed — the market
    #: cap's own reading time, not the rate's. The temporal rule
    #: compares this with the rate's observation.
    subject_observed_at: datetime

    def __post_init__(self) -> None:
        if self.rate.base != self.original.currency:
            raise ValueError(
                f"a {self.rate.base}→{self.rate.quote} rate cannot translate "
                f"a {self.original.currency} amount; an inverted or "
                "mismatched pair must fail here, loudly, rather than "
                "produce a numerically plausible wrong answer"
            )

        if self.rate.rate <= 0:
            raise ValueError("a non-positive rate is not a measurement")

    @property
    def target(self) -> str:
        """The currency the derived claim is expressed in."""

        return self.rate.quote

    @property
    def temporally_compatible(self) -> bool:
        """Whether the rate and the subject were observed on one UTC day.

        The rule this platform's evidence supports — both stores read
        once a day and re-read the next — and no finer one, because
        neither record evidences its own market-effective instant yet.
        """

        return _day(self.rate.reading.observed_at) == _day(self.subject_observed_at)

    @property
    def authorised(self) -> bool:
        """Whether the derived amount may be used at all.

        Direction and evidence are guaranteed by construction; what
        remains is time. A rate served as last-known after a provider
        failure keeps its original observation date and fails here
        naturally — no special case, and no fallback.
        """

        return self.temporally_compatible

    @property
    def translated(self) -> MonetaryAmount | None:
        """The derived claim, only while its authorisation holds."""

        if not self.authorised:
            return None

        return MonetaryAmount(
            amount=self.rate.convert(self.original.amount),
            currency=self.target,
        )

    @property
    def stated(self) -> str:
        """The derivation, printable — or the refusal, worded.

        The inspectable form C6 requires: a reader sees the original,
        the rate with its source and date, and the product — without
        the original being lost, and without any surface recomputing
        the arithmetic.
        """

        observed = _day(self.rate.reading.observed_at).isoformat()

        derived = self.translated

        if derived is not None:
            return (
                f"{self.original.stated} × [{self.rate.base}→{self.rate.quote} "
                f"{self.rate.rate:.6g}, {self.rate.reading.source}, observed "
                f"{observed}] = {derived.stated}"
            )

        return (
            f"{self.original.stated} holds a {self.rate.base}→{self.rate.quote} "
            f"rate from {self.rate.reading.source} observed {observed}, but the "
            f"amount itself was observed "
            f"{_day(self.subject_observed_at).isoformat()} — a rate from a "
            "different day is not evidence about this observation, so the "
            "translation is refused rather than computed from stale evidence."
        )
