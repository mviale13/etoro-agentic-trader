"""Which durable qualities of a token this platform can judge, and why not.

Two readings of the same model. With a symbol it shows one asset: the
headline or the honest absence of one, the coverage beneath it, every
applicable question with how it participated, and — for the questions
that are shown rather than scored — the evidence itself, each line
carrying its standing. Without one it shows the corpus as a matrix,
where a column of *not yet answerable* is the acquisition roadmap and a
column of *not applicable* is a list of things it would be wrong to
acquire.

Read-only, like every surface in this phase: it asks the stores what
they hold and stops. No provider is called, no model is asked, and
nothing is stored.
"""

from __future__ import annotations

from app.domain.asset_class import AssetClass
from app.domain.crypto_archetype import ASSIGNMENTS, archetype_for
from app.domain.crypto_quality import (
    RULES,
    CryptoAssetQuality,
    QualityAnswer,
    QuestionParticipation,
    readiness_for,
)
from app.domain.crypto_questions import QUESTIONS
from app.services.crypto_asset_quality_service import CryptoAssetQualityService

_MARK = {
    QuestionParticipation.SCORED: "SCORED",
    QuestionParticipation.SCORABLE_UNANSWERED: "unans",
    QuestionParticipation.SHOWN: "shown",
    QuestionParticipation.UNANSWERABLE: "—",
    QuestionParticipation.OUTSIDE: "out",
    QuestionParticipation.NOT_APPLICABLE: "n/a",
    QuestionParticipation.UNDETERMINED: "?",
}


class CryptoQualityCommand:
    def run(self, symbol: str | None = None) -> int:
        service = CryptoAssetQualityService()

        if symbol is None:
            _render_matrix(service)
            return 0

        normalized = symbol.upper().strip()

        quality = service.established(normalized, AssetClass.CRYPTO)

        if quality is None:
            print(f"{normalized} — no asset quality: this is not a digital asset.")
            return 1

        _render(quality)

        return 0


# ── one security ────────────────────────────────────────────────────


def _render(quality: CryptoAssetQuality) -> None:
    assignment = archetype_for(quality.symbol)

    print(f"{quality.symbol} — Asset quality")
    print(f"  {assignment.definition.name} · {assignment.confidence.stated}")
    print()

    if quality.quality == "UNKNOWN":
        print("  Asset quality      not assessed")
    else:
        print(
            f"  Asset quality      {quality.quality} "
            f"({quality.earned} of {quality.available} points)"
        )

    coverage = quality.coverage

    print(
        f"  Evidence coverage  {coverage.answered} of {coverage.scorable} "
        f"scorable questions answered, "
        f"{coverage.scorable} of {coverage.in_scope} questions scorable"
    )
    print(f"  Confidence         {quality.confidence}")
    print()
    print(_wrap(quality.because, "  "))
    print()

    _section(
        "Scored",
        quality,
        (QuestionParticipation.SCORED,),
        detail=True,
    )
    _section(
        "Scorable, unanswered",
        quality,
        (QuestionParticipation.SCORABLE_UNANSWERED,),
        detail=True,
    )
    _section(
        "Shown, not scored",
        quality,
        (QuestionParticipation.SHOWN,),
        detail=True,
    )
    _section(
        "Not yet answerable",
        quality,
        (QuestionParticipation.UNANSWERABLE,),
        detail=False,
    )
    _section(
        "Outside asset quality",
        quality,
        (QuestionParticipation.OUTSIDE,),
        detail=False,
    )
    _section(
        "Not asked of this asset",
        quality,
        (QuestionParticipation.NOT_APPLICABLE,),
        detail=False,
    )
    _section(
        "Applicability undetermined",
        quality,
        (QuestionParticipation.UNDETERMINED,),
        detail=False,
    )


def _section(
    title: str,
    quality: CryptoAssetQuality,
    states: tuple[QuestionParticipation, ...],
    detail: bool,
) -> None:
    answers = [answer for answer in quality.answers if answer.participation in states]

    if not answers:
        return

    print(f"  {title}")

    for answer in answers:
        _answer(answer, detail)

    print()


def _answer(answer: QualityAnswer, detail: bool) -> None:
    question = QUESTIONS[answer.question]

    print(f"    {question.label}")

    if answer.band is not None and answer.rule is not None:
        print(
            f"      {answer.band.verdict.upper()} · "
            f"{_money(answer.value or 0)} · "
            f"{answer.source or 'source unrecorded'} · "
            f"rule {answer.rule.name}@{answer.rule.version}"
        )

    if not detail:
        print(_wrap(answer.because, "      "))
        return

    print(_wrap(answer.because, "      "))

    for line in answer.shown:
        print(_wrap(f"· {line}", "      "))


# ── the corpus ──────────────────────────────────────────────────────


def _render_matrix(service: CryptoAssetQualityService) -> None:
    symbols = sorted(ASSIGNMENTS)

    print("Crypto asset quality — the corpus")
    print()
    print("  One question of nineteen is scorable today, and a headline band")
    print("  requires two. Every column below is a question; every cell says")
    print("  how that question participated for that asset.")
    print()

    results = {
        symbol: service.established(symbol, AssetClass.CRYPTO) for symbol in symbols
    }

    print(f"  {'':7s} {'quality':9s} {'conf':>4s}  {'scored':>6s} {'scorable':>8s}")

    for symbol in symbols:
        quality = results[symbol]

        if quality is None:
            continue

        print(
            f"  {symbol:7s} {quality.quality:9s} {quality.confidence:4d}  "
            f"{quality.coverage.answered:6d} "
            f"{quality.coverage.scorable:8d}"
        )

    print()
    print("  Question readiness — a property of the question, not of any asset")
    print()

    for key in QUESTIONS:
        ruling = readiness_for(key)

        rule = RULES.get(key)

        print(
            f"    {QUESTIONS[key].label:28s} {ruling.readiness.stated:22s} "
            + (f"rule {rule.name}@{rule.version}" if rule is not None else "")
        )

    print()
    print("  Per asset")
    print()

    for symbol in symbols:
        quality = results[symbol]

        if quality is None:
            continue

        marks = " ".join(
            f"{_MARK[answer.participation]:>6s}" for answer in quality.answers
        )

        print(f"    {symbol:7s} {marks}")

    print()
    print("    Columns, in order:")

    for index, key in enumerate(QUESTIONS, start=1):
        print(f"      {index:2d}. {QUESTIONS[key].label}")


def _money(value: float) -> str:
    if abs(value) >= 1_000_000_000:
        return f"${value / 1_000_000_000:,.2f}bn"

    if abs(value) >= 1_000_000:
        return f"${value / 1_000_000:,.1f}m"

    if abs(value) >= 1_000:
        return f"${value / 1_000:,.1f}k"

    return f"${value:,.2f}"


def _wrap(text: str, indent: str, width: int = 78) -> str:
    words = text.split()
    lines: list[str] = []
    current = indent

    for word in words:
        if len(current) + len(word) + 1 > width and current.strip():
            lines.append(current.rstrip())
            current = indent + (" " * 2 if text.startswith(("-", "·")) else "")

        current += word + " "

    if current.strip():
        lines.append(current.rstrip())

    return "\n".join(lines)


async def run(symbol: str | None = None) -> int:
    return CryptoQualityCommand().run(symbol)
