import requests

def get_coordinates(city_name):
    """Получает широту и долготу по названию города."""
    geo_url = "https://geocoding-api.open-meteo.com/v1/search"
    params = {
        "name": city_name,
        "count": 1,  # Берем только первый, самый релевантный результат
        "language": "ru",
        "format": "json"
    }
    response = requests.get(geo_url, params=params)
    data = response.json()
    
    if "results" in data:
        result = data["results"][0]
        return result["latitude"], result["longitude"]
    else:
        raise ValueError(f"Город '{city_name}' не найден")

city_name = input("Введите название города: ")

try:
    city_lat, city_lon = get_coordinates(city_name)
except ValueError as e:
    print(str(e))

print(f"{city_name}: {city_lat}, {city_lon}")
