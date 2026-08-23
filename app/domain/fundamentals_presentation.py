"""The dossier's fundamentals, each figure under its honest authority.

The owner's ruling of 2026-08-23: a dossier must not display repeated
"not established" rows when this platform already holds useful
provider-reported financial information. So every metric here is
selected under one precedence — **filing-established evidence first,
provider-reported fallback second, the exact refusal or absence third**
— and the selection is worn on the row, not implied by it.

What this layer is not. It is not a third analytical route, and it does
not blend the two that exist: a provider value never becomes
filing-established evidence, never overwrites one, never raises the
quality authority to grounded, never removes a named evidence gap, and
cannot enlarge a capital-action envelope. The filing analysts still
read `FinancialUnderstanding` and nothing else; the provider-fed
analysts still read `CompanyFacts` and nothing else. This module reads
both *outputs* and decides only what a page prints — which is why it
lives beside `investor_assessment` and `decision_synthesis` rather
than beside either route.

Two honesty rules the ruling states and this module enforces:

- **Currency is never inferred.** A cash flow's denomination comes from
  the provider's own `financialCurrency` field carried on the stored
  snapshot, or it is absent — never from the ticker, the exchange or
  the company's domicile. Yahoo's quote `currency` for BP.L is GBp
  while its financials are reported in USD, which is the whole case.
- **A period is never guessed.** The stored provider record states no
  reporting period for its figures, so none is printed: not FY, not
  annual, not TTM. "Reporting period not stated by the stored record"
  is the maximum claim.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC
from enum import StrEnum

from app.domain.financial_understanding import (
    FinancialMeasure,
    FinancialUnderstanding,
    MeasureUnit,
)
from app.domain.valuation_snapshot import ValuationSnapshot


class FundamentalStanding(StrEnum):
    """Whose figure a row shows, or why it shows none."""

    #: Read out of the filing, checked against the cells it sits in,
    #: settled across repeated readings. The strongest authority this
    #: platform has, and the one every other standing defers to.
    FILING_EVIDENCE = "filing_evidence"

    #: The provider's reported value, shown because the filing
    #: establishes nothing here. Descriptive, labelled, and not
    #: evidence: the filing-grade gap it stands in front of still
    #: stands.
    PROVIDER_FALLBACK = "provider_fallback"

    #: The provider's last successful reading, served because the most
    #: recent attempt failed. The same fallback, older, and marked —
    #: age alone cannot tell these apart.
    LAST_KNOWN_PROVIDER_FALLBACK = "last_known_provider_fallback"

    #: Neither route holds a figure. The reason is worded, and where
    #: the filing route refused in its own words those words are kept.
    UNAVAILABLE = "unavailable"

    #: A provider figure exists and is not shown, for the named reason
    #: — the stored snapshot does not identify what the provider
    #: answered about, and an unattributable number is not a fallback.
    REFUSED = "refused"


@dataclass(frozen=True, slots=True)
class FundamentalFact:
    """One metric, its figure where one is shown, and its account."""

    #: The stable key a surface groups by, e.g. "gross_margin".
    metric: str

    #: The investor's name for it, e.g. "Gross margin".
    label: str

    #: The figure, read through `unit`. None exactly where the standing
    #: shows none — and a measured zero is a figure, never an absence.
    value: float | None

    #: "fraction" (a percentage), "multiple" (times), or "currency"
    #: (an absolute amount, denominated by `currency` where that was
    #: established and by nothing where it was not).
    unit: str

    standing: FundamentalStanding

    #: Who reported the figure — the filing citation for evidence, the
    #: provider's name for a fallback. None where nothing is shown.
    source: str | None

    #: When: the filing route's own reading account, or the provider
    #: snapshot's receipt date worded as one. None where nothing is
    #: shown.
    as_of: str | None

    #: ISO currency code where the provider's own record establishes
    #: one. Only meaningful for `unit == "currency"`, and never
    #: inferred.
    currency: str | None

    #: The reporting period, where established. The stored provider
    #: record establishes none, so a fallback always carries None here
    #: and the sentence says so.
    period: str | None

    #: One concise sentence an investor reads under the figure.
    because: str

    #: The filing arithmetic as an investor would check it, for
    #: FILING_EVIDENCE rows only.
    stated: str | None = None

    def __post_init__(self) -> None:
        showing = self.standing in (
            FundamentalStanding.FILING_EVIDENCE,
            FundamentalStanding.PROVIDER_FALLBACK,
            FundamentalStanding.LAST_KNOWN_PROVIDER_FALLBACK,
        )

        if showing and self.value is None:
            raise ValueError(
                f"{self.standing} shows a figure, and {self.metric} has none"
            )

        if not showing and self.value is not None:
            raise ValueError(
                f"{self.standing} shows no figure, and {self.metric} has one"
            )

        if not self.because.strip():
            raise ValueError("every fundamentals row carries its account in words")


#: The section's metrics, in display order: key, label, unit, the
#: filing measure that answers it where one exists, and the snapshot
#: field that reports it.
#:
#: Two deliberate absences. `debt_to_equity` names no filing measure:
#: the filing route establishes LIABILITIES_TO_EQUITY, a larger and
#: different quantity, and presenting it under this label would be the
#: restatement-in-the-right-label move the measure's own docstring
#: shuts out. And the two P/E rows name none because no filing states
#: a market multiple — both are provider observations by nature, and
#: neither is a valuation judgment (VALUATION_AUTHORITY.md still
#: holds: a multiple is an observation; "cheap" is a conclusion this
#: platform does not draw).
METRICS: tuple[tuple[str, str, MeasureUnit, FinancialMeasure | None, str], ...] = (
    (
        "revenue_growth",
        "Revenue growth",
        MeasureUnit.FRACTION,
        FinancialMeasure.REVENUE_GROWTH,
        "revenue_growth",
    ),
    (
        "earnings_growth",
        "Earnings growth",
        MeasureUnit.FRACTION,
        FinancialMeasure.EARNINGS_GROWTH,
        "earnings_growth",
    ),
    (
        "gross_margin",
        "Gross margin",
        MeasureUnit.FRACTION,
        FinancialMeasure.GROSS_MARGIN,
        "gross_margin",
    ),
    (
        "operating_margin",
        "Operating margin",
        MeasureUnit.FRACTION,
        FinancialMeasure.OPERATING_MARGIN,
        "operating_margin",
    ),
    (
        "net_margin",
        "Net margin",
        MeasureUnit.FRACTION,
        FinancialMeasure.NET_MARGIN,
        "net_margin",
    ),
    (
        "return_on_equity",
        "Return on equity",
        MeasureUnit.FRACTION,
        None,
        "return_on_equity",
    ),
    (
        "current_ratio",
        "Current ratio",
        MeasureUnit.MULTIPLE,
        FinancialMeasure.CURRENT_RATIO,
        "current_ratio",
    ),
    (
        "debt_to_equity",
        "Debt-to-equity",
        MeasureUnit.MULTIPLE,
        None,
        "debt_to_equity",
    ),
    (
        "operating_cash_flow",
        "Operating cash flow",
        MeasureUnit.CURRENCY,
        FinancialMeasure.OPERATING_CASH_FLOW,
        "operating_cash_flow",
    ),
    (
        "free_cash_flow",
        "Free cash flow",
        MeasureUnit.CURRENCY,
        FinancialMeasure.FREE_CASH_FLOW,
        "free_cash_flow",
    ),
    ("trailing_pe", "Trailing P/E", MeasureUnit.MULTIPLE, None, "trailing_pe"),
    ("forward_pe", "Forward P/E", MeasureUnit.MULTIPLE, None, "forward_pe"),
)


def fundamentals_for(
    financial: FinancialUnderstanding | None,
    snapshot: ValuationSnapshot | None,
) -> tuple[FundamentalFact, ...]:
    """Every metric of the section, selected under the ruled precedence.

    Deterministic and read-only: both inputs are what the stores
    already hold, and calling this acquires nothing, writes nothing and
    asks no model. A snapshot that was never read arrives as None (or
    as the unread sentinel, whose reading is None) and simply offers no
    fallback — the filing route's own words then stand, exactly as they
    did before this layer existed.
    """

    offered = (
        snapshot if snapshot is not None and snapshot.reading is not None else None
    )

    return tuple(
        _select(metric, label, unit, measure, field, financial, offered)
        for metric, label, unit, measure, field in METRICS
    )


#: The two growth metrics carry their authority in their name — the
#: owner's ruling of 2026-08-23, after the measurement showed the
#: filing's fiscal-year growth and the provider's undocumented-window
#: growth to be non-comparable measurements. Everywhere one of these
#: rows shows a figure, the label says whose window it is; the other
#: ten metrics keep their #240 names, because renaming them is the
#: broader question this slice does not open.
_GROWTH_NAMES = {
    "revenue_growth": (
        "Revenue growth — FY filing",
        "Provider-reported revenue growth — period not stated",
    ),
    "earnings_growth": (
        "Earnings growth — FY filing",
        "Provider-reported earnings growth — period not stated",
    ),
}

#: The clause every provider growth row carries, verbatim — the same
#: sentence the growth analyst now words its own evidence with.
_GROWTH_UNSTATED = (
    "The stored provider record states neither its reporting period nor its formula."
)


def _select(
    metric: str,
    label: str,
    unit: MeasureUnit,
    measure: FinancialMeasure | None,
    field: str,
    financial: FinancialUnderstanding | None,
    snapshot: ValuationSnapshot | None,
) -> FundamentalFact:
    # ── 1. filing evidence wins whenever established ────────────────
    filing_absence: str | None = None

    if financial is not None and measure is not None:
        established = next(
            (item for item in financial.measures if item.measure is measure),
            None,
        )

        if established is not None and established.value is not None:
            return FundamentalFact(
                metric=metric,
                label=(_GROWTH_NAMES[metric][0] if metric in _GROWTH_NAMES else label),
                value=established.value,
                unit=established.unit.value,
                standing=FundamentalStanding.FILING_EVIDENCE,
                source=financial.source,
                as_of=financial.reading.source,
                # A filing figure is denominated and dated by the
                # statement it sits in; both travel inside `source` and
                # `stated` in the filer's own terms, and no code here
                # asserts either separately.
                currency=None,
                period=None,
                because=(
                    "Established from the filing itself, checked against "
                    "the cells the figures sit in."
                ),
                stated=established.stated,
            )

        if established is not None:
            filing_absence = established.absent_because

    # ── 2. otherwise, an admissible stored provider value ───────────
    value = getattr(snapshot, field, None) if snapshot is not None else None

    if snapshot is not None and value is not None:
        assert snapshot.reading is not None  # the caller's offered gate

        if snapshot.vendor_identity is None:
            # A figure the store cannot attribute to a vendor claim
            # about *this* security is not served as one. Identity is
            # enforced before the reading (Invariant 2), and the
            # fallback route earns no exemption.
            return FundamentalFact(
                metric=metric,
                label=label,
                value=None,
                unit=unit.value,
                standing=FundamentalStanding.REFUSED,
                source=None,
                as_of=None,
                currency=None,
                period=None,
                because=(
                    "A provider figure is held but not shown: the stored "
                    "snapshot does not identify what the provider answered "
                    "about, and an unattributable number is not a fallback."
                ),
            )

        received = f"{snapshot.reading.observed_at.astimezone(UTC):%Y-%m-%d}"

        last_known = snapshot.reading.last_known

        currency = snapshot.financial_currency if unit is MeasureUnit.CURRENCY else None

        sentences = [
            "Not established from the filing."
            if filing_absence is not None
            else "No filing measure answers this metric.",
            (
                f"{snapshot.reading.source} reported this value; the reading "
                f"is the last known — the most recent attempt to refresh it "
                f"failed — received {received}."
                if last_known
                else (
                    f"{snapshot.reading.source} provider snapshot, received {received}."
                )
            ),
        ]

        if metric in _GROWTH_NAMES:
            sentences.append(_GROWTH_UNSTATED)

        if unit is MeasureUnit.CURRENCY:
            sentences.append(
                "Reporting period not stated by the stored record."
                + (
                    " Currency not stated by the stored record."
                    if currency is None
                    else ""
                )
            )

        return FundamentalFact(
            metric=metric,
            label=(_GROWTH_NAMES[metric][1] if metric in _GROWTH_NAMES else label),
            value=value,
            unit=unit.value,
            standing=(
                FundamentalStanding.LAST_KNOWN_PROVIDER_FALLBACK
                if last_known
                else FundamentalStanding.PROVIDER_FALLBACK
            ),
            source=snapshot.reading.source,
            as_of=f"received {received}",
            currency=currency,
            period=None,
            because=" ".join(sentences),
        )

    # ── 3. otherwise, the exact refusal or absence, preserved ───────
    return FundamentalFact(
        metric=metric,
        label=label,
        value=None,
        unit=unit.value,
        standing=FundamentalStanding.UNAVAILABLE,
        source=None,
        as_of=None,
        currency=None,
        period=None,
        because=(
            filing_absence
            if filing_absence is not None
            else "No stored provider snapshot carries this figure, and no "
            "filing measure answers it."
        ),
    )
