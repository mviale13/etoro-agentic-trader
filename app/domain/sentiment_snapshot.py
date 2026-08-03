"""A published reading of how one market feels, and which market that is."""

from dataclasses import dataclass

from app.domain.asset_class import AssetClass
from app.domain.provenance import Provenance


@dataclass(frozen=True, slots=True)
class SentimentSnapshot:
    """
    One sentiment reading, and what it is a reading of.

    `subject` is not decoration. The only index this platform reads is
    Alternative.me's crypto Fear & Greed, and it was being combined with
    the mood of nine instruments into a single outlook — so crypto fear
    "confirmed" an equity sell-off it knows nothing about, and raised the
    confidence of the whole reading while doing it.

    A sentiment reading applies to the asset class it was taken of.
    Naming that here is what lets a reader see when it is being asked to
    describe something else.
    """

    score: int
    label: str

    #: The asset class this reading describes.
    subject: AssetClass

    #: Who published it, and when they published it.
    reading: Provenance

    @property
    def describes_crypto(self) -> bool:
        return self.subject is AssetClass.CRYPTO

    @property
    def stated(self) -> str:
        """The reading as the investor should read it, subject named."""

        # The class as it is named, not as it is used in a sentence:
        # "Crypto sentiment", not "Cryptocurrency sentiment".
        return (
            f"{self.subject.value.capitalize()} sentiment reads "
            f"{self.score} ({self.label})"
        )
