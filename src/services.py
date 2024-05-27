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
    url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&hourly=temperature_2m,precipitation,windspeed_10m,precipitation_probability,pressure_msl,direct_radiation&daily=temperature_2m_max,temperature_2m_min,precipitation_sum&timezone=America/Sao_Paulo"
    print(f"Fetching weather data from URL: {url}")
    async with session.get(url) as response:
        print(f"Response status: {response.status}")
        if response.status == 200:
            data = await response.json()
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
            stats["temperature_min"] = min(stats["temperature_min"], min(daily_temp_min))
        if daily_temp_max:
            stats["temperature_max"] = max(stats["temperature_max"], max(daily_temp_max))
        if daily_precip:
            stats["precipitation_sum"] += sum(daily_precip)

    if stats["temperature_min"] == float('inf'):
        stats["temperature_min"] = None
    if stats["temperature_max"] == float('-inf'):
        stats["temperature_max"] = None

    if len(hourly_data['precipitation_probability']) > 0:
        stats["precipitation_probability_avg"] /= len(hourly_data['precipitation_probability'])
    if len(hourly_data['pressure_msl']) > 0:
        stats["pressure_avg"] /= len(hourly_data['pressure_msl'])
    if len(hourly_data['direct_radiation']) > 0:
        stats["direct_radiation_avg"] /= len(hourly_data['direct_radiation'])

    stats["risk_level"] = assess_risk(stats)

    print(f"Calculated stats: {stats}")
    return stats


def assess_risk(stats):
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


async def main():
    cities_stats = await get_statistics_for_all_cities()
    print(cities_stats)


if __name__ == "__main__":
    asyncio.run(main())
