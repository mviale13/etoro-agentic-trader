"""The ledger must agree with the adapter, field for field.

This boundary is only worth having if it describes what the platform
actually does. The audit found `market_snapshot_archive` duplicating
the quote restore with its own copy of the same hardcoded defaults —
one translation, two owners, and a fix to either would miss the other.

So the ledger performs no conversion and these tests prove it: over
the live stored corpus, every promoted value equals the value the
adapter produced, and the claim's raw value is the payload's own.
A ledger that started converting would diverge here rather than in
production.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from app.domain.provider_claim import ClaimAbsence
from app.domain.provider_translation import TranslationWarrant
from app.providers.value_provider import ValueProvider
from app.services.provider_ledger_service import _FUNDAMENTALS, ProviderLedgerService

NOW = datetime(2026, 8, 15, 12, 0, tzinfo=UTC)

#: Payloads shaped like the live corpus, held here rather than read
#: from `data/`. The audit's 77-record corpus is gitignored, so a test
#: reading it would pass vacuously in CI by skipping — the failure mode
#: #118 named — and would also read the developer's own machine, which
#: the same ruling forbids. The corpus round trip is run as an explicit
#: measurement instead, and its result is recorded in the slice
#: document; these fixtures carry the shapes that measurement found.
CORPUS_SHAPES: tuple[tuple[str, dict[str, Any]], ...] = (
    (
        "BNP.PA",
        {
            "forwardPE": 8.5368805,
            "trailingPE": 9.697231,
            "marketCap": 122861600768,
            "dividendYield": 8.85,
            "trailingEps": 11.56,
            "sector": "Financial Services",
        },
    ),
    (
        "NOVO-B.CO",
        {
            "forwardPE": 14.05,
            "dividendYield": 0.0521,
            "trailingEps": 26.21,
            "revenueGrowth": 0.181,
            "grossMargins": 0.8425,
            "debtToEquity": 195.6,
        },
    ),
    (
        "IB01.L",
        {"netExpenseRatio": 0.07, "dividendYield": 0.0},
    ),
    (
        "H2O.DE",
        {"forwardPE": -7.37, "trailingEps": -1.08, "marketCap": 31100000},
    ),
    (
        "ARB-USD",
        {"marketCap": 0, "circulatingSupply": 4960000000},
    ),
    ("UDMY", {}),
)


class TestLedgerAgreesWithTheAdapter:
    def test_every_promoted_value_equals_the_snapshot_field(self) -> None:
        """The property that keeps one translation from becoming two."""

        service = ProviderLedgerService()

        for symbol, payload in CORPUS_SHAPES:
            snapshot = ValueProvider.from_info(payload)

            ledger = service.fundamentals(symbol, payload, snapshot, NOW)

            for _, attribute, concept in _FUNDAMENTALS:
                fact = ledger.fact(concept)

                assert fact is not None, f"{symbol}: {concept} ungoverned"
                assert fact.value == getattr(snapshot, attribute), (
                    f"{symbol}: {concept} diverged from the adapter — "
                    f"the ledger is converting something"
                )

    def test_every_governed_fundamental_is_promoted(self) -> None:
        """A field silently dropped from the ledger would prove nothing."""

        service = ProviderLedgerService()

        snapshot = ValueProvider.from_info({})

        ledger = service.fundamentals("X", {}, snapshot, NOW)

        concepts = {fact.concept for fact in ledger.facts}

        for _, _, concept in _FUNDAMENTALS:
            assert concept in concepts


class TestClaimsRecordWhatArrived:
    def test_a_claim_carries_the_raw_payload_value(self) -> None:
        service = ProviderLedgerService()

        payload = {"forwardPE": 8.5368805}

        snapshot = ValueProvider.from_info(payload)

        ledger = service.fundamentals("BNP.PA", payload, snapshot, NOW)

        fact = ledger.fact("ValuationSnapshot.forward_pe")

        assert fact is not None
        assert fact.claims[0].raw_value == 8.5368805

    def test_a_missing_key_and_a_null_are_different_absences(self) -> None:
        service = ProviderLedgerService()

        missing = service.fundamentals("X", {}, ValueProvider.from_info({}), NOW).fact(
            "ValuationSnapshot.forward_pe"
        )

        nulled = service.fundamentals(
            "X", {"forwardPE": None}, ValueProvider.from_info({"forwardPE": None}), NOW
        ).fact("ValuationSnapshot.forward_pe")

        assert missing is not None and nulled is not None
        assert missing.claims[0].absence is ClaimAbsence.FIELD_ABSENT
        assert nulled.claims[0].absence is ClaimAbsence.REPORTED_NULL


class TestDividendYieldConflict:
    """The mandatory case: two schemas, one field name."""

    def test_unmerged_payloads_produce_two_claims_and_no_established_fact(
        self,
    ) -> None:
        service = ProviderLedgerService()

        merged = {"dividendYield": 5.17}

        ledger = service.fundamentals(
            "BNP.PA",
            merged,
            ValueProvider.from_info(merged),
            NOW,
            quote_summary={"dividendYield": 0.0517},
            v7_quote={"dividendYield": 5.17},
        )

        fact = ledger.fact("ValuationSnapshot.dividend_yield")

        assert fact is not None
        assert len(fact.claims) == 2
        assert fact.unresolved
        assert not fact.establishes_domain_fact
        assert fact.value == 5.17
        assert "0.0517" in fact.stated and "5.17" in fact.stated

    def test_the_merged_payload_alone_is_still_never_established(self) -> None:
        """A record written before this boundary keeps its honest standing."""

        service = ProviderLedgerService()

        payload = {"dividendYield": 8.85}

        ledger = service.fundamentals(
            "BNP.PA", payload, ValueProvider.from_info(payload), NOW
        )

        fact = ledger.fact("ValuationSnapshot.dividend_yield")

        assert fact is not None
        assert fact.warrant is TranslationWarrant.UNKNOWN
        assert not fact.establishes_domain_fact


class TestEpsSubstitution:
    """A forecast standing in for a realised figure must say so."""

    def test_a_trailing_eps_is_governed_as_the_realised_figure(self) -> None:
        service = ProviderLedgerService()

        payload = {"trailingEps": 11.56}

        ledger = service.fundamentals(
            "BNP.PA", payload, ValueProvider.from_info(payload), NOW
        )

        assert ledger.fact("ValuationSnapshot.eps") is not None
        assert ledger.fact("ValuationSnapshot.eps (substituted)") is None

    def test_a_forward_eps_substitution_is_visible_and_unwarranted(self) -> None:
        """The turnaround case: the two figures differ in sign.

        The compatibility value is unchanged — a loss-making company
        still earns the platform's positive-earnings point today —
        but the number now carries that a forecast supplied it.
        """

        service = ProviderLedgerService()

        payload = {"forwardEps": 1.20}

        snapshot = ValueProvider.from_info(payload)

        ledger = service.fundamentals("TURN", payload, snapshot, NOW)

        fact = ledger.fact("ValuationSnapshot.eps (substituted)")

        assert fact is not None
        assert fact.value == snapshot.eps == 1.20
        assert fact.warrant is TranslationWarrant.UNKNOWN
        assert not fact.establishes_domain_fact

        absences = [claim for claim in fact.claims if not claim.reported]

        assert absences and absences[0].field == "trailingEps"

    def test_the_substitution_survives_a_sign_disagreement(self) -> None:
        """Trailing negative, forward positive — and only forward present."""

        service = ProviderLedgerService()

        payload = {"forwardEps": 2.5}

        snapshot = ValueProvider.from_info(payload)

        assert snapshot.eps == 2.5

        ledger = service.fundamentals("TURN", payload, snapshot, NOW)

        fact = ledger.fact("ValuationSnapshot.eps (substituted)")

        assert fact is not None
        assert not fact.establishes_domain_fact
