from dataclasses import dataclass

from app.domain.committee_evidence import CommitteeEvidence


@dataclass(frozen=True)
class CommitteeOpinion:
    """One legacy committee member's position — or its refusal to take one.

    **Abstention is a property of the opinion, not of the reader.** The
    chairman excluding a zero-confidence opinion from its arithmetic was
    only half a repair: every other consumer still read `vote` and saw a
    genuine HOLD. The doctor scored the account healthy on it, the
    reports and renderers printed HOLD, and the persisted event carried
    it into the analytics as a HOLD vote for ever.

    So the fact lives here, where anyone holding the opinion can ask.
    No consumer rediscovers it from `confidence == 0`, and none infers
    it from the word HOLD — HOLD is a real position, and a member that
    reached it is saying something.
    """

    member: str
    vote: str
    confidence: int
    rationale: str
    evidence: tuple[CommitteeEvidence, ...] = ()

    #: Why this member took no position, or None where it took one. A
    #: `vote` is still carried alongside — the legacy type requires the
    #: field — and it means nothing while this is set.
    abstained_because: str | None = None

    def __post_init__(self) -> None:
        if self.abstained_because is not None:
            if not self.abstained_because.strip():
                raise ValueError("an abstention carries its reason in words")

            if self.confidence != 0:
                raise ValueError(
                    "an abstention carries no confidence: it is the absence "
                    "of a position, not a weakly held one"
                )
        elif self.confidence <= 0:
            raise ValueError(
                "a participating opinion carries positive confidence; a "
                "zero-confidence position is an abstention and must say why"
            )

    @property
    def participates(self) -> bool:
        """Whether this opinion is a position the committee actually took."""

        return self.abstained_because is None
