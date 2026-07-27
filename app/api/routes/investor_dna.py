from fastapi import APIRouter

from app.api.models.investor_dna import InvestorDNAResponse
from app.services.investor_dna_service import InvestorDNAService

router = APIRouter(prefix="/investor-dna", tags=["investor-dna"])


@router.get("/", response_model=InvestorDNAResponse)
def get_investor_dna() -> InvestorDNAResponse:
    dna = InvestorDNAService().analyze([])

    understanding = dna.confidence

    if understanding < 25:
        message = "I'm just getting to know your investment style."
    elif understanding < 50:
        message = "I'm starting to recognize patterns in your decisions."
    elif understanding < 75:
        message = "I can personalize many recommendations."
    else:
        message = "I understand your long-term investment philosophy well."

    return InvestorDNAResponse(
        understanding=understanding,
        message=message,
    )
