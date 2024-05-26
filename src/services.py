import logging

import requests
from sqlalchemy.orm import Session

import src.models as models
import src.schemas as schemas

logging.basicConfig(level=logging.INFO)


def get_location_by_city_and_state(db: Session, state: str, city: str):
    return db.query(models.Location).filter(models.Location.state == state, models.Location.city == city).first()


def get_weather_by_lat_lon(lat: float, lon: float):
    api_key = "M80eWFhpywNsTYx4"
    url = f"https://my.meteoblue.com/packages/basic-1h_basic-day?apikey={api_key}&lat={lat}&lon={lon}&asl=279&format=json"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        logging.info(f"API Response: {data}")

        try:
            temperature = data['data_1h']['temperature'][0]
            humidity = data['data_1h']['relativehumidity'][0]
            wind_speed = data['data_1h']['windspeed'][0]
            
            return schemas.Weather(
                temperature=temperature,
                humidity=humidity,
                wind_speed=wind_speed
            )
        except KeyError as e:
            logging.error(f"KeyError: {e}")
            return None
    else:
        logging.error(f"Failed to fetch weather data: {response.status_code}")
        return None


def create_subscriber(db: Session, subscriber: schemas.SubscriberCreate):
    db_subscriber = models.Subscriber(email=subscriber.email)
    db.add(db_subscriber)
    db.commit()
    db.refresh(db_subscriber)
    return db_subscriber
