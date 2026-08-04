from pydantic import BaseModel


class ObservationResponse(BaseModel):
    title: str
    message: str
    category: str
