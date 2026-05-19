def activity_suggestion(temp, precip, wind):
    """Simple rule-based activity suggestion."""
    if precip and precip > 5:
        return ("Stay indoors today", "🏠", "heavy precipitation expected")
    if wind and wind > 40:
        return ("Indoor activities recommended", "💨", "strong winds today")
    if temp is None:
        return ("Check conditions before heading out", "🤔", "")
    if temp < 0:
        return ("Bundle up for winter walks", "🧥", "below freezing")
    if 0 <= temp < 10:
        return ("Good for a brisk run", "🏃", "cool and crisp")
    if 10 <= temp < 20:
        return ("Great day for walking or cycling", "🚴", "comfortable conditions")
    if 20 <= temp < 30:
        return ("Perfect for outdoor activities", "🌳", "ideal weather")
    return ("Stay hydrated, limit outdoor exertion", "💧", "hot conditions")