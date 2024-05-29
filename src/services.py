import asyncio
from typing import List, Optional, Tuple

import aiohttp
import pandas as pd
from dotenv import load_dotenv
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from src import models, schemas

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_user(db: Session, user: schemas.UserCreate) -> models.User:
    hashed_password = get_password_hash(user.password)
    db_user = models.User(
        username=user.username,
        email=user.email,
        hashed_password=hashed_password,
        is_collector=user.is_collector,
        is_admin=user.is_admin
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def authenticate_user(db: Session, username: str, password: str) -> Optional[models.User]:
    user = db.query(models.User).filter(models.User.username == username).first()
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user


def create_donation_location(db: Session, location: schemas.DonationLocationCreate, collector_id: int) -> models.DonationLocation:
    db_location = models.DonationLocation(
        name=location.name,
        location=location.location,
        hygiene=location.hygiene,
        food=location.food,
        clothes=location.clothes,
        collector_id=collector_id
    )
    db.add(db_location)
    db.commit()
    db.refresh(db_location)
    return db_location


def update_donation_location(db: Session, location_id: int, location_update: schemas.DonationLocationUpdate, user: models.User):
    location = db.query(models.DonationLocation).filter(models.DonationLocation.id == location_id).first()
    if location is None:
        raise NoResultFound("Location not found")
    if location.collector_id != user.id:
        raise PermissionError("Not authorized to update this location")

    if location_update.name is not None:
        location.name = location_update.name
    if location_update.location is not None:
        location.location = location_update.location
    if location_update.hygiene is not None:
        location.hygiene = location_update.hygiene
    if location_update.food is not None:
        location.food = location_update.food
    if location_update.clothes is not None:
        location.clothes = location_update.clothes

    db.commit()
    db.refresh(location)
    return location


def delete_donation_location(db: Session, location_id: int, user: models.User):
    location = db.query(models.DonationLocation).filter(models.DonationLocation.id == location_id).first()
    if location is None:
        raise NoResultFound("Location not found")
    if location.collector_id != user.id and not user.is_admin:
        raise PermissionError("Not authorized to delete this location")

    db.delete(location)
    db.commit()
    return {"detail": "Location deleted"}


def list_donation_locations(db: Session):
    return db.query(models.DonationLocation).all()


def list_donation_locations_by_state(db: Session, state: str):
    return db.query(models.DonationLocation).filter(models.DonationLocation.location.ilike(f"%{state}%")).all()


def load_cities_csv() -> pd.DataFrame:
    """Carrega o arquivo CSV contendo os dados das cidades do Rio Grande do Sul."""
    df: pd.DataFrame = pd.read_csv('data/worldcities.csv')
    return df[df['admin_name'] == 'Rio Grande do Sul']


def get_city_coordinates(city_name: str) -> Tuple[Optional[float], Optional[float]]:
    """Obtém as coordenadas (latitude e longitude) de uma cidade pelo nome."""
    df: pd.DataFrame = load_cities_csv()
    city_row: pd.Series = df[df['city'].str.lower() == city_name.lower()]
    if not city_row.empty:
        return city_row.iloc[0]['lat'], city_row.iloc[0]['lng']
    return None, None


def get_cities_rio_grande_do_sul() -> List[dict]:
    """Obtém uma lista de dicionários contendo os nomes e coordenadas das cidades do Rio Grande do Sul."""
    df: pd.DataFrame = load_cities_csv()
    return [{"city": row['city'], "lat": row['lat'], "lon": row['lng']} for _, row in df.iterrows()]


async def fetch_weather_data(session: aiohttp.ClientSession, lat: float, lon: float) -> Optional[dict]:
    """Busca dados meteorológicos de uma API com base na latitude e longitude."""
    load_dotenv()
    url: str = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&hourly=temperature_2m,precipitation,windspeed_10m,precipitation_probability,pressure_msl,direct_radiation&daily=temperature_2m_max,temperature_2m_min,precipitation_sum&timezone=America/Sao_Paulo"
    async with session.get(url) as response:
        if response.status == 200:
            data: dict = await response.json()
            return data
    return None


async def get_weather_data(lat: float, lon: float) -> Optional[dict]:
    """Obtém dados meteorológicos com base na latitude e longitude."""
    async with aiohttp.ClientSession() as session:
        return await fetch_weather_data(session, lat, lon)


def calculate_statistics(weather_data: dict) -> dict:
    """Calcula estatísticas com base nos dados meteorológicos."""
    stats = {
        "precipitation_sum": 0,
        "temperature_min": float('inf'),
        "temperature_max": float('-inf'),
        "wind_speed_max": 0,
        "precipitation_probability_avg": 0,
        "pressure_avg": 0,
        "direct_radiation_avg": 0,
    }

    hourly_data = weather_data.get("hourly", {})
    for temp, precip, wind_speed, precipitation_probability, pressure, direct_radiation in zip(hourly_data['temperature_2m'], hourly_data['precipitation'], hourly_data['windspeed_10m'], hourly_data['precipitation_probability'], hourly_data['pressure_msl'], hourly_data['direct_radiation']):
        if temp is not None:
            stats["temperature_min"] = min(stats["temperature_min"], temp)
            stats["temperature_max"] = max(stats["temperature_max"], temp)
        if precip is not None:
            stats["precipitation_sum"] += precip
        if wind_speed is not None:
            stats["wind_speed_max"] = max(stats["wind_speed_max"], wind_speed)
        if precipitation_probability is not None:
            stats["precipitation_probability_avg"] += precipitation_probability
        if pressure is not None:
            stats["pressure_avg"] += pressure
        if direct_radiation is not None:
            stats["direct_radiation_avg"] += direct_radiation

    daily_data = weather_data.get("daily", {})
    if daily_data:
        daily_temp_min = daily_data.get("temperature_2m_min", [])
        daily_temp_max = daily_data.get("temperature_2m_max", [])
        daily_precip = daily_data.get("precipitation_sum", [])

        if daily_temp_min:
            stats["temperature_min"] = min(stats["temperature_min"],
                                           min(daily_temp_min))
        if daily_temp_max:
            stats["temperature_max"] = max(stats["temperature_max"],
                                           max(daily_temp_max))
        if daily_precip:
            stats["precipitation_sum"] += sum(daily_precip)

    if stats["temperature_min"] == float('inf'):
        stats["temperature_min"] = None
    if stats["temperature_max"] == float('-inf'):
        stats["temperature_max"] = None

    if len(hourly_data['precipitation_probability']) > 0:
        stats["precipitation_probability_avg"] = round(
            stats["precipitation_probability_avg"] /
            len(hourly_data['precipitation_probability']), 2
        )
    if len(hourly_data['pressure_msl']) > 0:
        stats["pressure_avg"] = round(
            stats["pressure_avg"] / len(hourly_data['pressure_msl']), 2
        )
    if len(hourly_data['direct_radiation']) > 0:
        stats["direct_radiation_avg"] = round(
            stats["direct_radiation_avg"] / len(hourly_data['direct_radiation']), 2
        )

    stats["risk_level"] = assess_risk(stats)
    return stats


def assess_risk(stats: dict) -> Tuple[str, List[str]]:
    """Avalia o nível de risco com base nas estatísticas meteorológicas."""
    reasons = []
    if stats["precipitation_sum"] >= 50:
        reasons.append("alta precipitação")
    if stats["wind_speed_max"] >= 50:
        reasons.append("alta velocidade do vento")
    if stats["temperature_max"] >= 40:
        reasons.append("temperatura máxima alta")
    if stats["temperature_min"] < -5:
        reasons.append("temperatura mínima baixa")
    if stats["pressure_avg"] <= 900:
        reasons.append("baixa pressão atmosférica")
    if stats["direct_radiation_avg"] >= 500:
        reasons.append("alta radiação solar direta")

    if reasons:
        risk_level = "PERIGO"
    else:
        risk_level = "SEGURO"

    return risk_level, reasons


async def get_statistics_for_all_cities() -> List[dict]:
    """Obtém estatísticas meteorológicas para todas as cidades do Rio Grande do Sul."""
    cities = get_cities_rio_grande_do_sul()
    async with aiohttp.ClientSession() as session:
        tasks = [asyncio.create_task(fetch_city_statistics(session, city)) for city in cities]
        return await asyncio.gather(*tasks)


async def fetch_city_statistics(session: aiohttp.ClientSession, city: dict) -> dict:
    """Obtém as estatísticas meteorológicas de uma cidade."""
    lat, lon = city["lat"], city["lon"]
    weather_data = await fetch_weather_data(session, lat, lon)
    if weather_data:
        stats = calculate_statistics(weather_data)
        risk_level, reasons = assess_risk(stats)
        stats["risk_level"] = risk_level
        stats["reasons"] = reasons
        city["stats"] = stats
    else:
        city["stats"] = {}
    return city


def filter_cities(cities: List[dict], criteria: dict) -> List[dict]:
    """Filtra as cidades com base nos critérios especificados."""
    filtered = []
    for city in cities:
        stats = city.get("stats", {})
        if all(stats.get(k) is not None and stats.get(k) >= v for k, v in criteria.items()):
            filtered.append(city)
    return filtered
