"""Recent articles a provider associates with a ticker, and nothing more.

This is a discovery surface. It is not a News Analyst, not a Company
Development Radar, not evidence, not a materiality assessment and not a
recommendation — and the type system is where that is enforced rather
than the prose: there is no field here for a score, a cluster, a topic
or a verdict, and a lead's status has exactly one member.

Four measurements from `MASSIVE_FREE_PERSONAL_NEWS_MEASUREMENT.md`
shape every decision below.

**A ticker association is not aboutness.** One article in the measured
corpus carries 44 tickers. So `associated_ticker_count` travels with
every lead and is shown, and where it exceeds one the lead words the
caveat itself. It is a disclosure, never a filter: no threshold rejects
an article for naming too many companies, because no measurement earned
one.

**The provider has no last-updated field.** There is deliberately no
`updated_at` here. A null one would imply the provider could fill it.

**The provider's sentiment is quoted, and only as an icon.** It is read
from the `insights` entry for the *exact* queried ticker — another
associated ticker's opinion is a different opinion about a different
company — and normalised to two directions or nothing, because the
measured field emitted `positive`, `negative`, `bullish`, `bearish`,
`neutral` and `mixed` through one key, which is more than one scale.
`sentiment_reasoning` is not carried in any form: an icon is a
quotation and a paragraph is an argument. Invariant 10 governs the
rest — the classification is Massive's and so is its meaning, and this
platform says whose it is rather than adopting it.

**A ticker can change hands.** `PARA` resolved to Paramount Global in
2023 and to Banzai International today, and a news item carries only the
bare symbol — no CIK, no FIGI. So identity is decided for the whole page
before any of it is shown, and the outcome of that decision is a
property of the *result*, not of a lead.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum


class LeadStatus(StrEnum):
    """What a displayed lead is. There is one, and that is the point."""

    DISPLAY_ONLY = "DISPLAY_ONLY"


class ProviderSentiment(StrEnum):
    """Massive's own classification for the queried ticker, as quoted.

    Two members and no third. `neutral`, `mixed`, `unknown`, an absent
    insight and two insights for the same ticker that disagree all
    resolve to `None` rather than to a member — a middle value would be
    this platform's reading of the provider's uncertainty, and reading
    it is exactly what this feature does not do.
    """

    POSITIVE = "positive"
    NEGATIVE = "negative"


#: What the provider prints, and what this platform is willing to quote
#: it as. `bullish`/`bearish` sit in the same field as
#: `positive`/`negative` in the measured corpus — two scales through one
#: key — so both spellings collapse to one direction and everything else
#: is dropped rather than guessed at.
_SENTIMENT_DIRECTIONS = {
    "positive": ProviderSentiment.POSITIVE,
    "bullish": ProviderSentiment.POSITIVE,
    "negative": ProviderSentiment.NEGATIVE,
    "bearish": ProviderSentiment.NEGATIVE,
}


def provider_sentiment_for(ticker: str, insights: object) -> ProviderSentiment | None:
    """Massive's classification for exactly this ticker, or nothing.

    Selected on the insight's own `ticker`, never on position and never
    from the article's other associations: an article naming forty-four
    companies carries opinions about forty-four companies, and the only
    one that may be shown here is the one about the company being asked
    about.

    Where the exact ticker carries several insights that do not agree,
    the answer is nothing. Taking the first would hide the provider's
    own disagreement, and taking a majority would be this platform
    deciding what the provider meant.
    """

    if not isinstance(insights, list):
        return None

    directions = [
        _SENTIMENT_DIRECTIONS.get(str(entry.get("sentiment", "")).strip().casefold())
        for entry in insights
        if isinstance(entry, dict)
        and str(entry.get("ticker", "")).strip().upper() == ticker.strip().upper()
    ]

    # One insight, and one this platform is willing to quote. Anything
    # else — none, several that disagree, or a value outside the two
    # directions — shows no icon.
    if len(set(directions)) != 1:
        return None

    return directions[0]


class NewsOutcome(StrEnum):
    """What became of one request for a ticker's news."""

    #: Identity held for the whole window and there are items to show.
    DISPLAY_ONLY = "DISPLAY_ONLY"

    #: The ticker resolved to different issuers at the two ends of the
    #: returned window. The whole result is refused — not filtered,
    #: because nothing in a news item says which issuer it belongs to.
    ISSUER_REASSIGNED = "ISSUER_REASSIGNED"

    #: The reference lookup returned nothing, or returned a record with
    #: no CIK. An unidentified issuer is not a permissive default.
    IDENTITY_UNRESOLVED = "IDENTITY_UNRESOLVED"

    #: The provider could not be read — an error, a refusal, or the
    #: rate limit reached. Never retried.
    PROVIDER_UNAVAILABLE = "PROVIDER_UNAVAILABLE"

    #: The provider returned an empty page. It means that and nothing
    #: else; see `stated`.
    NO_ITEMS_RETURNED = "NO_ITEMS_RETURNED"

    #: A runtime gate is closed. No provider call was attempted.
    NOT_ENABLED = "NOT_ENABLED"


@dataclass(frozen=True, slots=True)
class PersonalNewsLead:
    """One article the provider associates with the queried ticker.

    Every field is the provider's own, unchanged. Nothing here is
    summarised, scored, ranked, clustered or interpreted by this
    platform.

    `provider_sentiment` is the one thing quoted rather than merely
    passed through, and it is quoted narrowly: Massive's classification
    for this exact ticker, reduced to a direction or to nothing, with
    the provider's reasoning left behind entirely. It is shown as an
    icon and it reaches nothing — it does not order this list, does not
    filter it, is never counted, and no field on this type or any other
    aggregates it.
    """

    provider_article_id: str
    queried_ticker: str
    associated_tickers: tuple[str, ...]
    headline: str
    provider_summary: str
    publisher_name: str
    author: str
    published_at: datetime
    article_url: str

    #: Massive's classification for the queried ticker, or nothing.
    #: Never inferred from the headline or the summary, and never taken
    #: from another associated ticker's insight.
    provider_sentiment: ProviderSentiment | None = None

    status: LeadStatus = LeadStatus.DISPLAY_ONLY

    @property
    def associated_ticker_count(self) -> int:
        return len(self.associated_tickers)

    def stated_sentiment(self) -> str:
        """The icon's accessible wording, naming whose opinion it is."""

        if self.provider_sentiment is None:
            return ""

        return f"Massive sentiment: {self.provider_sentiment.value}"

    def stated_association(self) -> str:
        """What this platform can say about the article's relevance.

        Worded here rather than on a surface, because it is a claim
        about evidence and the frontend is not allowed to author one.
        """

        if self.associated_ticker_count > 1:
            return (
                f"This article is associated with "
                f"{self.associated_ticker_count} tickers; relevance to "
                f"{self.queried_ticker} has not been verified."
            )

        return (
            f"Associated with {self.queried_ticker} only; relevance has "
            "not been verified."
        )


@dataclass(frozen=True, slots=True)
class PersonalNewsResult:
    """One asking of one ticker, and what may be shown for it."""

    queried_ticker: str
    outcome: NewsOutcome
    retrieved_at: datetime

    leads: tuple[PersonalNewsLead, ...] = ()

    #: The issuer the ticker resolved to at each end of the returned
    #: window. Both empty where no lookup was made or none resolved.
    identity_now: str = ""
    identity_at_oldest: str = ""

    @property
    def stated(self) -> str:
        """Why this result is what it is, in words a surface prints."""

        if self.outcome is NewsOutcome.DISPLAY_ONLY:
            return (
                f"Recent articles Massive associates with "
                f"{self.queried_ticker}. These items have not been "
                "assessed or verified by MOVRvest."
            )

        if self.outcome is NewsOutcome.ISSUER_REASSIGNED:
            return (
                f"{self.queried_ticker} does not identify one company "
                "across the period these articles cover: the ticker "
                f"resolves to CIK {self.identity_now} today and to CIK "
                f"{self.identity_at_oldest} at the oldest article's "
                "date. Nothing is shown, because a news item carries "
                "only the symbol and cannot say which company it is "
                "about."
            )

        if self.outcome is NewsOutcome.IDENTITY_UNRESOLVED:
            return (
                f"The company behind {self.queried_ticker} could not be "
                "identified from the provider's own reference data, so "
                "no articles are shown."
            )

        if self.outcome is NewsOutcome.PROVIDER_UNAVAILABLE:
            return (
                "Massive could not be read just now, so no articles are "
                "shown. Nothing was retried."
            )

        if self.outcome is NewsOutcome.NO_ITEMS_RETURNED:
            return (
                f"Massive returned no articles for {self.queried_ticker}. "
                "That means only that Massive returned none — it does "
                "not mean no material development occurred."
            )

        return (
            "Personal Ticker News is not enabled. It is a private, "
            "single-user feature and stays off until it is switched on "
            "explicitly."
        )

    @property
    def coverage_notice(self) -> str:
        """The limitation the corpus measured, shown wherever leads are.

        Five publishers wrote all 600 articles in the measured sample and
        one of them wrote 67% of them. A reader who is not told that will
        read an empty or thin feed as an absence of news.
        """

        return (
            "At most the latest three articles returned by the provider "
            "are shown — never complete coverage. Publisher coverage is "
            "limited and may be concentrated, and no items returned does "
            "not mean that no material development occurred."
        )

    @property
    def sentiment_notice(self) -> str:
        """Whose classification the icons are, said where they are shown.

        Worded here rather than on the surface for the same reason every
        other sentence is: an icon that appears beside a headline on this
        platform's page will be read as this platform's opinion unless
        the page says otherwise, and what it says is a claim about
        evidence.
        """

        return (
            "Sentiment icons, where present, show Massive's "
            "classification for this ticker. They are not MOVRvest "
            "analysis."
        )
