"""W-05–W-07, Q-02–Q-04: BMKG formatters and fetch fallbacks."""
import httpx
import pytest

from bot.services import bmkg

SAMPLE_WEATHER = {
    "data": [
        {
            "cuaca": [
                [
                    {
                        "local_datetime": "2026-08-01 12:00",
                        "weather_desc": "Cerah",
                        "t": 28,
                        "hu": 80,
                        "ws": 10,
                    }
                ]
            ]
        }
    ]
}

SAMPLE_QUAKE = {
    "Infogempa": {
        "gempa": {
            "Tanggal": "01 Agu 2026",
            "Jam": "10:00:00 WIB",
            "Magnitude": "5.2",
            "Kedalaman": "10 km",
            "Wilayah": "Pusat laut",
            "Potensi": "Tidak berpotensi tsunami",
        }
    }
}


def test_format_weather_summary_shows_temp_and_wind():
    text = bmkg.format_weather_summary(SAMPLE_WEATHER)
    assert "28" in text
    assert "Cerah" in text
    assert "angin" in text.lower() or "km/jam" in text


def test_format_weather_summary_empty_forecasts():
    text = bmkg.format_weather_summary({"data": [{"cuaca": [[]]}]})
    assert "tidak tersedia" in text.lower()


def test_format_weather_summary_malformed():
    text = bmkg.format_weather_summary({"unexpected": True})
    assert "gagal" in text.lower() or "tidak" in text.lower()


def test_format_quake_summary_shows_magnitude_and_tsunami():
    text = bmkg.format_quake_summary(SAMPLE_QUAKE)
    assert "5.2" in text
    assert "tsunami" in text.lower()
    assert "Pusat laut" in text


def test_format_quake_summary_malformed():
    text = bmkg.format_quake_summary({"Infogempa": {"gempa": None}})
    assert "gagal" in text.lower()


@pytest.mark.asyncio
async def test_fetch_weather_returns_none_on_http_error(httpx_mock):
    httpx_mock.add_response(status_code=500, is_reusable=True)
    result = await bmkg.fetch_weather("36.74.06.1001")
    assert result is None


@pytest.mark.asyncio
async def test_fetch_latest_quake_returns_none_on_failure(httpx_mock):
    httpx_mock.add_response(status_code=503, is_reusable=True)
    result = await bmkg.fetch_latest_quake()
    assert result is None
