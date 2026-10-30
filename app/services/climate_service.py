from app.repositories import climate_repo
from app.utils.country_codes import to_alpha3


def get_country_indicators(country_code, country_name):
    """Latest value per indicator for a country.

    Open-Meteo returns alpha-2 codes ("NE"); OWID stores alpha-3 ("NER"). Match the exact code first,
    then an exact (case-insensitive) country name. Never a partial match, so "Niger" can't return Nigeria.
    """
    rows = []
    alpha3 = to_alpha3(country_code)
    if alpha3:
        rows = climate_repo.find_by_country_code(alpha3)
    if not rows and country_name:
        rows = climate_repo.find_by_country_name(country_name)

    indicators = {}
    for row in rows:  # ordered newest year first, so the first row per indicator wins
        indicators.setdefault(row["indicator_name"], {
            "value": row["value"], "unit": row["unit"] or "", "year": row["year"], "source": row["source"],
        })
    return indicators
