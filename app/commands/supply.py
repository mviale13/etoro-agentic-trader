"""What each supply number counts, and which of them really disagree.

Read-only: it asks the stores what `movrvest acquire` left behind and
stops. No provider is called, no model is asked, nothing is stored.

The command exists because "sources conflict" was hiding three correct
readings of the same ledger. What it prints instead is the vocabulary —
which quantity each source is reporting, whose definition decided it,
and whether two numbers are a disagreement or simply two different
facts.

Nothing here interprets. Dilution, tokenomics and supply pressure are
words this command does not know.
"""

from __future__ import annotations

from app.domain.asset_class import AssetClass
from app.domain.supply_semantics import (
    Comparison,
    SupplyConcept,
    SupplyFact,
    SupplyPicture,
)
from app.providers.coingecko_facts_provider import COINGECKO_IDS
from app.services.supply_semantics_service import SupplySemanticsService

_ORDER = (
    SupplyConcept.MAX_SUPPLY,
    SupplyConcept.EMITTED_SUPPLY,
    SupplyConcept.FUTURE_EMISSIONS,
    SupplyConcept.CIRCULATING_ESTIMATE,
    SupplyConcept.EXCLUDED_BALANCE,
)


class SupplyCommand:
    def run(self, symbol: str | None = None) -> int:
        service = SupplySemanticsService()

        if symbol is None:
            _render_corpus(service)
            return 0

        normalized = symbol.upper().strip()

        picture = service.established(normalized, AssetClass.CRYPTO)

        if picture is None:
            print(f"{normalized} — no supply picture: this is not a digital asset.")
            return 1

        _render(picture)

        return 0 if picture.is_read else 1


def _render(picture: SupplyPicture) -> None:
    print(f"{picture.symbol} — supply")
    print("=" * 74)

    if not picture.is_read:
        print()
        print(_wrap(picture.unavailable_because or "Nothing has been read.", "  "))
        print()
        return

    for concept in _ORDER:
        facts = picture.of(concept)

        if not facts:
            continue

        print()
        print(f"  {concept.stated} — {concept.described}")

        for fact in facts:
            _render_fact(fact)

    if picture.comparisons:
        print()
        print("  How the figures relate")

        for item in sorted(
            picture.comparisons,
            key=lambda entry: entry.verdict.value,
        ):
            print()
            print(
                f"    [{item.verdict.stated}] {item.left.source} "
                f"{item.left.stated} · {item.right.source} {item.right.stated}"
            )
            print(_wrap(item.because, "      "))

    if picture.unresolved:
        print()
        print("  Unresolved")

        for line in picture.unresolved:
            print(_wrap(f"- {line}", "    "))

    print()


def _render_fact(fact: SupplyFact) -> None:
    label = fact.reported_as or fact.methodology.defined_by

    print(f"    {fact.source:<26} {fact.value:>22,.4f}  ({label})")
    print(_wrap(f"{fact.methodology.defined_by}: {fact.methodology.stated}", "      "))

    if fact.methodology.excludes:
        print(_wrap("excludes " + "; ".join(fact.methodology.excludes), "      "))

    if fact.because:
        print(_wrap(fact.because, "      "))

    for caveat in fact.caveats:
        print(_wrap(f"caveat: {caveat}", "      "))


def _render_corpus(service: SupplySemanticsService) -> None:
    print("CRYPTO SUPPLY — what each number counts")
    print("=" * 74)
    print()
    print(
        _wrap(
            "Two numbers conflict only if they claim to represent the same "
            "thing. A difference between two different quantities is "
            "information, not a contradiction.",
            "  ",
        )
    )
    print()
    print(f"  {'':<8}{'facts':>7}{'agree':>7}{'coexist':>9}{'conflict':>10}  chain")
    print()

    for symbol in sorted(COINGECKO_IDS):
        picture = service.established(symbol, AssetClass.CRYPTO)

        if picture is None:
            continue

        agree = sum(
            1 for item in picture.comparisons if item.verdict is Comparison.CORROBORATED
        )

        chain = any(fact.authority.is_primary for fact in picture.facts)

        print(
            f"  {symbol:<8}{len(picture.facts):>7}{agree:>7}"
            f"{len(picture.coexisting):>9}{len(picture.conflicts):>10}"
            f"  {'read' if chain else '—'}"
        )

    print()


def _wrap(text: str, indent: str, width: int = 86) -> str:
    words = text.split()
    lines: list[str] = []
    current = indent
    hanging = indent + "  "

    for word in words:
        if len(current) + len(word) + 1 > width and current.strip():
            lines.append(current.rstrip())
            current = hanging

        current += word + " "

    if current.strip():
        lines.append(current.rstrip())

    return "\n".join(lines)


async def run(symbol: str | None = None) -> int:
    return SupplyCommand().run(symbol)
