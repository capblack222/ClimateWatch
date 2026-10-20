import pycountry

# Codes Open-Meteo returns that ISO 3166 does not define, mapped to OWID's own codes.
_OWID_OVERRIDES = {"XK": "OWID_KOS"}  # Kosovo


def to_alpha3(code):
    """Convert an ISO 3166-1 alpha-2 code (what Open-Meteo returns) to the alpha-3 code OWID uses."""
    if not code:
        return None
    code = code.strip().upper()
    if code in _OWID_OVERRIDES:
        return _OWID_OVERRIDES[code]
    if len(code) == 3:
        return code
    country = pycountry.countries.get(alpha_2=code)
    return country.alpha_3 if country else None
