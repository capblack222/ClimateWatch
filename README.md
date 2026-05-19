# 🌍 Weather & Climate Planner

A modular Flask-based weather and climate dashboard that combines real-time weather forecasting from Open-Meteo with country-level climate indicators from Our World in Data.

The application supports city search, persistent saved locations, 7-day forecasts, climate analytics, and personalized activity recommendations.

---

## Architecture

The project follows a modular Flask application structure using:

- Blueprint-based route separation
- Service layer abstraction
- Utility/helper modules
- SQLite persistence layer
- Application factory pattern

---

## Project Structure

```
weather_planner/
├── run.py                      # App starting point
├── requirements.txt
├── data/
│    └── weather_planner.db      # Auto-created SQLite database
├── app/
│    ├── __init__.py
│    │
│    ├── routes/
│    │   ├── __init__.py
│    │   ├── weather_routes.py
│    │   └── location_routes.py
│    │
│    ├── services/
│    │   ├── __init__.py
│    │   ├── weather_service.py
│    │   ├── geocoding_service.py
│    │   └── suggestion_service.py
│    │
│    ├── utils/
│    │   ├── __init__.py
│    │   └── weather_codes.py
│    │
│    ├── database/
│    │   ├── __init__.py
│    │   ├── db.py
│    │   └── seed.py
├── .gitignore
├── .env
└── Readme.md
```

---

## Tech Stack

- Backend: Flask
- Database: SQLite
- External APIs:
  - Open-Meteo API
  - Open-Meteo Geocoding API
  - Our World in Data CSV datasets
- Data Processing: Pandas
- Frontend: HTML, CSS, JavaScript

---

## Environment Variables

Optional `.env` variables:

```env
SECRET_KEY=your_secret_key
DB_PATH=data/weather_planner.db
```

---

## Prerequisites

| Tool | Version | Install |
|------|---------|---------|
| Python | 3.9+ | https://python.org |
| pip | bundled | — |

No API keys required - Open-Meteo is fully free and key-free.

---

## Setup & Run

```bash
# 1. Clone / unzip the project, then enter the folder
cd weather_planner

# 2. (Recommended) Create a virtual environment
python -m venv venv
source venv/bin/activate        # macOS/Linux
venv\Scripts\activate           # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the app
python run.py
```

Open your browser at **http://127.0.0.1:5000**

The SQLite database (`weather_planner.db`) is created automatically on first run.

---

## Loading Real OWID Data 

Climate indicator data is fetched automatically from Our World in Data's public CSV endpoint during first launch.
No manual dataset download is required.

---

## Features

- **Live weather** — current conditions + 7-day forecast via Open-Meteo (no key needed)
- **City search** — geocoding via Open-Meteo's geocoding endpoint
- **Save favorites** — stored in SQLite, persists across restarts
- **Activity suggestion** — rule-based recommendation from temperature/precip/wind
- **Climate indicators** — CO₂ per capita + obesity prevalence by country
- **Session memory** — Flask session remembers your last city; "Resume" button on home page

---

## Reliability Features

- Automatic fallback sample climate data if OWID fetch fails
- Timeout protection for external API calls
- SQLite auto-initialization on first launch

---

## Future Enhancements

- **Compare two cities**: add a `/compare` route returning JSON for both cities, render side-by-side cards.
- **MongoDB caching**: replace the `weather_cache` SQLite table with PyMongo writes to Atlas.
