import pytest

from app.services.suggestion_service import activity_suggestion


@pytest.mark.parametrize(
    "temp, precip, wind, expected",
    [
        (15, 6, 0, "Stay indoors today"),               # heavy precipitation wins over everything
        (15, 0, 41, "Indoor activities recommended"),   # strong wind
        (None, 0, 0, "Check conditions before heading out"),
        (-5, 0, 0, "Bundle up for winter walks"),
        (0, 0, 0, "Good for a brisk run"),              # 0 is the lower edge of the 0-10 band
        (10, 0, 0, "Great day for walking or cycling"),
        (25, 0, 0, "Perfect for outdoor activities"),
        (30, 0, 0, "Stay hydrated, limit outdoor exertion"),
    ],
)
def test_activity_suggestion(temp, precip, wind, expected):
    text, _icon, _note = activity_suggestion(temp, precip, wind)
    assert text == expected
