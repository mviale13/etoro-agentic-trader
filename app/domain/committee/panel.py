"""The committees' positions on one security, read together.

The object the Executive layer adjudicates over. It is a *reading* of
opinions, never a participant: it holds no position of its own, and no
committee can see it. That separation is what keeps a dissent
recoverable — a panel that resolved disagreement before the Executive
layer ran would leave nothing to record but the winner.

Agreement here means *the committees that spoke point the same way*.
It deliberately does not mean *the committees are confident*, which is
what the old figure measured while being labelled agreement: an
average of two confidence floats rose and fell with how much had been
read and never once counted whether the two committees concurred.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.domain.committee.opinion import CommitteeOpinion, Stance


@dataclass(frozen=True, slots=True)
class Panel:
    """Every committee's opinion on one security."""

    opinions: tuple[CommitteeOpinion, ...] = ()

    @property
    def spoke(self) -> tuple[CommitteeOpinion, ...]:
        """The committees that took a position.

        An abstention is never counted among these. The platform has
        twice shipped a defect where silence was averaged in as though
        it were a view, and both times the effect was the same: a
        committee that could not measure its own subject looked like a
        committee voting against.
        """

        return tuple(opinion for opinion in self.opinions if opinion.has_opinion)

    @property
    def abstained(self) -> tuple[CommitteeOpinion, ...]:
        return tuple(opinion for opinion in self.opinions if not opinion.has_opinion)

    @property
    def positive(self) -> tuple[CommitteeOpinion, ...]:
        return tuple(
            opinion
            for opinion in self.spoke
            if opinion.stance is not None and opinion.stance.is_positive
        )

    @property
    def negative(self) -> tuple[CommitteeOpinion, ...]:
        return tuple(
            opinion
            for opinion in self.spoke
            if opinion.stance is not None and opinion.stance.is_negative
        )

    @property
    def neutral(self) -> tuple[CommitteeOpinion, ...]:
        return tuple(
            opinion for opinion in self.spoke if opinion.stance is Stance.NEUTRAL
        )

    @property
    def is_unanimous(self) -> bool:
        """Whether every committee that spoke pointed the same way."""

        spoke = self.spoke

        return bool(spoke) and len({self._direction(o) for o in spoke}) == 1

    @property
    def is_divided(self) -> bool:
        """Whether one committee is positive while another is negative.

        Stricter than *not unanimous*: a positive committee beside a
        neutral one is a difference of degree, and calling it a
        division would tell an investor there was an argument where
        there was only an absence of one.
        """

        return bool(self.positive) and bool(self.negative)

    @property
    def agreement_pct(self) -> int | None:
        """The share of speaking committees holding the majority direction.

        None where none spoke. Zero would say they disagreed
        completely, which is the opposite of what an empty panel means.
        """

        spoke = self.spoke

        if not spoke:
            return None

        directions = [self._direction(opinion) for opinion in spoke]

        largest = max(directions.count(value) for value in set(directions))

        return round(largest / len(spoke) * 100)

    def stated(self) -> str:
        """How far the committees agreed, in words, with the counts."""

        spoke = self.spoke

        if not spoke:
            return (
                f"No committee took a position; {len(self.abstained)} "
                "abstained. Nothing here is disagreement."
            )

        if self.is_divided:
            return (
                f"{len(self.positive)} of {len(spoke)} committees are "
                f"positive and {len(self.negative)} negative — they disagree."
            )

        if self.is_unanimous:
            return (
                f"All {len(spoke)} committees that spoke agree, and "
                f"{len(self.abstained)} abstained."
            )

        return (
            f"{len(spoke)} committees spoke without contradicting each "
            f"other, and {len(self.abstained)} abstained."
        )

    @staticmethod
    def _direction(opinion: CommitteeOpinion) -> str:
        """Which way an opinion points, ignoring how strongly.

        Strength is not a direction: *strongly positive* and *positive*
        are the same side of the argument, and a panel that counted
        them as disagreeing would report an argument between two
        committees that concur.
        """

        stance = opinion.stance

        if stance is None:
            return "silent"

        if stance.is_positive:
            return "positive"

        if stance.is_negative:
            return "negative"

        return "neutral"
