import pytest

from app.utils.country_codes import to_alpha3
from app.utils.weather_codes import wmo_description


@pytest.mark.parametrize(
    "code, expected",
    [("NE", "NER"), ("NG", "NGA"), ("in", "IND"), (" us ", "USA"), ("XK", "OWID_KOS"), ("NER", "NER"),
     ("ZZ", None), ("", None), (None, None)],
)
def test_to_alpha3(code, expected):
    assert to_alpha3(code) == expected


def test_wmo_description_known_and_unknown():
    assert wmo_description(0)[0] == "Clear Sky"
    assert wmo_description(12345)[0] == "Unknown"


def test_json_log_line_includes_extra_fields_and_exceptions():
    import json
    import logging

    from app.logging_config import JsonFormatter

    try:
        raise ValueError("boom")
    except ValueError:
        import sys
        record = logging.LogRecord("app.test", logging.ERROR, __file__, 1, "failed %s", ("x",), sys.exc_info())
    record.city = "Pune"
    line = json.loads(JsonFormatter().format(record))
    assert line["message"] == "failed x"
    assert line["city"] == "Pune"
    assert "ValueError: boom" in line["exception"]
