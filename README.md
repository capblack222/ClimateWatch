# 🌍 ClimateWatch

A modular Flask-based weather and climate dashboard that combines real-time weather forecasting from Open-Meteo with country-level climate indicators from Our World in Data.

The application supports city search, persistent saved locations, 7-day forecasts, climate analytics, and personalized activity recommendations.

The project is being extended into an event-driven data pipeline on AWS that collects hourly weather observations, stores them as a queryable history, and sends alerts when conditions cross thresholds.

---

## Architecture

The project follows a modular Flask application structure using:

- Blueprint-based route separation
- Service layer abstraction
- Utility/helper modules
- SQLite persistence layer
- Application factory pattern

---

## Planned Cloud Architecture

- EventBridge Scheduler triggers hourly ingestion for every tracked city
- SQS queue with a dead-letter queue for retries and failure isolation
- Lambda functions for fan-out, ingestion, nightly rollups and OWID refresh
- Amazon Data Firehose to batch records and convert them to Parquet
- S3 raw and curated layers, queried with Glue Data Catalog and Athena
- DynamoDB for saved locations, latest readings and daily summaries
- EventBridge + SNS for threshold alerts (heat, heavy rain, high wind)
- CloudWatch dashboards and alarms, infrastructure defined with AWS CDK (Python)

---

## Project Structure

```
ClimateWatch/
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
├── LICENSE
└── README.md
```

---

## Tech Stack

- Backend: Flask
- Database: SQLite (moving to DynamoDB)
- External APIs:
  - Open-Meteo API
  - Open-Meteo Geocoding API
  - Our World in Data CSV datasets
- Data Processing: Pandas
- Frontend: HTML, CSS, JavaScript
- Cloud (planned): AWS Lambda, SQS, EventBridge, Data Firehose, S3, Athena, DynamoDB, SNS, CloudWatch
- Infrastructure as Code (planned): AWS CDK (Python)

---

## Environment Variables

Optional `.env` variables:

```env
FLASK_SECRET_KEY=your_secret_key
DB_PATH=data/weather_planner.db
FLASK_DEBUG=1                   # local development only
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
# 1. Clone the project, then enter the folder
git clone https://github.com/capblack222/ClimateWatch.git
cd ClimateWatch

# 2. (Recommended) Create a virtual environment
python -m venv venv
source venv/bin/activate        # macOS/Linux
venv\Scripts\activate           # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Create the data folder for the SQLite database
mkdir data

# 5. Run the app
python run.py
```

Open your browser at **http://127.0.0.1:5000**

The SQLite database (`weather_planner.db`) is created automatically inside `data/` on first run.

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
- **Climate indicators** — CO₂ per capita by country
- **Session memory** — Flask session remembers your last city; "Resume" button on home page

---

## Reliability Features

- Automatic fallback sample climate data if OWID fetch fails
- Timeout protection for external API calls
- SQLite auto-initialization on first launch

---

## Future Enhancements

- **Hourly ingestion**: scheduled pulls for tracked cities through SQS and Lambda, with retries and a dead-letter queue.
- **Climate history**: Parquet data in S3 queried with Athena for temperature and rainfall trends per city.
- **Weather alerts**: email notifications when a city crosses heat, rain or wind thresholds.
- **Full OWID time series**: store every year of climate indicators instead of only the latest.
- **Compare two cities**: add a `/compare` route returning JSON for both cities, render side-by-side cards.
- **Testing and CI**: unit and route tests with pytest, run automatically on every push.

---

## Data Attribution

- Weather data by [Open-Meteo](https://open-meteo.com/) (CC BY 4.0)
- Climate data from [Our World in Data](https://ourworldindata.org/) (CC BY 4.0)
