"""What the investor needs to know today, before anything else."""

from datetime import UTC, datetime, timedelta

from app.application.brief.today_briefing_builder import (
    HORIZON_DAYS,
    TodayBriefingBuilder,
)
from app.domain.change_feed.change_event import (
    ChangeCategory,
    ChangeEvent,
    ChangeSeverity,
)
from tests.test_security_evidence import (
    TODAY,
    make_brain,
    make_company,
    make_holding,
    schedule,
)

NOW = datetime.now(UTC)


def decision(
    title: str,
    severity: ChangeSeverity = ChangeSeverity.LOW,
    action_required: bool = False,
    minutes_ago: int = 0,
) -> ChangeEvent:
    return ChangeEvent(
        title=title,
        description="Recorded at the time.",
        category=ChangeCategory.DECISION,
        severity=severity,
        timestamp=NOW - timedelta(minutes=minutes_ago),
        action_required=action_required,
        symbol=title.split(" ", 1)[0],
    )


def market(
    title: str = "Market mood moved from cautious to constructive",
) -> ChangeEvent:
    return ChangeEvent(
        title=title,
        description="Recorded between two observations.",
        category=ChangeCategory.MARKET,
        severity=ChangeSeverity.LOW,
        timestamp=NOW,
    )


def brief(changes=(), holdings=(), evidence=None):
    return TodayBriefingBuilder().build(
        make_brain(evidence or {}, holdings=holdings),
        changes,
        TODAY,
    )


def statements(briefing) -> tuple[str, ...]:
    return tuple(line.statement for line in briefing.lines)


def test_a_quiet_day_says_it_is_quiet_and_shows_no_headline() -> None:
    """
    The most common answer, and the one a briefing must be able to give.

    A page that manufactures a highest priority every morning teaches its
    reader that a highest priority means nothing. Nothing changed is
    information: it says do not act, which is the most frequently correct
    decision an investor makes.
    """

    briefing = brief()

    assert briefing.headline is None
    assert briefing.is_quiet is True

    assert "No recommendation changed since your last visit." in statements(briefing)
    assert not any(line.notable for line in briefing.lines)


def test_changed_recommendations_are_counted_not_characterised() -> None:
    """ "3 recommendations changed" can be checked against the feed below."""

    briefing = brief(
        changes=(
            decision("DIS moved from PREPARE to RECOMMEND"),
            decision("META moved from INVESTIGATE to PREPARE"),
            decision("SPCX moved from MONITOR to REJECT"),
        ),
    )

    assert "3 recommendations changed." in statements(briefing)
    assert briefing.is_quiet is False


def test_one_change_is_worded_as_one() -> None:
    briefing = brief(changes=(decision("DIS moved from PREPARE to RECOMMEND"),))

    assert "1 recommendation changed." in statements(briefing)


def test_the_headline_is_the_change_that_asks_for_something() -> None:
    """
    Ranked by what the change asks for, then by how far the decision moved.

    Both measured. Neither is an opinion about which name matters more.
    """

    briefing = brief(
        changes=(
            decision("META moved from PREPARE to INVESTIGATE", ChangeSeverity.HIGH),
            decision(
                "DIS moved from PREPARE to RECOMMEND",
                ChangeSeverity.LOW,
                action_required=True,
            ),
        ),
    )

    assert briefing.headline == "DIS moved from PREPARE to RECOMMEND"


def test_a_company_reporting_today_leads_the_earnings_line() -> None:
    briefing = brief(
        holdings=(make_holding("MSFT"),),
        evidence={"MSFT": (make_company("MSFT", earnings=schedule(TODAY)),)},
    )

    assert "1 company reports earnings today: MSFT." in statements(briefing)


def test_reports_inside_the_horizon_are_named_and_the_rest_are_not() -> None:
    """A quarter's notice is not news; a week's is."""

    soon = TODAY + timedelta(days=HORIZON_DAYS - 1)
    later = TODAY + timedelta(days=HORIZON_DAYS + 40)

    briefing = brief(
        holdings=(make_holding("SOON"), make_holding("LATER")),
        evidence={
            "SOON": (make_company("SOON", earnings=schedule(soon)),),
            "LATER": (make_company("LATER", earnings=schedule(later)),),
        },
    )

    line = next(item for item in statements(briefing) if "report" in item)

    assert "SOON" in line
    assert "LATER" not in line


def test_a_book_with_nothing_scheduled_says_so() -> None:
    briefing = brief(
        holdings=(make_holding("MSFT"),),
        evidence={"MSFT": (make_company("MSFT", earnings=schedule()),)},
    )

    assert f"No company you hold reports within {HORIZON_DAYS} days." in (
        statements(briefing)
    )


def test_a_calendar_that_could_not_be_read_is_never_a_quiet_week() -> None:
    """The absence the whole earnings calendar exists to keep apart."""

    briefing = brief(
        holdings=(make_holding("MSFT"),),
        evidence={"MSFT": (make_company("MSFT", earnings=schedule(unread=True)),)},
    )

    line = next(item for item in statements(briefing) if "calendar" in item)

    assert "could not be read" in line
    assert "No company you hold reports" not in " ".join(statements(briefing))


def test_market_movements_are_counted_apart_from_decisions() -> None:
    """
    What the market did is not what the Artificial CIO decided.

    Counting them together would let three sentiment readings look like
    three changes of mind.
    """

    briefing = brief(changes=(market(), market("Volatility moved to elevated")))

    assert "2 market movements recorded." in statements(briefing)
    assert "No recommendation changed since your last visit." in statements(briefing)

    # A market that moved is not, by itself, a highest priority.
    assert briefing.headline is None


def test_the_platform_never_reports_on_actions_it_cannot_see() -> None:
    """
    It recommends; the investor decides, and nothing records what they did.

    "No portfolio actions executed" would be a claim about something
    nobody measured, so no line here makes it.
    """

    assert not any("executed" in statement for statement in statements(brief()))


def test_holdings_are_counted_rather_than_changes() -> None:
    """
    Three moves on one security is one holding changing, not three.

    The account really does record a security moving out and back within
    a week, and counting the moves would tell the investor more of their
    book had changed than actually did.
    """

    briefing = brief(
        changes=(
            decision("DIS moved from PREPARE to RECOMMEND"),
            decision("DIS moved from RECOMMEND to PREPARE", minutes_ago=60),
            decision("META moved from INVESTIGATE to PREPARE"),
        ),
    )

    assert "2 recommendations changed." in statements(briefing)
