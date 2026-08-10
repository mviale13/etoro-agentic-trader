"""What the economic system behind a token earns, judged on read.

The consumption seam for the second evidence family, built on the same
architecture S1 established for the first: adapters produce claim sets,
the service pools them, and standings are derived on read — so a rule
improved later re-judges stored claims without a reacquisition, and a
second protocol-data source is an adapter plus a list entry.

The same establishment rule applies, uniformly: **agreement inside one
provider is not corroboration**. With one protocol source today, its
figures are its claims — attributed, dated, carrying its own
methodology, and consumed by nothing. Naming them established because
they are the only ones available would be the substitution the whole
gate exists to prevent, and it would mean two different things by
"established" on one page.

What the pool *does* check today is the provider's internal coherence
across metrics, which the corpus makes possible: fees ≥ protocol
revenue and fees ≥ holder revenue are relations of what the words mean,
and a set that breaks them has its offending figures rejected with the
reason retained.

Nothing here scores. No factor consumes any of it.
"""

from __future__ import annotations

from typing import Protocol

from app.domain.asset_class import AssetClass
from app.domain.evidence_standing import EvidenceStanding
from app.domain.protocol_entities import entities_for
from app.domain.protocol_fundamentals import (
    DerivedProtocolFigure,
    MetricAvailability,
    ProtocolEntity,
    ProtocolEntityKind,
    ProtocolFact,
    ProtocolFundamentals,
    ProtocolMetric,
    annualise,
)
from app.providers.defillama_provider import (
    CachedDefiLlamaProvider,
    ProtocolClaimSet,
    ProtocolMetricClaim,
)

#: Which metrics each kind of entity is even asked about.
#:
#: Applicability, not availability: a chain has no order book, so its
#: DEX volume is not a gap in this platform's reading — it is a
#: question that does not apply. Bitcoin must never read as incomplete
#: for lacking an exchange's figures.
_APPLICABLE: dict[ProtocolEntityKind, tuple[ProtocolMetric, ...]] = {
    ProtocolEntityKind.CHAIN: (
        ProtocolMetric.TVL,
        ProtocolMetric.FEES,
        ProtocolMetric.PROTOCOL_REVENUE,
        ProtocolMetric.HOLDER_REVENUE,
    ),
    ProtocolEntityKind.PROTOCOL: (
        ProtocolMetric.TVL,
        ProtocolMetric.FEES,
        ProtocolMetric.PROTOCOL_REVENUE,
        ProtocolMetric.HOLDER_REVENUE,
        ProtocolMetric.DEX_VOLUME,
        ProtocolMetric.OPEN_INTEREST,
    ),
}

#: Metrics that are applicable to an entity but which no free source
#: publishes for it — stated per entity, because "nobody publishes it"
#: and "this entity does not have one" are different sentences.
_UNAVAILABLE_FREE: dict[str, dict[ProtocolMetric, str]] = {
    "hyperliquid-protocol": {},
}

#: Metrics an entity is not asked about, with the reason it is not.
#:
#: Applicability declared from what the entity *is*, never inferred
#: from an absence of data. An aggregator routes trades to other
#: venues: it runs no book, holds nothing of its own, and takes no
#: derivative positions, so three of the six questions are not thin
#: evidence about it — they are not questions about it at all.
_DECLINED: dict[str, dict[ProtocolMetric, str]] = {
    "1inch-protocol": {
        ProtocolMetric.TVL: (
            "an aggregator routes trades to other venues and holds "
            "little of its own, so capital held would measure "
            "something other than the business."
        ),
        ProtocolMetric.DEX_VOLUME: (
            "an aggregator has no book of its own: what it routes to "
            "other venues is a different measurement from a venue's "
            "own volume, and this platform does not conflate them."
        ),
        ProtocolMetric.OPEN_INTEREST: (
            "it runs no derivatives venue, so the question does not arise."
        ),
    },
}


#: The metrics whose definitions travel together in one provider
#: record. A missing key is evidence about applicability only against
#: its own siblings: fees, protocol revenue and holder revenue are
#: published in a single methodology, so one absent among the others
#: says something. Capital and activity are published separately and
#: say nothing about each other.
_FAMILY_SIBLINGS: dict[ProtocolMetric, tuple[ProtocolMetric, ...]] = {
    ProtocolMetric.FEES: (
        ProtocolMetric.PROTOCOL_REVENUE,
        ProtocolMetric.HOLDER_REVENUE,
    ),
    ProtocolMetric.PROTOCOL_REVENUE: (
        ProtocolMetric.FEES,
        ProtocolMetric.HOLDER_REVENUE,
    ),
    ProtocolMetric.HOLDER_REVENUE: (
        ProtocolMetric.FEES,
        ProtocolMetric.PROTOCOL_REVENUE,
    ),
}


class ProtocolClaimSource(Protocol):
    """One claimant: asked for an entity, answers with a set or nothing."""

    def claim_set(self, entity_key: str) -> ProtocolClaimSet | None: ...


class StoredProtocolClaimsReader(Protocol):
    """A cached protocol provider's read-only door."""

    def claims(self, entity_key: str) -> ProtocolClaimSet | None: ...


class DefiLlamaClaimSource:
    """DefiLlama's stored claims, as a pool claimant."""

    def __init__(self, reader: StoredProtocolClaimsReader | None = None) -> None:
        self._reader: StoredProtocolClaimsReader = (
            reader or CachedDefiLlamaProvider.stored()
        )

    def claim_set(self, entity_key: str) -> ProtocolClaimSet | None:
        try:
            return self._reader.claims(entity_key)
        except Exception:
            return None


class ProtocolFundamentalsService:
    """Everything held about the economics behind one security."""

    def __init__(
        self,
        sources: tuple[ProtocolClaimSource, ...] | None = None,
    ) -> None:
        self._sources: tuple[ProtocolClaimSource, ...] = sources or (
            DefiLlamaClaimSource(),
        )

    def established(
        self,
        symbol: str,
        asset_class: AssetClass | None,
    ) -> ProtocolFundamentals | None:
        """The judged protocol facts, or None where the family does not apply.

        Only a security positively classified as crypto is answered. An
        unclassified security is never promoted into this family by a
        heuristic, exactly as it is never promoted into the token-facts
        one.
        """

        if asset_class is not AssetClass.CRYPTO:
            return None

        normalized = symbol.upper().strip()

        entities = entities_for(normalized)

        if not entities:
            return ProtocolFundamentals(
                symbol=normalized,
                entities=(),
                facts=(),
                unmapped_because=(
                    f"No economic system has been mapped to {normalized}. "
                    "A shared name does not establish one, so nothing is "
                    "measured rather than something adjacent being "
                    "measured and labelled as its own."
                ),
            )

        facts: list[ProtocolFact] = []
        derived: list[DerivedProtocolFigure] = []

        for entity in entities:
            pool = tuple(
                claims
                for source in self._sources
                if (claims := source.claim_set(entity.key)) is not None
            )

            entity_facts = self._judge(entity, pool)

            facts.extend(entity_facts)

            for fact in entity_facts:
                figure = annualise(fact)

                if figure is not None:
                    derived.append(figure)

        return ProtocolFundamentals(
            symbol=normalized,
            entities=entities,
            facts=tuple(facts),
            derived=tuple(derived),
        )

    # ── judging one entity's pool ───────────────────────────────────

    def _judge(
        self,
        entity: ProtocolEntity,
        pool: tuple[ProtocolClaimSet, ...],
    ) -> list[ProtocolFact]:
        applicable = _APPLICABLE[entity.kind]

        declined = _DECLINED.get(entity.key, {})

        incoherent = self._incoherent_metrics(pool)

        facts: list[ProtocolFact] = []

        for metric in ProtocolMetric:
            if metric not in applicable or metric in declined:
                facts.append(self._not_applicable(entity, metric, declined))
                continue

            offered = [
                (claims, claim)
                for claims in pool
                if (claim := claims.claim(metric)) is not None
            ]

            if not offered:
                # Two absences that look identical. A source that
                # publishes no *definition* of this metric for this
                # entity is telling us the question does not arise
                # here — Bitcoin has no holder-revenue mechanism, and
                # that is a property of Bitcoin, not a gap in today's
                # reading.
                # Only where the source documents *sibling* metrics —
                # and only within the same family. A source that
                # publishes a fee methodology naming fees and revenue
                # and omitting holder revenue is telling us Bitcoin has
                # no such mechanism. A source that publishes only a TVL
                # figure is telling us nothing about fees at all, and
                # reading its silence as inapplicability would invent a
                # finding out of a gap.
                siblings = _FAMILY_SIBLINGS.get(metric, ())

                undefined = bool(siblings) and (
                    any(
                        sibling in claims.defines
                        for claims in pool
                        for sibling in siblings
                    )
                    and not any(metric in claims.defines for claims in pool)
                )

                if undefined:
                    facts.append(
                        ProtocolFact(
                            metric=metric,
                            entity=entity,
                            availability=MetricAvailability.NOT_APPLICABLE,
                            standing=EvidenceStanding.ABSENT,
                            because=(
                                f"The source defines other measures for "
                                f"{entity.name} and none for this one: "
                                "it is not a mechanism this entity has, "
                                "rather than a figure missing today."
                            ),
                        )
                    )
                    continue

                defined = any(metric in claims.defines for claims in pool)

                facts.append(self._unavailable(entity, metric, bool(pool), defined))
                continue

            if metric in incoherent:
                facts.append(
                    ProtocolFact(
                        metric=metric,
                        entity=entity,
                        availability=MetricAvailability.SEMANTICS_UNRESOLVED,
                        standing=EvidenceStanding.REJECTED,
                        because=(
                            "the source reports a figure that breaks what "
                            "the words mean — a share of fees larger than "
                            "the fees themselves — so it is not served."
                        ),
                    )
                )
                continue

            facts.append(self._claimed(entity, metric, offered))

        return facts

    @staticmethod
    def _incoherent_metrics(
        pool: tuple[ProtocolClaimSet, ...],
    ) -> set[ProtocolMetric]:
        """Figures a source's own metrics contradict.

        Protocol revenue and holder revenue are shares of fees. A share
        larger than the whole is not a methodology this platform has
        failed to understand; it is a figure that cannot be true.
        """

        broken: set[ProtocolMetric] = set()

        for claims in pool:
            fees = claims.claim(ProtocolMetric.FEES)

            if fees is None:
                continue

            for share in (
                ProtocolMetric.PROTOCOL_REVENUE,
                ProtocolMetric.HOLDER_REVENUE,
            ):
                part = claims.claim(share)

                # A percent of slack for rounding between two figures
                # the provider computes separately.
                if part is not None and part.value > fees.value * 1.01:
                    broken.add(share)

        return broken

    def _claimed(
        self,
        entity: ProtocolEntity,
        metric: ProtocolMetric,
        offered: list[tuple[ProtocolClaimSet, ProtocolMetricClaim]],
    ) -> ProtocolFact:
        """One source's figure, served as its claim.

        Establishment waits for a second protocol source. Where two
        eventually agree, this is the seam that will say so — the rule
        is the token layer's, unchanged.
        """

        claims, claim = offered[0]

        sources = sorted({item[0].source for item in offered})

        because = (
            f"{claims.source} reports it"
            + ("" if len(sources) == 1 else f", and so do {', '.join(sources[1:])}")
            + ". No independent source corroborates it — agreement "
            "inside one provider is not corroboration."
        )

        if not entity.mapping_settled:
            because += (
                " The entity is mapped, and what its economics mean for "
                "this token is not settled."
            )

        return ProtocolFact(
            metric=metric,
            entity=entity,
            availability=MetricAvailability.AVAILABLE,
            standing=EvidenceStanding.CLAIMED,
            value=claim.value,
            window=claim.window,
            source=claims.source,
            observed_at=claims.read.observed_at,
            provider_methodology=claim.methodology,
            because=because,
        )

    @staticmethod
    def _not_applicable(
        entity: ProtocolEntity,
        metric: ProtocolMetric,
        declined: dict[ProtocolMetric, str],
    ) -> ProtocolFact:
        if metric in declined:
            reason = f"{entity.name} is not asked this: {declined[metric]}"
        else:
            reason = (
                f"{entity.name} is a {entity.kind.stated}, and this "
                "measures something a "
                f"{entity.kind.stated} does not have."
            )

        return ProtocolFact(
            metric=metric,
            entity=entity,
            availability=MetricAvailability.NOT_APPLICABLE,
            standing=EvidenceStanding.ABSENT,
            because=reason,
        )

    @staticmethod
    def _unavailable(
        entity: ProtocolEntity,
        metric: ProtocolMetric,
        read_anything: bool,
        defined: bool = False,
    ) -> ProtocolFact:
        if not read_anything:
            return ProtocolFact(
                metric=metric,
                entity=entity,
                availability=MetricAvailability.UNAVAILABLE_FREE,
                standing=EvidenceStanding.ABSENT,
                because=(
                    f"Nothing has been read for {entity.name}. Reading it "
                    "is an explicit spend, and no surface takes it — "
                    "`movrvest acquire` does."
                ),
            )

        if defined:
            return ProtocolFact(
                metric=metric,
                entity=entity,
                availability=MetricAvailability.UNAVAILABLE_FREE,
                standing=EvidenceStanding.ABSENT,
                because=(
                    f"The source defines this for {entity.name} and "
                    "reported no figure for the window. Whether that is "
                    "a mechanism producing nothing or a reading that "
                    "did not arrive, the source does not say."
                ),
            )

        return ProtocolFact(
            metric=metric,
            entity=entity,
            availability=MetricAvailability.UNAVAILABLE_FREE,
            standing=EvidenceStanding.ABSENT,
            because=(
                f"The question applies to {entity.name}, and no source "
                "this platform reads publishes it without payment."
            ),
        )
