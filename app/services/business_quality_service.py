"""The grounded quality assessment for one company, from stored evidence only.

Read-only, like every consumption door on this platform. It asks the
statement store what it already holds and stops: no filing is fetched,
no model is asked, and no provider is called. A quality score that
spent money to compute would put an acquisition behind an evaluation.

**The two routes never blend.** Where the statements support a grounded
assessment, it governs and the provider-fed proxy is not consulted;
where they do not, the proxy stands unchanged and the basis says which
route ran. That is the migration rule this platform has applied twice
before — the filing-grade route outgrows the provider-fed one, one
authoritative case at a time, never by wrapping it.
"""

from __future__ import annotations

from app.domain.business_quality import BusinessQuality, assess
from app.domain.financial_question import FinancialModel
from app.domain.financial_understanding import FinancialUnderstanding
from app.services.financial_questions import answer_questions


def quality_of(
    symbol: str,
    understanding: FinancialUnderstanding | None,
    model: FinancialModel = FinancialModel.GENERIC,
) -> BusinessQuality | None:
    """What the established statements say about this business.

    `None` where there is nothing to assess — no understanding at all,
    or one that has not reached quorum. Below quorum this platform does
    not call a claim established, and a quality score resting on one
    reading would present a draw as the account.

    The model is passed in rather than resolved here. Which financial
    language reads a company is decided by a layer that already owns
    it, and re-deriving it would be a second place for that decision to
    live.
    """

    if understanding is None or not understanding.quorate:
        return None

    return assess(
        symbol=symbol,
        answers=answer_questions(model, understanding),
        source=understanding.source,
        # Carried, never consulted. The answers above are produced from
        # `understanding.measures`, which this quantity is in none of, so
        # the band is what it was before this line existed — and the
        # reason a bank's margins are unavailable stops looking like a
        # filer that printed nothing.
        incomparable_top_line=understanding.incomparable_top_line,
    )
