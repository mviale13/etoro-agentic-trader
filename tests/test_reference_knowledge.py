"""The committed reference fixture, and the claim that lets it be restamped.

`tests/reference_knowledge.py` serves JPM's committed observations at the
current protocol so two decision suites stop reaching into the
developer's own tree through a store's default path. Restamping is only
honest while the protocol that moved does not move *this* document's
readings — so that is asserted here rather than assumed there.
"""

from __future__ import annotations

from app.domain.knowledge_consensus import consensus_of
from app.domain.prose_evidence import namings
from tests.reference_knowledge import REFERENCE_SYMBOL, reference_observations


def test_the_reference_entry_restores_at_the_current_protocol() -> None:
    observations = reference_observations()

    assert len(observations) == 5
    assert all(item.symbol == REFERENCE_SYMBOL for item in observations)


def test_the_reference_entry_is_partition_stable() -> None:
    """DP1 may not have moved a single naming in this document.

    The schema-14 partition withdraws a naming only where the filer's
    own declared name runs into a segment's name. JPMorgan's identity
    words never do, so every description in the committed entry is owned
    by exactly the segment that owned it when it was read — which is the
    whole of the licence to restamp it rather than re-read it.

    Asserted over the observations' own text and the filer's own name,
    both taken from the entry itself.
    """

    observations = reference_observations()
    segments = tuple(segment.name for segment in consensus_of(observations).segments)
    filer = observations[0].source.company

    assert filer

    for observed in observations:
        prose = observed.description

        assert namings(prose, segments) == namings(prose, segments, filer)
