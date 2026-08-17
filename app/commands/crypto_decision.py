"""What the Artificial CIO concludes about one digital asset. A read.

The last surface of the convergence arc. The same canonical answer the
crypto dossier renders, the portfolio brief carries and the research
pipeline admits on — asked from a terminal, and asked rather than
computed: this command owns no rule, no threshold and no wording of its
own, and every sentence it prints was worded by the layer that
established it.

**Read-only, deliberately, and the CLI's own law decides it.** `judge`
is the one verb that writes, and it says why: *rendering must not
manufacture events, or "the committee has reviewed this eleven times"
becomes a count of page views wearing the language of review*. The
canonical decision is a projection over what `judge` recorded, so
printing it must not append to the journal. The write already happens
where a decision is genuinely executed — the portfolio, dossier and
research paths, and `evaluate` — through the one writer DV6 established.

There is therefore no second journal writer here, and no second
constructor of crypto investment meaning.
"""

from __future__ import annotations

import textwrap

from app.cio.digital_asset_decision import DigitalAssetDecision
from app.domain.crypto_archetype import ASSIGNMENTS
from app.services.digital_asset_decision_service import (
    DigitalAssetDecisionService,
)


class CryptoDecisionCommand:
    """Ask the canonical crypto decision path what this platform thinks."""

    def __init__(self, service: DigitalAssetDecisionService | None = None) -> None:
        self._service = service or DigitalAssetDecisionService()

    def run(self, symbol: str | None = None) -> int:
        if symbol is None:
            return self._corpus()

        decision = self._service.decide(symbol)

        if not decision.judged:
            # True of an asset no committee has looked at, and equally
            # true of a symbol that is not a digital asset at all. It
            # claims neither: it says only what this platform holds,
            # which is the sentence the bridge already prints for the
            # same state.
            #
            # Exit 0, measured against the siblings rather than assumed:
            # `crypto-playbook`, `crypto-market`, `committees`,
            # `committee-judgment` and `considerations` all report an
            # unheld asset and exit 0. A non-zero code in this CLI means
            # the command could not do its job, and this command did —
            # the answer is that there is no decision, and saying so is
            # not a failure.
            print()
            print(
                _wrap(
                    f"{decision.symbol} — no committee has recorded a judgment "
                    "for this asset, so this platform has reached no decision "
                    "about it. That is a statement about this platform rather "
                    "than about the asset, and it is not a verdict against it.",
                    "  ",
                )
            )
            print()

            return 0

        _render(decision)

        return 0

    def _corpus(self) -> int:
        """Every asset this platform reads, one line each.

        `ASSIGNMENTS` enumerates the corpus here, exactly as the other
        crypto verbs use it — which asset to *iterate*, never which
        asset *is* one. Nothing below asks it to classify anything.
        """

        print()
        print("What the Artificial CIO concludes, per digital asset")
        print()

        for asset in sorted(ASSIGNMENTS):
            decision = self._service.decide(asset)

            posture = decision.state.value if decision.judged else "not judged"

            print(f"  {asset:<8} {posture}")

        print()
        print(
            _wrap(
                "No conviction appears above and none exists: what a "
                "structural conclusion is worth to an investment case is not "
                "established by this platform, so no number is stated and "
                "these postures are not ordered against each other.",
                "  ",
            )
        )

        return 0


def _render(decision: DigitalAssetDecision) -> None:
    print()
    print(f"{decision.symbol} — {decision.state.value}")
    print()
    print(_wrap(decision.rationale, "  "))
    print()

    # Named, never omitted and never a zero. An absent conviction that
    # printed nothing would read as a surface that forgot to show one.
    print("  conviction: withheld")
    print(_wrap(decision.conviction_withheld_because, "    "))
    print()

    _section("What is established", decision.established)

    _section(
        "The wrong instrument for this asset — knowledge, never adverse",
        decision.not_applicable,
    )

    _section(
        "Open questions, each in its owner's words",
        tuple(f"{item.owner}: {item.stated}" for item in decision.unresolved),
    )

    _section(
        "Material uncertainty — stated as uncertainty, never as adverse",
        decision.material_uncertainties,
    )

    if decision.adverse:
        _section("Against this asset", decision.adverse)
    else:
        print(_wrap(decision.adverse_absent, "  "))
        print()

    if decision.silent_committees:
        print(
            _wrap(
                "Committees with no recorded judgment: "
                + ", ".join(decision.silent_committees)
                + ". A committee that never ran is not one that answered.",
                "  ",
            )
        )
        print()

    print(_wrap(decision.ceiling, "  "))
    print()

    # The authority, and what it rests on. A record of this decision
    # carries both, so a reader can ask whether the answer they are
    # looking at came from the rule and the judgments they think it did.
    print(
        "  decided under: "
        + ", ".join(rule.identity for rule in decision.decided_under)
    )

    print("  rests on the recorded judgments:")

    for reference in decision.judgment_ids:
        print(f"    {reference}")

    print()


def _section(title: str, lines: tuple[str, ...]) -> None:
    if not lines:
        return

    print(f"  {title}")

    for line in lines:
        print(_wrap(f"— {line}", "    "))

    print()


def _wrap(text: str, indent: str) -> str:
    return textwrap.fill(
        text,
        width=76,
        initial_indent=indent,
        subsequent_indent=indent + "  ",
    )


async def run(symbol: str | None = None) -> int:
    return CryptoDecisionCommand().run(symbol)
