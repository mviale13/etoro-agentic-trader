from pydantic import BaseModel


class ReflectionResponse(BaseModel):
    title: str
    message: str
    source: str
