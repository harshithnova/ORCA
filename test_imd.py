from pathlib import Path

from providers.imd.adapter import IMD_KOCHI_URL
from providers.imd.normalize import normalize_kochi_weather


def test_normalize_kochi_weather():
    fixture = Path("tests/fixtures/imd_kochi.html")

    result = normalize_kochi_weather(
        str(fixture),
        "data/normalized/kochi_imd.json",
        IMD_KOCHI_URL,
    )

    assert result["latitude"] == 9.90
    assert result["longitude"] == 76.10
    assert result["weather_condition"] == (
        "Partly cloudy sky with one or two spells of rain or thundershowers"
    )
    assert result["warning_level"] == "Hot Day"
    assert result["source"] == "IMD"
    assert result["data_mode"] == "CACHED_OFFICIAL"
    assert result["data_type"] == "FORECAST"