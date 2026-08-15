"""What the committees establish, addressed to an investment layer.

Read-only, no model, no fetch. It projects recorded judgments and prints
them; it convenes nothing, so opening it can never manufacture a
judgment event.

**Deliberately a CLI surface and not a dossier section.** The crypto
dossier already renders every committee's conclusion, with its question,
applicability, reasoning, confidence and provenance, in *What each
committee concluded*. A second section reading *What the committees
establish* would print the same conclusions a second time — which is the
exact defect PR #126 spent a slice removing, arriving one slice later
under a new name. The bridge's investor-facing value is what it makes
*possible*, and nothing consumes it yet; when something does, that
consumer earns the surface.

What this shows that no other surface does is the second half of each
line: whether this platform has established what a conclusion means for
an investment case. Today it has not, for any of them, and printing that
plainly beside sixteen real conclusions is the honest state of the
bridge.
"""

from __future__ import annotations

import textwrap

from app.domain.crypto_archetype import ASSIGNMENTS
from app.domain.investment_consideration import AssetConsiderations
from app.services.decision_bridge_service import DecisionBridgeService


class ConsiderationsCommand:
    async def run(self, symbol: str | None = None) -> int:
        service = DecisionBridgeService()

        assets = [symbol.upper().strip()] if symbol else sorted(ASSIGNMENTS)

        for asset in assets:
            self._render(service.considerations(asset))

        print()
        print(
            _wrap(
                "Each line is one committee's own conclusion, carried "
                "without being weighted, ranked or combined. The second "
                "half of each line is this platform's view of what that "
                "conclusion means for an investment case — and where it "
                "says nothing is established, that is a statement about "
                "this platform rather than about the asset. No layer here "
                "has ever written a rule turning a structural verdict into "
                "an investment effect, so none is applied.",
                "  ",
            )
        )

        return 0

    def _render(self, considered: AssetConsiderations) -> None:
        print()
        print(f"{considered.asset} — what the committees establish")
        print()

        if not considered.considerations:
            print(
                _wrap(
                    "No committee has recorded a judgment for this asset, so "
                    "there is nothing to carry forward. That is a statement "
                    "about this platform rather than about the asset.",
                    "  ",
                )
            )

        for item in considered.considerations:
            print(f"  {item.committee.name} v{item.committee.version}")

            if item.question:
                print(_wrap(f"question: {item.question}", "    "))

            print(_wrap(f"conclusion: {item.posture.stated}", "    "))

            if item.conclusion_stated:
                print(_wrap(f"  — {item.conclusion_stated}", "    "))

            if item.because:
                print(_wrap(f"because: {item.because}", "    "))

            print(_wrap(f"investment effect: {item.effect.stated}", "    "))

            print(
                f"    confidence: {item.confidence.stated if item.confidence else '—'}"
            )
            print(f"    judgment: {item.judgment_id}")
            print(f"    bridge policy: v{item.policy_version}")
            print()

        for name in considered.silent:
            print(f"  {name}")
            print(
                _wrap(
                    "has recorded no judgment for this asset, which is a "
                    "different fact from having reached no usable answer.",
                    "    ",
                )
            )
            print()


def _wrap(text: str, indent: str) -> str:
    return textwrap.fill(
        text,
        width=76,
        initial_indent=indent,
        subsequent_indent=indent + "  ",
    )


async def run(symbol: str | None = None) -> int:
    return await ConsiderationsCommand().run(symbol)
