"""W-09: Nominatim reverse geocode boundaries."""
import pytest

from bot.services import nominatim


@pytest.mark.asyncio
async def test_reverse_geocode_returns_data_for_indonesia(httpx_mock):
    httpx_mock.add_response(
        json={
            "address": {"country_code": "id", "suburb": "Pondok Aren"},
            "display_name": "Pondok Aren, Indonesia",
        }
    )
    result = await nominatim.reverse_geocode(-6.25, 106.75)
    assert result is not None
    assert result["address"]["country_code"] == "id"


@pytest.mark.asyncio
async def test_reverse_geocode_rejects_non_indonesia(httpx_mock):
    httpx_mock.add_response(
        json={
            "address": {"country_code": "sg"},
            "display_name": "Singapore",
        }
    )
    result = await nominatim.reverse_geocode(1.29, 103.85)
    assert result is None


@pytest.mark.asyncio
async def test_reverse_geocode_returns_none_on_http_error(httpx_mock):
    httpx_mock.add_response(status_code=500, is_reusable=True)
    result = await nominatim.reverse_geocode(-6.25, 106.75)
    assert result is None
