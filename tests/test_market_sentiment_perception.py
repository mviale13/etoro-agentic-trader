"""Sentiment reaching the Brain, and staying about what it describes."""

import asyncio
from datetime import UTC, datetime

from app.application.brain.perception.market_perception import MarketPerception
from app.application.brain.reasoning.market_analyst import MarketAnalyst
from app.brain import BrainBuilder
from app.domain.asset_class import AssetClass
from app.domain.market_snapshot import MarketData, MarketQuote, MarketSnapshot
from app.domain.provenance import Provenance
from app.domain.sentiment_snapshot import SentimentSnapshot
from tests.test_brain_context import make_policy, make_portfolio

NOW = datetime(2026, 8, 3, 12, 0, tzinfo=UTC)


def reading() -> SentimentSnapshot:
    return SentimentSnapshot(
        score=28,
        label="Fear",
        subject=AssetClass.CRYPTO,
        reading=Provenance(source="Alternative.me", observed_at=NOW),
    )


class MarketStub:
    async def snapshot(self) -> MarketData:
        return MarketData(
            quotes=(
                MarketQuote(
                    symbol="SPY",
                    name="S&P 500 ETF",
                    price=600.0,
                    change_percent=1.2,
                    reading=Provenance(source="Yahoo Finance", observed_at=NOW),
                ),
            ),
            vix=16.0,
        )


class SentimentStub:
    def __init__(
        self,
        snapshot: SentimentSnapshot | None = None,
        failure: Exception | None = None,
    ) -> None:
        self._snapshot = snapshot
        self._failure = failure

    async def snapshot(self) -> SentimentSnapshot | None:
        if self._failure is not None:
            raise self._failure

        return self._snapshot


class ArchiveStub:
    """Records nothing. These tests are about the reading, not the record."""

    def record(self, snapshot: MarketSnapshot) -> object:
        return None


def perceive(sentiment: SentimentStub) -> MarketSnapshot:
    return asyncio.run(
        MarketPerception(
            provider=MarketStub(),
            sentiment_provider=sentiment,
            archive=ArchiveStub(),
        ).execute()
    )


def test_the_brain_can_finally_see_a_sentiment_reading() -> None:
    """
    It lived on the legacy committee path, where it set the outlook for
    the whole market, and the canonical pipeline could not see it at all.
    """

    market = perceive(SentimentStub(reading()))

    assert market.sentiment is not None
    assert market.sentiment.score == 28
    assert market.sentiment.subject is AssetClass.CRYPTO


def test_an_index_that_could_not_be_read_costs_the_reading_not_the_cycle() -> None:
    unread = perceive(SentimentStub(None))
    failed = perceive(SentimentStub(failure=OSError("the index is unreachable")))

    assert unread.sentiment is None
    assert failed.sentiment is None

    # The market itself still arrives.
    assert unread.quotes and failed.quotes


def test_sentiment_never_moves_the_market_scores() -> None:
    """
    The scores describe nine instruments; the reading describes one asset
    class. Folding one into the other lets a crypto mood move an equity
    reading.
    """

    without = MarketAnalyst().assess(brain(perceive(SentimentStub(None))))
    with_fear = MarketAnalyst().assess(brain(perceive(SentimentStub(reading()))))

    assert with_fear.momentum_score == without.momentum_score
    assert with_fear.volatility_score == without.volatility_score
    assert with_fear.trend == without.trend
    assert with_fear.regime == without.regime


def test_the_reading_reaches_reasoning_naming_what_it_describes() -> None:
    assessment = MarketAnalyst().assess(brain(perceive(SentimentStub(reading()))))

    stated = next(
        item for item in assessment.evidence if "sentiment" in item.description
    )

    assert stated.description == (
        "Crypto sentiment reads 28 (Fear), which describes crypto only."
    )

    # Cited to the service that published it, not to the snapshot.
    assert "Alternative.me" in stated.source


def brain(market: MarketSnapshot):
    return BrainBuilder(
        portfolio=make_portfolio(),
        market=market,
        investment_policy=make_policy(),
    ).build()


def test_the_reading_names_its_subject_as_data_not_only_in_prose() -> None:
    """
    A caption cannot be filtered on.

    "which describes crypto only" told the reader the fact did not apply;
    nothing downstream could act on that, so the fact went on being listed
    among those weighed about a software company.
    """

    assessment = MarketAnalyst().assess(brain(perceive(SentimentStub(reading()))))

    stated = next(
        item for item in assessment.evidence if "sentiment" in item.description
    )

    assert stated.subject is AssetClass.CRYPTO

    # The facts that describe the whole market carry no subject, and so
    # reach every case.
    assert all(
        item.subject is None
        for item in assessment.evidence
        if "sentiment" not in item.description
    )


def committee_evidence(asset_class: str | None) -> tuple[str, ...]:
    """The context facts that bear on a holding of this class.

    This used to read the Investment Committee's own evidence list,
    because that is where the defect appeared. The committee no longer
    carries context at all — it states a position over findings in its
    remit, and the portfolio and the market reach the investor as
    context, labelled as context — so the filter is exercised where it
    now lives. The claim under test is unchanged.
    """

    from dataclasses import replace

    from app.application.brain.reasoning import ReasoningService
    from app.application.brain.reasoning.models.assessment import evidence_about
    from app.domain.portfolio_position import PortfolioPosition
    from tests.test_security_evidence import make_company

    holding = PortfolioPosition(
        symbol="MSFT",
        quantity=1.0,
        invested_usd=100.0,
        market_value_usd=100.0,
        unrealized_pnl_usd=0.0,
        asset_class=asset_class,
        instrument_id=1,
    )

    market = perceive(SentimentStub(reading()))

    knowledge = BrainBuilder(
        portfolio=replace(make_portfolio(), holdings=(holding,)),
        market=market,
        investment_policy=make_policy(),
        evidence={"MSFT": (make_company("MSFT"),)},
    ).build()

    reasoning = ReasoningService().reason(knowledge)

    bearing = evidence_about(
        (*reasoning.portfolio.evidence, *reasoning.market.evidence),
        knowledge.asset_class_for("MSFT"),
    )

    return tuple(item.description for item in bearing)


def test_a_committee_carries_no_market_context_at_all() -> None:
    """
    The structural repair, above and beyond the filter.

    A committee that weighed the account and the market held an opinion
    that was partly about neither the security nor anything the investor
    asked about — identical under every symbol. It now states a position
    over findings in its own remit and carries nothing else, so the
    class of defect the filter catches cannot reach a committee at all.
    """

    from dataclasses import replace

    from app.application.committees.investment_committee import (
        InvestmentCommittee,
    )
    from app.application.executive.decision_evidence_builder import (
        DecisionEvidenceBuilder,
    )
    from app.domain.portfolio_position import PortfolioPosition
    from tests.test_security_evidence import make_company

    holding = PortfolioPosition(
        symbol="MSFT",
        quantity=1.0,
        invested_usd=100.0,
        market_value_usd=100.0,
        unrealized_pnl_usd=0.0,
        asset_class="stock",
        instrument_id=1,
    )

    knowledge = BrainBuilder(
        portfolio=replace(make_portfolio(), holdings=(holding,)),
        market=perceive(SentimentStub(reading())),
        investment_policy=make_policy(),
        evidence={"MSFT": (make_company("MSFT"),)},
    ).build()

    ledger = DecisionEvidenceBuilder().ledger("MSFT", knowledge)

    opinion = InvestmentCommittee().review(knowledge, "MSFT", ledger)

    # Everything it stands on resolves to a finding read about MSFT.
    for ref in (*opinion.supporting, *opinion.opposing):
        assert ledger.resolve(ref) is not None


def test_a_stock_is_never_judged_beside_the_crypto_fear_index() -> None:
    """
    The bug, stated: crypto sentiment among the facts weighed about MSFT.

    It was captioned honestly and it was still irrelevant — a fact that
    cannot bear on the decision in front of you is noise wherever it is
    printed, and noise on an investment case reads as something considered.
    """

    weighed = committee_evidence("stock")

    assert not any("sentiment" in line for line in weighed)

    # The conditions that do describe a stock are untouched.
    assert any("Average market move" in line for line in weighed)


def test_a_crypto_holding_is_judged_beside_it_because_it_describes_them() -> None:
    weighed = committee_evidence("crypto")

    assert any("Crypto sentiment reads 28 (Fear)" in line for line in weighed)


def test_an_unclassified_holding_is_not_assumed_to_be_the_class_that_fits() -> None:
    """Guessing the class is the substitution the subject exists to stop."""

    weighed = committee_evidence(None)

    assert not any("sentiment" in line for line in weighed)
