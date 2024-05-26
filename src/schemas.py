from pydantic import BaseModel


class LocationCreate(BaseModel):
    state: str
    city: str
    lat: float
    lon: float
