import asyncio
import os

import aiohttp
import pandas as pd
from dotenv import load_dotenv


def load_cities_csv():
    df = pd.read_csv('data/worldcities.csv')
    return df[df['admin_name'] == 'Rio Grande do Sul']


def get_city_coordinates(city_name: str):
    df = load_cities_csv()
    city_row = df[df['city'].str.lower() == city_name.lower()]
    if not city_row.empty:
        return city_row.iloc[0]['lat'], city_row.iloc[0]['lng']
    return None, None


def get_cities_rio_grande_do_sul():
    df = load_cities_csv()
    return [{"city": row['city'], "lat": row['lat'], "lon": row['lng']} for index, row in df.iterrows()]


async def fetch_weather_data(session, lat: float, lon: float):
    load_dotenv()
    api_key = os.getenv("API_KEY")
    url = f"https://my.meteoblue.com/packages/basic-1h_basic-day?apikey={api_key}&lat={lat}&lon={lon}&asl=0&format=json"
    print(f"Fetching weather data from URL: {url}")
    async with session.get(url) as response:
        print(f"Response status: {response.status}")
        if response.status == 200:
            data = await response.json()
            print(f"Weather data for lat={lat}, lon={lon}: {data}")
            return data
        else:
            print(f"Failed to fetch weather data: {response.status}")
            text = await response.text()
            print(f"Response text: {text}")
    return None


async def get_weather_data(lat: float, lon: float):
    async with aiohttp.ClientSession() as session:
        return await fetch_weather_data(session, lat, lon)


def calculate_statistics(weather_data):
    stats = {
        "precipitation": 0,
        "temperature_min": float('inf'),
        "temperature_max": float('-inf'),
        "wind_speed_max": 0,
        "humidity_max": 0
    }

    data_hourly = weather_data.get("data_1h", {})
    for entry in zip(data_hourly['temperature'], data_hourly['precipitation'], data_hourly['windspeed'], data_hourly['relativehumidity']):
        temp, precip, wind_speed, humidity = entry
        
        if temp is not None:
            stats["temperature_min"] = min(stats["temperature_min"], temp)
            stats["temperature_max"] = max(stats["temperature_max"], temp)

        if precip is not None:
            stats["precipitation"] += precip

        if wind_speed is not None:
            stats["wind_speed_max"] = max(stats["wind_speed_max"], wind_speed)

        if humidity is not None:
            stats["humidity_max"] = max(stats["humidity_max"], humidity)

    data_daily = weather_data.get("data_day", {})
    if data_daily:
        daily_temp_min = data_daily.get("temperature_min")
        daily_temp_max = data_daily.get("temperature_max")
        daily_precip = data_daily.get("precipitation")

        if daily_temp_min:
            stats["temperature_min"] = min(stats["temperature_min"], min(daily_temp_min))
        if daily_temp_max:
            stats["temperature_max"] = max(stats["temperature_max"], max(daily_temp_max))
        if daily_precip:
            stats["precipitation"] += sum(daily_precip)

    if stats["temperature_min"] == float('inf'):
        stats["temperature_min"] = None
    if stats["temperature_max"] == float('-inf'):
        stats["temperature_max"] = None

    stats["risk_level"] = assess_risk(stats)

    print(f"Calculated stats: {stats}")
    return stats


def assess_risk(stats):
    reasons = []
    if stats["precipitation"] > 50:
        reasons.append("alta precipitação")
    if stats["wind_speed_max"] > 20:
        reasons.append("alta velocidade do vento")
    if stats["temperature_max"] > 40:
        reasons.append("temperatura máxima alta")
    if stats["temperature_min"] < -5:
        reasons.append("temperatura mínima baixa")
    if stats["humidity_max"] > 90:
        reasons.append("alta umidade")

    if reasons:
        risk_level = "PERIGO"
    else:
        if stats["precipitation"] > 20:
            reasons.append("precipitação moderada")
        if stats["wind_speed_max"] > 10:
            reasons.append("velocidade do vento moderada")
        if stats["temperature_max"] > 35:
            reasons.append("temperatura máxima moderada")
        if stats["temperature_min"] < 0:
            reasons.append("temperatura mínima moderada")
        if stats["humidity_max"] > 70:
            reasons.append("umidade moderada")

        if reasons:
            risk_level = "ATENÇÃO"
        else:
            risk_level = "SEGURO"

    return risk_level, reasons



async def get_statistics_for_all_cities():
    cities = get_cities_rio_grande_do_sul()
    async with aiohttp.ClientSession() as session:
        tasks = []
        for city in cities:
            task = asyncio.create_task(fetch_city_statistics(session, city))
            tasks.append(task)
        return await asyncio.gather(*tasks)


async def fetch_city_statistics(session, city):
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



def filter_cities(cities, criteria):
    filtered = []
    for city in cities:
        stats = city.get("stats", {})
        if all(stats.get(k) is not None and stats.get(k) >= v for k, v in criteria.items()):
            filtered.append(city)
    return filtered
