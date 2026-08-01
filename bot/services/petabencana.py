"""
Client buat API terbuka PetaBencana.id (laporan bencana crowdsource).
Wajib set header User-Agent custom sesuai dokumentasi mereka.
"""
import logging

import httpx

from bot import config
from utils.retry import with_retry

logger = logging.getLogger(__name__)

_TIMEOUT = httpx.Timeout(15.0)


async def fetch_reports(
    geoformat: str = "geojson",
    timeperiod: str = "3h",
    disaster_type: str | None = None,
) -> dict | None:
    """
    Ambil laporan bencana crowdsource dari PetaBencana.id.

    Args:
        geoformat: "geojson" | "topojson" | "cap"
        timeperiod: default "3h" (3 jam terakhir)
        disaster_type: filter opsional — "flood" | "earthquake" | "fire" | "haze" | "wind"

    Return None kalau gagal — caller wajib fallback gracefully.
    """
    params = {"geoformat": geoformat, "timeperiod": timeperiod}
    if disaster_type:
        params["disaster_type"] = disaster_type

    async def _do_fetch() -> dict:
        headers = {"User-Agent": config.PETABENCANA_USER_AGENT}
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            resp = await client.get(
                f"{config.PETABENCANA_BASE_URL}/reports",
                params=params,
                headers=headers,
            )
            resp.raise_for_status()
            return resp.json()

    try:
        return await with_retry(_do_fetch, max_retries=2)
    except Exception:
        logger.exception("Gagal fetch laporan PetaBencana.id")
        return None
