"""Reverse geocoding via OpenStreetMap Nominatim (gratis, tanpa API key)."""
import logging

import httpx

logger = logging.getLogger(__name__)

_NOMINATIM_URL = "https://nominatim.openstreetmap.org/reverse"
_USER_AGENT = "disaster-response-mvp/1.0 (hackathon-edu)"
_TIMEOUT = httpx.Timeout(10.0)


async def reverse_geocode(lat: float, lon: float) -> dict | None:
    """Return Nominatim JSON atau None kalau gagal / di luar Indonesia."""
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            resp = await client.get(
                _NOMINATIM_URL,
                params={
                    "lat": lat,
                    "lon": lon,
                    "format": "json",
                    "addressdetails": 1,
                    "accept-language": "id",
                },
                headers={"User-Agent": _USER_AGENT},
            )
            resp.raise_for_status()
            data = resp.json()
            country = data.get("address", {}).get("country_code", "").lower()
            if country != "id":
                logger.warning("Lokasi di luar Indonesia: %s", country)
                return None
            return data
    except Exception:
        logger.exception("Nominatim gagal untuk %s,%s", lat, lon)
        return None
