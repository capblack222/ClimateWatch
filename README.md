# 🌍 Weather & Climate Planner

A Flask dashboard combining live weather data from Open-Meteo with
country-level climate/health indicators (CO₂, obesity) from Our World in Data.

---

## Prerequisites

| Tool | Version | Install |
|------|---------|---------|
| Python | 3.9+ | https://python.org |
| pip | bundled | — |

No API keys required — Open-Meteo is fully free and key-free.

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
python app.py
```

Open your browser at **http://127.0.0.1:5000**

The SQLite database (`weather_planner.db`) is created automatically on first run.

---

## Loading Real OWID Data (Optional)

1. Download any CSV from https://ourworldindata.org  
   (e.g., "CO₂ per capita" or "Share of adults who are obese")
2. Drop the `.csv` file into the `/data/` folder.
3. Restart the app — it parses columns named `Entity`, `Code`, `Year`, and the metric column automatically.

---

## Features

- **Live weather** — current conditions + 7-day forecast via Open-Meteo (no key needed)
- **City search** — geocoding via Open-Meteo's geocoding endpoint
- **Save favorites** — stored in SQLite, persists across restarts
- **Activity suggestion** — rule-based recommendation from temperature/precip/wind
- **Climate indicators** — CO₂ per capita + obesity prevalence by country
- **Session memory** — Flask session remembers your last city; "Resume" button on home page

---

## Project Structure

```
weather_planner/
├── app.py                  # Flask routes, DB logic, weather/geocoding calls
├── requirements.txt
├── weather_planner.db      # Auto-created SQLite database
├── data/                   # Drop OWID CSVs here
├── templates/
│   └── index.html          # Jinja2 template
└── static/
    ├── css/style.css
    └── js/app.js
```

---

## Extension Ideas (from project spec)

- **Compare two cities**: add a `/compare` route returning JSON for both cities, render side-by-side cards.
- **MongoDB caching**: replace the `weather_cache` SQLite table with PyMongo writes to Atlas.
- **Per-user preferences**: extend Flask sessions to store preferred metric (CO₂ vs. obesity).
