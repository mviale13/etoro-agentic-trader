from pydantic import BaseModel


class CommitteeWeightsResponse(BaseModel):
    regime: str
    weights: dict[str, float]
