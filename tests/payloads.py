"""Trimmed copies of real API responses."""

FORECAST = {
    "current": {
        "temperature_2m": 7.0, "apparent_temperature": 5.0, "relative_humidity_2m": 91,
        "precipitation": 0.0, "wind_speed_10m": 6.0, "weather_code": 0, "is_day": 1,
    },
    "daily": {
        "time": ["2026-10-19", "2026-10-20"],
        "weather_code": [3, 61],
        "temperature_2m_max": [20.0, 20.0],
        "temperature_2m_min": [7.0, 8.0],
        "precipitation_sum": [0.0, 1.4],
        "wind_speed_10m_max": [10.0, 12.0],
    },
}

GEOCODING = {
    "results": [
        {"name": "Pristina", "country": "Kosovo", "country_code": "XK", "admin1": "Pristina",
         "latitude": 42.67272, "longitude": 21.16688, "population": 161751},
    ]
}

OWID_CSV = """entity,code,year,emissions_total_per_capita
Niger,NER,2023,0.10
Niger,NER,2024,0.11
Nigeria,NGA,2024,0.60
Kosovo,OWID_KOS,2024,4.6
Africa,,2024,1.0
"""
