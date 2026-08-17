"""Everything this platform can say about one digital asset. A read.

**Its own endpoint, deliberately, and the reason is measured.**
`/executive/{symbol}/dossier` runs the brain pipeline and takes ~12
seconds; the whole crypto analytical composition below takes ~19
milliseconds, because every layer it reads is a stored door. That is
not a performance note — it is the shape of the thing. The equity
dossier composes a *decision*, and a decision needs the pipeline. This
composes what is *known*, and nothing here decides anything.

The second reason is that the equity dossier was answering crypto
questions with equity vocabulary. Asked for BTC today it leads with a
conviction of 46, a committee agreement of 0.5, a safety score of 35
and the Investment and Risk Committees — none of which comes from any
crypto evidence, while Fee Capture, Supply Governance, the investor
assessment and Asset Quality appear nowhere. A token is not a company
with different labels, and a surface that says otherwise is the failure
`DOSSIER_DEFINITION` was built to prevent, one level up.

**Nothing here is computed.** Every field is a state or a sentence the
domain already settled: applicability from the archetype, meaning from
the licensing contract, verdicts in each committee's own words, bands
that today are absent for every asset and say why. There is no score,
no aggregate, no agreement, no ranking and no ordering that means
anything — the same refusals `/committees/{symbol}` already states, held
across nine more families.

**And it acquires nothing.** Every service is opened at its read-only
door, so requesting this page cannot fetch, cannot ask a model and
cannot manufacture a judgment event. `movrvest acquire` and
`movrvest judge` remain the only two spends.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException

from app.api.dependencies import get_issuance_rule_provider
from app.api.models.asset_profile_adapter import asset_profile_response
from app.api.models.crypto_dossier_adapter import (
    asset_quality_response,
    intelligence_response,
    issuance_response,
    journal_response,
)
from app.api.models.crypto_market_adapter import crypto_market_response
from app.api.models.crypto_playbook_adapter import crypto_playbook_response
from app.api.models.protocol_adapter import protocol_fundamentals_response
from app.api.models.supply_adapter import supply_response
from app.domain.asset_class import AssetClass
from app.domain.crypto_archetype import ASSIGNMENTS
from app.providers.issuance_rule_provider import IssuanceRuleProvider
from app.services.committee_matrix_service import CommitteeMatrixService
from app.services.crypto_asset_quality_service import CryptoAssetQualityService
from app.services.crypto_intelligence_service import CryptoIntelligenceService
from app.services.crypto_market_service import CryptoMarketService
from app.services.crypto_playbook_service import CryptoPlaybookService
from app.services.intelligence_journal_service import IntelligenceJournalService
from app.services.investor_assessment_service import InvestorAssessmentService
from app.services.protocol_fundamentals_service import ProtocolFundamentalsService
from app.services.supply_semantics_service import SupplySemanticsService
from app.services.token_facts_service import TokenFactsService

router = APIRouter(prefix="/crypto", tags=["crypto"])


@router.get("/corpus")
async def get_corpus() -> dict[str, Any]:
    """The assets this platform has read, so a client can offer a switcher.

    Served from `ASSIGNMENTS` rather than from a hand-kept list on the
    client, so an asset added to the corpus appears without a frontend
    change — and one removed disappears rather than 404ing from a menu.
    """

    return {
        "assets": [
            {
                "symbol": assignment.symbol,
                "archetype": assignment.archetype.value,
                "name": assignment.definition.name,
                "established": assignment.is_established,
            }
            for assignment in sorted(ASSIGNMENTS.values(), key=lambda a: a.symbol)
        ]
    }


@router.get("/{symbol}/dossier")
async def get_crypto_dossier(
    symbol: str,
    issuance: IssuanceRuleProvider = Depends(get_issuance_rule_provider),
) -> dict[str, Any]:
    """Everything held about one digital asset, in one read.

    404 for a security this platform does not read as a token, rather
    than an empty dossier: a page of nine absent sections says *we
    looked and found nothing*, and the truth is that nobody looked.
    """

    asset = symbol.upper().strip()

    # **The corpus is the gate, and it is a declaration rather than a
    # guess.** Every service below refuses a security that is not a
    # token — but each refuses on an `AssetClass` the caller supplies,
    # and the only resolver for that runs the brain pipeline this
    # endpoint exists to avoid. Asserting `CRYPTO` to get past them
    # would make every symbol a token, so an equity would be served a
    # dossier of nine empty sections reading *we looked and found
    # nothing*.
    #
    # `ASSIGNMENTS` is the hand-verified list of digital assets this
    # platform has actually read, and it is the same list `/corpus`
    # serves — so the switcher and the gate cannot disagree. An asset
    # in it with no established archetype (TAO) is still read; one
    # outside it was never looked at, and those are opposite claims.
    if asset not in ASSIGNMENTS:
        raise HTTPException(
            status_code=404,
            detail=(
                f"{asset} is not a digital asset this platform reads. No "
                "crypto evidence has been acquired for it, which is a "
                "statement about this platform rather than about the asset."
            ),
        )

    asset_class = AssetClass.CRYPTO

    playbook = CryptoPlaybookService().established(asset, asset_class)

    journal = IntelligenceJournalService()

    return {
        "symbol": asset,
        # ── what am I looking at ──
        "playbook": crypto_playbook_response(playbook),
        "protocol": protocol_fundamentals_response(
            ProtocolFundamentalsService().established(asset, asset_class)
        ),
        # ── what can usefully be said (#117 / #119) ──
        # Serialised by the domain itself: every statement already
        # carries its shape, its licensed meanings with their licensors,
        # and the refusal where no contract established one.
        "assessment": InvestorAssessmentService().for_asset(asset).as_dict(),
        # ── which questions are asked, and what came of each ──
        "quality": asset_quality_response(
            CryptoAssetQualityService().established(asset, asset_class)
        ),
        # ── what each committee concluded, side by side, combined never ──
        "committees": CommitteeMatrixService().for_asset(asset).as_dict(),
        # ── supply, as a vocabulary rather than a number ──
        "supply": supply_response(
            SupplySemanticsService().established(asset, asset_class)
        ),
        "issuance": issuance_response(issuance.rule(asset)),
        # ── the market it trades in, and its peers ──
        "market": crypto_market_response(
            CryptoMarketService().context(asset, asset_class)
        ),
        "facts": asset_profile_response(
            TokenFactsService().established(asset, asset, asset_class)
        ),
        # ── what is happening ──
        "intelligence": intelligence_response(
            CryptoIntelligenceService().snapshot(asset, asset_class)
        ),
        # ── how long this platform has been looking ──
        "journal": journal_response(
            journal.history(asset),
            captures=len(journal.captures(asset)),
        ),
    }
