"""Compose today's executive briefing from what the cycle measured."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date

from app.brain import Brain
from app.domain.change_feed.change_event import (
    ChangeCategory,
    ChangeEvent,
    ChangeSeverity,
)
from app.domain.executive.today_briefing import BriefingLine, TodayBriefing

#: How far ahead a report still counts as "coming up" rather than merely
#: scheduled. A quarter's notice is not news; a week's is.
HORIZON_DAYS = 7

#: Highest first, so the day's most consequential change leads.
_SEVERITY_RANK = {
    ChangeSeverity.HIGH: 3,
    ChangeSeverity.MEDIUM: 2,
    ChangeSeverity.LOW: 1,
}


@dataclass(slots=True)
class TodayBriefingBuilder:
    """
    Count what changed and what is coming, and lead with what matters.

    Every line is a count of something the platform recorded — decisions
    it changed, reports the book's own companies have published dates for.
    Nothing is inferred, and nothing the platform does not record is
    mentioned: it never executes a trade and keeps no record of the
    investor's own, so it does not report on them either. A line saying
    "no portfolio actions executed" would be a claim about something
    nobody measured.
    """

    def build(
        self,
        brain: Brain,
        changes: Sequence[ChangeEvent],
        today: date,
    ) -> TodayBriefing:
        decisions = [
            change for change in changes if change.category is ChangeCategory.DECISION
        ]

        movements = [
            change
            for change in changes
            if change.category in (ChangeCategory.MARKET, ChangeCategory.MACRO)
        ]

        return TodayBriefing(
            lines=(
                self._decisions_line(decisions),
                self._earnings_line(brain, today),
                self._market_line(movements),
            ),
            headline=self._headline(decisions),
        )

    @staticmethod
    def _decisions_line(decisions: Sequence[ChangeEvent]) -> BriefingLine:
        """
        How many holdings the Artificial CIO changed its mind about.

        Holdings, not changes. The feed can hold three moves on one
        security across a week, and "3 recommendations changed" would be
        read as three securities — an overstatement of how much of the
        book actually moved, on the line meant to size the day.
        """

        if not decisions:
            return BriefingLine(
                statement="No recommendation changed since your last visit.",
            )

        securities = {
            change.symbol for change in decisions if change.symbol is not None
        }

        count = len(securities) or len(decisions)
        noun = "recommendation" if count == 1 else "recommendations"

        return BriefingLine(
            statement=f"{count} {noun} changed.",
            notable=True,
        )

    @staticmethod
    def _market_line(movements: Sequence[ChangeEvent]) -> BriefingLine:
        if not movements:
            return BriefingLine(
                statement=(
                    "The market's mood, volatility and sentiment are unchanged."
                ),
            )

        count = len(movements)
        noun = "movement" if count == 1 else "movements"

        return BriefingLine(
            statement=f"{count} market {noun} recorded.",
            notable=True,
        )

    @staticmethod
    def _earnings_line(brain: Brain, today: date) -> BriefingLine:
        """
        Which of the investor's own companies report, and how soon.

        Read from the schedules the cycle already gathered per security,
        rather than fetched again: the same reading that dates each case's
        catalyst dates this line, so the dashboard and the dossier can
        never disagree about when a company reports.
        """

        reporting_today: list[str] = []
        reporting_soon: list[str] = []
        unread = False

        for holding in brain.portfolio.holdings:
            company = brain.security_evidence(holding.symbol)

            schedule = company.signals.earnings if company is not None else None

            if schedule is None:
                continue

            if schedule.unread:
                unread = True
                continue

            window = schedule.window

            if window is None or not window.is_ahead_of(today):
                continue

            if window.starts_in_days(today) <= 0:
                reporting_today.append(holding.symbol)
            elif window.starts_in_days(today) <= HORIZON_DAYS:
                reporting_soon.append(holding.symbol)

        if reporting_today:
            count = len(reporting_today)
            noun = "company reports" if count == 1 else "companies report"

            return BriefingLine(
                statement=f"{count} {noun} earnings today: "
                f"{', '.join(sorted(reporting_today))}.",
                notable=True,
            )

        if reporting_soon:
            count = len(reporting_soon)
            noun = "company reports" if count == 1 else "companies report"

            return BriefingLine(
                statement=(
                    f"{count} {noun} within {HORIZON_DAYS} days: "
                    f"{', '.join(sorted(reporting_soon))}."
                ),
                notable=True,
            )

        if unread:
            # Not "no company reports": the calendar could not be read,
            # and reporting a provider failure as a quiet week is the one
            # thing this platform's calendar exists to avoid.
            return BriefingLine(
                statement=(
                    "The earnings calendar could not be read this cycle, so "
                    "nothing is claimed about who reports."
                ),
            )

        return BriefingLine(
            statement=(f"No company you hold reports within {HORIZON_DAYS} days."),
        )

    @staticmethod
    def _headline(decisions: Sequence[ChangeEvent]) -> str | None:
        """
        The one change that most deserves attention, or nothing at all.

        A briefing that produces a headline every morning teaches its
        reader that headlines mean nothing. Where the Artificial CIO
        changed no decision, there is no highest priority, and the space
        stays empty rather than being filled with the least uneventful
        fact available.

        Ranked by what the change asks for first, then by how far the
        decision actually moved — both measured, neither an opinion about
        importance.
        """

        if not decisions:
            return None

        leading = max(
            decisions,
            key=lambda change: (
                change.action_required,
                _SEVERITY_RANK.get(change.severity, 0),
                change.timestamp,
            ),
        )

        return leading.title
