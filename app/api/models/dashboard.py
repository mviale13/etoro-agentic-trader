from pydantic import BaseModel

from app.api.models.investor_dna import InvestorDNAResponse
from app.api.models.observation import ObservationResponse
from app.api.models.portfolio import PortfolioResponse
from app.api.models.reflection import ReflectionResponse
from app.api.models.today import TodayResponse


class DashboardResponse(BaseModel):
    today: TodayResponse
    portfolio: PortfolioResponse | None
    observation: ObservationResponse | None
    reflection: ReflectionResponse | None
    investor_dna: InvestorDNAResponse | None
