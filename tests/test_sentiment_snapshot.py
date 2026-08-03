"""A sentiment reading, and what it is a reading of."""

from datetime import UTC, datetime

from app.domain.asset_class import AssetClass
from app.domain.provenance import Provenance
from app.domain.sentiment_snapshot import SentimentSnapshot

PUBLISHED = datetime(2026, 8, 3, tzinfo=UTC)


def snapshot(subject: AssetClass = AssetClass.CRYPTO) -> SentimentSnapshot:
    return SentimentSnapshot(
        score=72,
        label="Greed",
        subject=subject,
        reading=Provenance(source="Alternative.me", observed_at=PUBLISHED),
    )


def test_a_reading_carries_its_figure_and_its_citation() -> None:
    sentiment = snapshot()

    assert sentiment.score == 72
    assert sentiment.label == "Greed"
    assert sentiment.reading.source == "Alternative.me"
    assert sentiment.reading.observed_at == PUBLISHED


def test_a_reading_names_the_asset_class_it_describes() -> None:
    """
    The only index read here is a crypto one, and it was being combined
    with the mood of nine instruments into a single outlook. A reading
    that cannot say what it is of cannot be caught describing something
    else.
    """

    assert snapshot().describes_crypto
    assert not snapshot(AssetClass.STOCK).describes_crypto


def test_the_reading_states_itself_with_its_subject() -> None:
    """Never "market sentiment": the subject is half the claim."""

    assert snapshot().stated == "Crypto sentiment reads 72 (Greed)"
