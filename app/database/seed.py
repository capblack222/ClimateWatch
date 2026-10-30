import io
import logging

import pandas as pd
import requests

from app.database.sample_data import SAMPLE_DATA, SAMPLE_YEAR
from app.repositories import climate_repo

logger = logging.getLogger(__name__)

OWID_CO2_URL = (
    "https://ourworldindata.org/grapher/co-emissions-per-capita.csv"
    "?v=1&csvType=full&useColumnShortNames=true"  # "filtered" returns only the chart's preset countries
)

def _download_owid_rows():
    """Download OWID CO2 per capita and keep the latest year per country."""
    # requests verifies TLS with certifi's CA bundle, so no global SSL patching is needed.
    resp = requests.get(OWID_CO2_URL, headers={"User-Agent": "Our World In Data data fetch/1.0"}, timeout=30)
    resp.raise_for_status()
    df = pd.read_csv(io.StringIO(resp.text))

    # Columns are entity, code, year, plus one value column. OWID has renamed that column before
    # (co2_per_capita -> emissions_total_per_capita), so find it instead of hardcoding the name.
    value_columns = [c for c in df.columns if c not in ("entity", "code", "year")]
    if not {"entity", "code", "year"} <= set(df.columns) or len(value_columns) != 1:
        raise ValueError(f"unexpected OWID CSV columns: {list(df.columns)}")
    value = value_columns[0]

    df = df.dropna(subset=["code", value])  # rows without a code are regions (Africa, World, ...)
    df = df.sort_values("year").groupby("code").last().reset_index()
    return [
        (row["code"], row["entity"], "co2_per_capita", int(row["year"]), float(row[value]), "tonnes", "owid")
        for _, row in df.iterrows()
    ]


def load_owid_csv():
    """Load real OWID data. Retries on every start while only sample data (or nothing) is present.

    Must run inside an app context.
    """
    if climate_repo.count(source="owid") > 0:
        return

    try:
        rows = _download_owid_rows()
    except (requests.RequestException, ValueError, KeyError) as err:
        if climate_repo.count() == 0:
            climate_repo.insert_rows([
                (code, name, "co2_per_capita", SAMPLE_YEAR, value, "tonnes", "sample")
                for code, name, value in SAMPLE_DATA
            ])
        logger.warning("OWID download failed; serving sample data", extra={"error": str(err)})
        return

    climate_repo.replace_samples_with(rows)
    logger.info("Loaded OWID CO2 data", extra={"rows": len(rows)})
