from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy.orm import Session

import src.models as models
import src.schemas as schemas
import src.services as services
from src.config.database import Base, SessionLocal, engine

app = FastAPI()

models.Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/locations/{state}/{city}", response_model=schemas.Location)
def get_location(state: str, city: str, db: Session = Depends(get_db)):
    location = services.get_location_by_city_and_state(db, state, city)
    if location is None:
        raise HTTPException(status_code=404, detail="Location not found")
    return location


@app.get("/weather/{lat}/{lon}", response_model=schemas.Weather)
def get_weather(lat: float, lon: float):
    weather = services.get_weather_by_lat_lon(lat, lon)
    if weather is None:
        raise HTTPException(status_code=404, detail="Weather data not found")
    return weather


@app.post("/subscribe", response_model=schemas.Subscriber)
def subscribe(subscriber: schemas.SubscriberCreate, db: Session = Depends(get_db)):
    return services.create_subscriber(db, subscriber)
