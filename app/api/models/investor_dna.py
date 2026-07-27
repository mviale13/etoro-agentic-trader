from pydantic import BaseModel


class InvestorDNAResponse(BaseModel):
    understanding: int
    message: str
