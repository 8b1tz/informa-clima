from pydantic import BaseModel


class LocationBase(BaseModel):
    state: str
    city: str


class LocationCreate(LocationBase):
    lat: float
    lon: float


class Location(LocationBase):
    id: int
    lat: float
    lon: float

    class Config:
        orm_mode = True


class Weather(BaseModel):
    temperature: float
    humidity: float
    wind_speed: float


class SubscriberBase(BaseModel):
    email: str


class SubscriberCreate(SubscriberBase):
    pass


class Subscriber(SubscriberBase):
    id: int

    class Config:
        orm_mode = True
