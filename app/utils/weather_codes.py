def wmo_description(code):
    """Map WMO weather code to human-readable description."""
    mapping = {
        0: ("Clear Sky", "☀️"), 1: ("Mostly Clear", "🌤️"), 2: ("Partly Cloudy", "⛅"),
        3: ("Overcast", "☁️"), 45: ("Foggy", "🌫️"), 48: ("Icy Fog", "🌫️"),
        51: ("Light Drizzle", "🌦️"), 53: ("Drizzle", "🌦️"), 55: ("Heavy Drizzle", "🌧️"),
        61: ("Light Rain", "🌧️"), 63: ("Rain", "🌧️"), 65: ("Heavy Rain", "🌧️"),
        71: ("Light Snow", "🌨️"), 73: ("Snow", "❄️"), 75: ("Heavy Snow", "❄️"),
        80: ("Rain Showers", "🌦️"), 81: ("Heavy Showers", "⛈️"), 82: ("Violent Showers", "⛈️"),
        95: ("Thunderstorm", "⛈️"), 96: ("Hail Storm", "⛈️"), 99: ("Heavy Hail", "⛈️"),
    }
    return mapping.get(code, ("Unknown", "🌡️"))