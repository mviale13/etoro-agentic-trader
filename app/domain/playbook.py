"""How the Artificial CIO believes a company should be understood."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from app.domain.research_plan import AnalystKey


class PlaybookKind(StrEnum):
    """
    The kind of investment this is, as far as the evidence establishes it.

    Every one of these is a *structural* fact about the security — what it
    is — read from its asset class and the industry its provider reports.
    None of them is a judgement about how the business is behaving: a
    "quality compounder" and a "turnaround" can sit in the same industry,
    and telling them apart is an assessment this does not attempt.

    `GENERAL_CORPORATE` is the honest default for a company whose industry
    this platform has no specialised reading for. `UNCLASSIFIED` is the
    different absence: the provider reported no industry at all, so even
    the default was not chosen on evidence.
    """

    SOFTWARE = "software"
    PLATFORM = "platform"
    SEMICONDUCTOR = "semiconductor"
    BANK = "bank"
    INSURANCE = "insurance"
    ASSET_MANAGER = "asset_manager"
    REIT = "reit"
    UTILITIES = "utilities"
    ENERGY = "energy"
    MINING = "mining"
    PHARMA = "pharma"
    AEROSPACE_DEFENCE = "aerospace_defence"
    DIGITAL_ASSET = "digital_asset"
    FUND = "fund"
    GENERAL_CORPORATE = "general_corporate"
    UNCLASSIFIED = "unclassified"


@dataclass(frozen=True, slots=True)
class PlaybookExclusion:
    """An analyst this playbook deliberately does not run, and why.

    Stated rather than omitted. A reader who sees four analyst verdicts
    where another security has five cannot otherwise tell a question this
    platform declined to ask from one it failed to answer — and those
    mean opposite things about the case in front of them.
    """

    analyst: AnalystKey
    reason: str


@dataclass(frozen=True, slots=True)
class InvestmentPlaybook:
    """
    The framework this security is evaluated with, and what it covers.

    A sector says what a company sells. A playbook says how it should be
    read, which is the thing that actually determines the analysis: a bank
    judged on gross margin and a property trust judged on earnings growth
    are both being measured with the wrong instrument.

    This is the explanation, not the instruction. The `ResearchPlan` built
    from it is what the executor runs, so what the investor is shown here
    and what the analysts were asked cannot drift apart.
    """

    kind: PlaybookKind

    #: What this playbook is called, as the investor reads it.
    name: str

    #: How this security is understood, in one sentence.
    explanation: str

    #: What it is analysed primarily for.
    priorities: tuple[str, ...]

    #: The analysts this playbook runs, in the order it asks them.
    analysts: tuple[AnalystKey, ...]

    #: The analysts it does not run, each with the reason it does not.
    excluded: tuple[PlaybookExclusion, ...] = ()

    @property
    def is_classified(self) -> bool:
        """Whether the security's kind was established from evidence."""

        return self.kind is not PlaybookKind.UNCLASSIFIED


#: The four analysts a company with ordinary financial statements gets.
_FUNDAMENTALS = (
    AnalystKey.GROWTH,
    AnalystKey.PROFITABILITY,
    AnalystKey.BALANCE_SHEET,
    AnalystKey.CASH_FLOW,
)


def _corporate(
    kind: PlaybookKind,
    name: str,
    explanation: str,
    priorities: tuple[str, ...],
) -> InvestmentPlaybook:
    """A playbook that reads ordinary company accounts in full."""

    return InvestmentPlaybook(
        kind=kind,
        name=name,
        explanation=explanation,
        priorities=priorities,
        analysts=_FUNDAMENTALS,
    )


#: Every playbook this platform can apply, by kind.
#:
#: The analyst sets differ only where the difference is defensible from
#: what this platform can actually read. A bank's cash flow statement and
#: a property trust's margins are not merely less useful — they measure
#: something other than what the reader takes them to measure — so those
#: analysts are declined, with the reason. Where a playbook would need a
#: figure the provider does not report (a bank's capital ratios, a miner's
#: reserve life), no analyst is invented to stand in for it.
PLAYBOOKS: dict[PlaybookKind, InvestmentPlaybook] = {
    PlaybookKind.SOFTWARE: _corporate(
        PlaybookKind.SOFTWARE,
        "Software",
        "Evaluated as a software business: recurring revenue, the margin "
        "it converts to cash, and the balance sheet behind it.",
        (
            "Revenue growth and its durability",
            "Gross and operating margin",
            "Cash conversion",
            "Balance sheet strength",
        ),
    ),
    PlaybookKind.PLATFORM: _corporate(
        PlaybookKind.PLATFORM,
        "Platform",
        "Evaluated as a platform business: scale economics, the margin "
        "that scale produces, and the cash it generates.",
        (
            "Revenue growth",
            "Operating leverage",
            "Cash generation",
            "Balance sheet strength",
        ),
    ),
    PlaybookKind.SEMICONDUCTOR: _corporate(
        PlaybookKind.SEMICONDUCTOR,
        "Semiconductor",
        "Evaluated as a semiconductor business, where earnings move with "
        "a cycle: margin through that cycle, and the balance sheet that "
        "has to carry it.",
        (
            "Growth through the cycle",
            "Margin at the trough",
            "Capital intensity",
            "Balance sheet resilience",
        ),
    ),
    PlaybookKind.AEROSPACE_DEFENCE: _corporate(
        PlaybookKind.AEROSPACE_DEFENCE,
        "Aerospace & Defence",
        "Evaluated as a long-cycle contractor: order-driven growth, "
        "programme profitability and the cash a long contract consumes "
        "before it returns any.",
        (
            "Order-driven growth",
            "Programme profitability",
            "Cash conversion",
            "Balance sheet strength",
        ),
    ),
    PlaybookKind.PHARMA: _corporate(
        PlaybookKind.PHARMA,
        "Pharmaceuticals",
        "Evaluated as a pharmaceutical business: the profitability of "
        "what is on the market today, and the balance sheet that funds "
        "what follows it.",
        (
            "Revenue growth",
            "Profitability",
            "Cash generation",
            "Balance sheet strength",
        ),
    ),
    PlaybookKind.UTILITIES: _corporate(
        PlaybookKind.UTILITIES,
        "Utilities",
        "Evaluated as a regulated utility: steady returns on a large "
        "asset base, and the debt that base is financed with.",
        (
            "Stability of earnings",
            "Regulated returns",
            "Balance sheet leverage",
            "Cash generation",
        ),
    ),
    PlaybookKind.ENERGY: _corporate(
        PlaybookKind.ENERGY,
        "Energy",
        "Evaluated as a commodity producer: a cycle it does not control, "
        "the cost position it meets that cycle with, and the balance "
        "sheet that survives the trough.",
        (
            "Position on the cost curve",
            "Profitability through the cycle",
            "Capital discipline",
            "Balance sheet resilience",
        ),
    ),
    PlaybookKind.MINING: _corporate(
        PlaybookKind.MINING,
        "Mining",
        "Evaluated as a commodity producer: a cycle it does not control, "
        "the cost position it meets that cycle with, and the balance "
        "sheet that survives the trough.",
        (
            "Position on the cost curve",
            "Profitability through the cycle",
            "Capital discipline",
            "Balance sheet resilience",
        ),
    ),
    PlaybookKind.GENERAL_CORPORATE: _corporate(
        PlaybookKind.GENERAL_CORPORATE,
        "General Corporate",
        "Evaluated with this platform's default company framework. Its "
        "industry has no specialised reading here, so it is read on the "
        "ordinary accounts rather than through a lens chosen for it.",
        (
            "Earnings growth",
            "Profitability",
            "Balance sheet strength",
            "Cash generation",
        ),
    ),
    PlaybookKind.BANK: InvestmentPlaybook(
        kind=PlaybookKind.BANK,
        name="Bank",
        explanation=(
            "Evaluated as a bank, whose balance sheet is its business "
            "rather than a support for it. A bank is not judged on the "
            "margins an industrial is judged on."
        ),
        priorities=(
            "Balance sheet strength",
            "Profitability on assets and equity",
            "Growth in lending",
        ),
        analysts=(
            AnalystKey.GROWTH,
            AnalystKey.PROFITABILITY,
            AnalystKey.BALANCE_SHEET,
        ),
        excluded=(
            PlaybookExclusion(
                analyst=AnalystKey.CASH_FLOW,
                reason=(
                    "A bank's operating cash flow is dominated by deposit "
                    "and lending flows, so it does not measure cash "
                    "generation the way it does for an industrial."
                ),
            ),
        ),
    ),
    PlaybookKind.INSURANCE: InvestmentPlaybook(
        kind=PlaybookKind.INSURANCE,
        name="Insurance",
        explanation=(
            "Evaluated as an insurer, which earns on underwriting and on "
            "the float it invests, and whose balance sheet carries the "
            "claims it has yet to pay."
        ),
        priorities=(
            "Balance sheet strength",
            "Profitability",
            "Premium growth",
        ),
        analysts=(
            AnalystKey.GROWTH,
            AnalystKey.PROFITABILITY,
            AnalystKey.BALANCE_SHEET,
        ),
        excluded=(
            PlaybookExclusion(
                analyst=AnalystKey.CASH_FLOW,
                reason=(
                    "An insurer's operating cash flow moves with premiums "
                    "received against claims paid, so it does not measure "
                    "cash generation the way it does for an industrial."
                ),
            ),
        ),
    ),
    PlaybookKind.ASSET_MANAGER: InvestmentPlaybook(
        kind=PlaybookKind.ASSET_MANAGER,
        name="Asset Manager",
        explanation=(
            "Evaluated as a manager of other people's money: fee income "
            "on assets under management, and the margin that fee earns."
        ),
        priorities=(
            "Growth in fee income",
            "Operating margin",
            "Balance sheet strength",
        ),
        analysts=(
            AnalystKey.GROWTH,
            AnalystKey.PROFITABILITY,
            AnalystKey.BALANCE_SHEET,
        ),
        excluded=(
            PlaybookExclusion(
                analyst=AnalystKey.CASH_FLOW,
                reason=(
                    "Cash on an asset manager's balance sheet moves with "
                    "client flows it does not own, so the statement does "
                    "not measure the business's own cash generation."
                ),
            ),
        ),
    ),
    PlaybookKind.REIT: InvestmentPlaybook(
        kind=PlaybookKind.REIT,
        name="Property Trust",
        explanation=(
            "Evaluated as a property trust, whose reported earnings are "
            "reduced by depreciation on buildings that are not wearing "
            "out. It is read on cash and on leverage instead."
        ),
        priorities=(
            "Cash generation",
            "Balance sheet leverage",
            "Rental growth",
        ),
        analysts=(
            AnalystKey.GROWTH,
            AnalystKey.BALANCE_SHEET,
            AnalystKey.CASH_FLOW,
        ),
        excluded=(
            PlaybookExclusion(
                analyst=AnalystKey.PROFITABILITY,
                reason=(
                    "Depreciation on property is a large non-cash charge, "
                    "so a trust's reported margins understate it. The "
                    "measure that corrects for this — funds from "
                    "operations — is not reported by this platform's "
                    "provider, so no substitute is offered for it."
                ),
            ),
        ),
    ),
    PlaybookKind.DIGITAL_ASSET: InvestmentPlaybook(
        kind=PlaybookKind.DIGITAL_ASSET,
        name="Digital Asset",
        explanation=(
            "Evaluated as a digital asset. It has no company behind it, "
            "no revenue and no earnings, so none of this platform's "
            "company analysts are asked about it — and its absence of a "
            "valuation score is that, not a gap in the data."
        ),
        priorities=(
            "Network scale and supply",
            "Observed volatility and drawdown",
            "Liquidity",
        ),
        analysts=(),
        excluded=tuple(
            PlaybookExclusion(
                analyst=analyst,
                reason=(
                    "A digital asset publishes no financial statements, "
                    "so there is nothing for this analyst to read."
                ),
            )
            for analyst in _FUNDAMENTALS
        ),
    ),
    PlaybookKind.FUND: InvestmentPlaybook(
        kind=PlaybookKind.FUND,
        name="Fund",
        explanation=(
            "Evaluated as a fund, which holds other securities rather "
            "than running a business of its own. Its accounts describe "
            "the wrapper, not the companies inside it."
        ),
        priorities=(
            "What it holds",
            "Observed volatility and drawdown",
            "Cost of ownership",
        ),
        analysts=(),
        excluded=tuple(
            PlaybookExclusion(
                analyst=analyst,
                reason=(
                    "A fund has no business of its own, so this analyst "
                    "would be reading the wrapper rather than a company."
                ),
            )
            for analyst in _FUNDAMENTALS
        ),
    ),
    PlaybookKind.UNCLASSIFIED: InvestmentPlaybook(
        kind=PlaybookKind.UNCLASSIFIED,
        name="Not classified",
        explanation=(
            "This platform's data provider reports no industry for this "
            "security, so no playbook was chosen for it on evidence. It "
            "is read on the ordinary accounts, and this says so rather "
            "than presenting the default as a decision."
        ),
        priorities=(
            "Earnings growth",
            "Profitability",
            "Balance sheet strength",
            "Cash generation",
        ),
        analysts=_FUNDAMENTALS,
    ),
}
