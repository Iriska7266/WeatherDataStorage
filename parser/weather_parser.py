import requests
import os
import pandas as pd
import time
from datetime import datetime

RETRIES: int = 10 # Сколько попыток даётся на получение ответа от open-meteo
TIME_TO_WAIT: int = 2 # Сколько нужно ждать между попытками
TIMEOUT: int = 10

METEO_SOURCE_URL: str = "https://api.open-meteo.com/v1/forecast"
RESULTS_FILE_NAME: str = "measures.csv"

def get_string_wind_direction(value: int, lang: str="eng") -> str:
    value = value % 360

    directions = {
        "eng": ["N", "NE", "E", "SE", "S", "SW", "W", "NW"],
        "rus": ["С", "СВ", "В", "ЮВ", "Ю", "ЮЗ", "З", "СЗ"]
    }
    
    # Определяем индекс сектора: каждый сектор по 45°, начиная с N
    # Добавляем 22.5°, чтобы границы секторов были посередине между направлениями
    index = int((value + 22.5) / 45) % 8
    
    return directions.get(lang, directions["eng"])[index]

def print_meteo_data(meteo_data: list[dict]) -> None:
    for i, location_data in enumerate(meteo_data):
        print(f"\n--- City {location_data["city"]} ---")
        print(f"Coordinates: {location_data['latitude']}, {location_data['longitude']}")
        current = location_data['current']
        print(f"Temperature: {current['temperature_2m']}°C")
        print(f"Relational humidity: {current['relative_humidity_2m']}%")
        print(f"Wind speed: {current['wind_speed_10m']} km/h")
        wind_direction = (current["wind_direction_10m"] + 180) % 360
        print(f"Wind direction: {wind_direction}°, {get_string_wind_direction(wind_direction)}")
        print(f"Precipitation: {current["precipitation"]} mm")
        print(f"Surface pressure: {current["surface_pressure"]} hpa")
        print(f"Rain: {current["rain"]} mm")
        print(f"Showfal: {current["snowfall"]} mm")

def save_meteo_data_to_csv(meteo_data: dict) -> None:
    f_name = RESULTS_FILE_NAME
    file_exists = os.path.isfile(f_name)

    wind_direction = (meteo_data["current"]["wind_direction_10m"] + 180) % 360
    df = pd.DataFrame([{
        "date_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "tz_info": meteo_data["timezone_abbreviation"],
        "city": meteo_data["city"],
        "latitude": meteo_data["latitude"],
        "longitude": meteo_data["longitude"],
        "temp_celsius": meteo_data['current']['temperature_2m'],
        "humidity_percent": meteo_data["current"]["relative_humidity_2m"],
        "wind_speed_kmh": meteo_data["current"]["wind_speed_10m"],
        "wind_direction_degree": wind_direction,
        "wind_direction_str": get_string_wind_direction(wind_direction),
        "precipitation_mm": meteo_data["current"]["precipitation"],
        "surface_pressure_hpa": meteo_data["current"]["surface_pressure"],
        "rain_mm": meteo_data["current"]["rain"],
        "snowfall_mm": meteo_data["current"]["snowfall"]
    }])
    df.to_csv(f_name, header=not file_exists, index=False, mode="a")


def main() -> None:
    # Координаты городов можно получить в модуле get_city_coords
    locations = {
        "Chelyabinsk": {"latitude": 55.1543, "longitude": 61.4291},
        "St_Petersburg": {"latitude": 59.93863, "longitude": 30.31413},
        "New_York": {"latitude": 40.71427, "longitude": -74.00597},
        "Moscow": {"latitude": 55.75204, "longitude": 37.61781},
        "Vladivostok": {"latitude": 43.10562, "longitude": 131.87354},
        "Tokyo": {"latitude": 35.6895, "longitude": 139.69171},
        "Brasília": {"latitude": -15.77972, "longitude": -47.92972},
        "Kair": {"latitude": 30.06263, "longitude": 31.24967},
        "Shanghai": {"latitude": 31.22222, "longitude": 121.45806},
        "Canberra": {"latitude": -35.28346, "longitude": 149.12807}
    }

    params = {
        "latitude": [locations[city]["latitude"] for city in locations],
        "longitude": [locations[city]["longitude"] for city in locations],
        "current": ["wind_direction_10m", "precipitation", "wind_speed_10m", "surface_pressure", "temperature_2m", "relative_humidity_2m", "rain", "snowfall"],
        "timezone": "auto"
    }

    for i in range(RETRIES):
        try:
            response = requests.get(METEO_SOURCE_URL, params=params, timeout=TIMEOUT)
            if response.status_code != 200:
                time.sleep(TIME_TO_WAIT)
            else:
                break
        except requests.exceptions.RequestException as e:
            print(f"{datetime.now()}\nRequest error: {e}\nRetry in {TIMEOUT} seconds...\n{"="*60}", flush=True)
        except Exception as e:
            print(f"{datetime.now()}\nError: {e}\nRetry in {TIMEOUT} seconds...\n{"="*60}", flush=True)
        
    else:
        print(f"{datetime.now()}\nHTTP error {response.status_code}: {response.text[:500]}\n{"="*60}", flush=True)
        return

    data = response.json()

    if not isinstance(data, list):
        print(f"{datetime.now()}\nAPI error: {data}\n{"="*60}", flush=True)
        return

    if data and not isinstance(data[0], dict):
        print(f"{datetime.now()}\nUnexpected data format: {type(data[0])} — {repr(data[0])[:200]}\n{"="*60}", flush=True)
        return

    if len(data) != len(locations):
        print(f"{datetime.now()}\nCity count mismatch: got {len(data)}, expected {len(locations)}\n{"="*60}", flush=True)
        return

    # Дозаписываем в каждый json название города
    cities = list(locations.keys())
    for i, chunk in enumerate(data):
        chunk["city"] = cities[i]

    for record in data:
        save_meteo_data_to_csv(record)

if __name__ == "__main__":
    main()
