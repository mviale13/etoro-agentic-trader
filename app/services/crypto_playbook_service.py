"""Join a token's archetype to its questions and to what is held.

A read-only door in the family `CompanyKnowledgeService.established` and
`ProtocolFundamentalsService.established` belong to: it asks the two
crypto evidence services what they already hold and stops. It fetches
nothing, asks no model, writes nothing, and — the rule this phase
established — a page view may sit behind it.

**Applicability is resolved before any evidence is read.** Not a
sequencing detail: `applicability_for` takes the archetype and nothing
else, so no absence of data can turn a legitimate question into an
inapplicable one. The evidence pass then fills in what is held against
questions whose applicability was already settled. A test runs this
service against empty stores and asserts the applicability column is
identical.

Nothing here scores, bands or concludes.
"""

from __future__ import annotations

from app.domain.asset_class import AssetClass
from app.domain.crypto_archetype import archetype_for
from app.domain.crypto_playbook import (
    CryptoPlaybook,
    DemandCoverage,
    QuestionCoverage,
    ValueUnit,
)
from app.domain.crypto_questions import (
    QUESTIONS,
    CryptoQuestion,
    CryptoQuestionKey,
    EvidenceDemand,
    applicability_for,
)
from app.domain.evidence_standing import EvidenceStanding
from app.domain.protocol_fundamentals import ProtocolFundamentals
from app.domain.token_facts import TokenMarketFacts
from app.domain.token_value_flow import value_chains
from app.services.protocol_fundamentals_service import ProtocolFundamentalsService
from app.services.token_facts_service import TokenFactsService

#: How each token fact is worded. The asset profile's own grouping,
#: expressed as units rather than as sections.
_MONEY_FACTS = (
    "market_cap",
    "spot_volume_24h",
    "market_volume_24h",
    "fully_diluted_valuation",
    "price",
)
_COUNT_FACTS = ("circulating_supply", "total_supply", "max_supply")


class CryptoPlaybookService:
    """Which questions this token is asked, and what could answer them."""

    def __init__(
        self,
        facts: TokenFactsService | None = None,
        protocol: ProtocolFundamentalsService | None = None,
    ) -> None:
        self._facts = facts or TokenFactsService()
        self._protocol = protocol or ProtocolFundamentalsService()

    def established(
        self,
        symbol: str,
        asset_class: AssetClass | None,
    ) -> CryptoPlaybook | None:
        """The playbook for a token, or None for anything that is not one.

        Only a security positively classified as crypto is answered, the
        same rule both evidence services live by. An unclassified
        security is never promoted into this family by a heuristic.
        """

        if asset_class is not AssetClass.CRYPTO:
            return None

        normalized = symbol.upper().strip()

        assignment = archetype_for(normalized)

        # Applicability first, from the archetype alone. Nothing read
        # below is permitted to change any of it.
        applicability = {
            key: applicability_for(assignment.archetype, key)
            for key in CryptoQuestionKey
        }

        facts = self._facts.established(normalized, normalized, asset_class)
        protocol = self._protocol.established(normalized, asset_class)

        # Evidence is gathered only for a question that applies. A
        # refused question with figures beneath it would let a later
        # reader take "Bitcoin's economic activity: $139.0k/day" off a
        # question this platform holds to be the wrong one — and the
        # refusal exists precisely so that figure is never read that
        # way. The same for an undetermined one: attaching evidence to
        # it would assert an applicability nothing established.
        coverage = tuple(
            QuestionCoverage(
                question=QUESTIONS[key],
                applicability=applicability[key],
                covered=(
                    self._cover(QUESTIONS[key], facts, protocol)
                    if applicability[key].is_asked
                    else ()
                ),
            )
            for key in CryptoQuestionKey
        )

        return CryptoPlaybook(
            symbol=normalized,
            assignment=assignment,
            coverage=coverage,
            chains=value_chains(protocol) if protocol is not None else (),
            unmapped_because=(
                protocol.unmapped_because if protocol is not None else None
            ),
        )

    # ── the evidence pass ───────────────────────────────────────────

    def _cover(
        self,
        question: CryptoQuestion,
        facts: TokenMarketFacts | None,
        protocol: ProtocolFundamentals | None,
    ) -> tuple[DemandCoverage, ...]:
        """What is held against each of one question's demands.

        Every demand appears, met or not. A demand dropped for being
        unmet would turn an acquisition roadmap into a list of things
        that happened to work.
        """

        return tuple(
            self._cover_one(demand, facts, protocol) for demand in question.demands
        )

    def _cover_one(
        self,
        demand: EvidenceDemand,
        facts: TokenMarketFacts | None,
        protocol: ProtocolFundamentals | None,
    ) -> DemandCoverage:
        if demand.token_fact is not None:
            return self._from_token_facts(demand, facts)

        if demand.protocol_metric is not None:
            return self._from_protocol(demand, protocol)

        return DemandCoverage(
            demand=demand,
            standing=EvidenceStanding.ABSENT,
            because=(
                "No source this platform reads publishes this. It is "
                "named so the gap is a demand rather than a silence."
            ),
        )

    @staticmethod
    def _from_token_facts(
        demand: EvidenceDemand,
        facts: TokenMarketFacts | None,
    ) -> DemandCoverage:
        name = demand.token_fact

        assert name is not None

        fact = facts.fact(name) if facts is not None else None

        if fact is None:
            return DemandCoverage(
                demand=demand,
                standing=EvidenceStanding.ABSENT,
                because=(
                    "Nothing has been read for this token. Reading it is "
                    "an explicit spend, and no surface takes it — "
                    "`movrvest acquire` does."
                ),
            )

        return DemandCoverage(
            demand=demand,
            standing=fact.standing,
            value=fact.value,
            unit=_unit_for(name),
            source=fact.source,
            observed_at=fact.observed_at,
            because=fact.because,
        )

    @staticmethod
    def _from_protocol(
        demand: EvidenceDemand,
        protocol: ProtocolFundamentals | None,
    ) -> DemandCoverage:
        metric = demand.protocol_metric

        assert metric is not None

        if protocol is None or not protocol.entities:
            return DemandCoverage(
                demand=demand,
                standing=EvidenceStanding.ABSENT,
                because=(
                    "No economic system is mapped to this security, so "
                    "there is nothing to measure. A shared name does not "
                    "establish one."
                ),
            )

        # The demand names the kind of entity it expects, because the
        # same metric measures different things on a chain and on a
        # venue. Where it names none, the first mapped entity that holds
        # a reading answers — and the entity's name travels with it, so
        # a reader always knows which of two systems was quoted.
        candidates = [
            entity
            for entity in protocol.entities
            if demand.entity_kind is None or entity.kind is demand.entity_kind
        ]

        if not candidates:
            return DemandCoverage(
                demand=demand,
                standing=EvidenceStanding.ABSENT,
                because=(
                    "This measure belongs to a "
                    f"{demand.entity_kind.stated if demand.entity_kind else 'system'}"
                    ", and none is mapped to this security."
                ),
            )

        best: DemandCoverage | None = None

        for entity in candidates:
            fact = protocol.fact(metric, entity.key)

            if fact is None:
                continue

            # A demand for the source's *definition* is met by the
            # sentence and by nothing else. A figure with no definition
            # beside it leaves this demand unmet even though the metric
            # was read — which is precisely the state 1inch is in, and
            # collapsing the two would let an amount stand in for the
            # mechanism nobody described.
            if demand.wants_methodology:
                if not fact.provider_methodology:
                    best = best or DemandCoverage(
                        demand=demand,
                        standing=EvidenceStanding.ABSENT,
                        entity=entity.name,
                        because=(
                            f"{fact.source or 'The source'} publishes no "
                            f"definition of this for {entity.name}, so "
                            "what any figure means is not established."
                        ),
                    )
                    continue

                return DemandCoverage(
                    demand=demand,
                    standing=fact.standing,
                    methodology=fact.provider_methodology,
                    source=fact.source,
                    observed_at=fact.observed_at,
                    entity=entity.name,
                    because=fact.because,
                )

            covered = DemandCoverage(
                demand=demand,
                standing=fact.standing,
                value=fact.value,
                unit=ValueUnit.MONEY,
                source=fact.source,
                observed_at=fact.observed_at,
                entity=entity.name,
                because=fact.because,
            )

            if fact.standing.serves_value:
                return covered

            best = best or covered

        return best or DemandCoverage(
            demand=demand,
            standing=EvidenceStanding.ABSENT,
            because="Nothing has been read for the systems mapped here.",
        )


def _unit_for(name: str) -> ValueUnit:
    if name in _MONEY_FACTS:
        return ValueUnit.MONEY

    if name in _COUNT_FACTS:
        return ValueUnit.COUNT

    if name == "rank":
        return ValueUnit.RANK

    return ValueUnit.NONE
