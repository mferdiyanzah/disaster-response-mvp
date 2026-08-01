"""
Client buat API terbuka BMKG (cuaca + gempa).
Rate limit BMKG: 60 request/menit/IP — pakai caching di layer pemanggil
(dashboard: @st.cache_data, bot: api_cache_logs) buat hindari kena limit.
"""
import logging

import httpx

from bot import config
from utils.retry import with_retry

logger = logging.getLogger(__name__)

_TIMEOUT = httpx.Timeout(10.0)


async def fetch_weather(kode_adm4: str) -> dict | None:
    """
    Ambil prakiraan cuaca 3-harian (interval 3 jam) untuk kode wilayah adm4.
    Return None kalau gagal total (sudah exhaust retry) — caller wajib handle
    dengan fallback message ke user, jangan biarkan exception nyampe ke handler.
    """
    async def _do_fetch() -> dict:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            resp = await client.get(
                config.BMKG_WEATHER_URL, params={"adm4": kode_adm4}
            )
            resp.raise_for_status()
            return resp.json()

    try:
        return await with_retry(_do_fetch, max_retries=2)
    except Exception:
        logger.exception("Gagal fetch cuaca BMKG untuk adm4=%s", kode_adm4)
        return None


async def fetch_latest_quake() -> dict | None:
    """Ambil data gempa terakhir (autogempa.json)."""

    async def _do_fetch() -> dict:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            resp = await client.get(config.BMKG_QUAKE_LATEST_URL)
            resp.raise_for_status()
            return resp.json()

    try:
        return await with_retry(_do_fetch, max_retries=2)
    except Exception:
        logger.exception("Gagal fetch gempa terakhir BMKG")
        return None


async def fetch_recent_quakes() -> list[dict] | None:
    """Ambil 15 gempa M>5.0 terakhir (gempaterkini.json)."""

    async def _do_fetch() -> dict:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            resp = await client.get(config.BMKG_QUAKE_RECENT_URL)
            resp.raise_for_status()
            return resp.json()

    try:
        data = await with_retry(_do_fetch, max_retries=2)
        return data.get("Infogempa", {}).get("gempa", [])
    except Exception:
        logger.exception("Gagal fetch daftar gempa terkini BMKG")
        return None


def format_weather_summary(weather_data: dict) -> str:
    """
    Ubah response JSON BMKG jadi teks ringkas buat dikirim ke chat Telegram.
    TODO (Cursor): sesuaikan parsing ini dengan struktur response asli BMKG
    (struktur bisa nested per lokasi/cuaca array — cek response mentah dulu).
    """
    try:
        forecasts = weather_data.get("data", [{}])[0].get("cuaca", [[]])[0]
        if not forecasts:
            return "Data cuaca tidak tersedia untuk wilayah ini."

        lines = ["🌤 *Prakiraan Cuaca*\n"]
        for f in forecasts[:4]:  # 4 slot ke depan (~12 jam)
            lines.append(
                f"• {f.get('local_datetime', '-')}: "
                f"{f.get('weather_desc', '-')}, "
                f"{f.get('t', '-')}°C, "
                f"kelembapan {f.get('hu', '-')}%, "
                f"angin {f.get('ws', '-')} km/jam"
            )
        return "\n".join(lines)
    except Exception:
        logger.exception("Gagal format ringkasan cuaca")
        return "Data cuaca berhasil diambil tapi gagal diformat. Coba lagi nanti."


def format_quake_summary(quake_data: dict) -> str:
    """Format data gempa terakhir jadi teks buat Telegram."""
    try:
        gempa = quake_data.get("Infogempa", {}).get("gempa", {})
        potensi = gempa.get("Potensi", "-")
        lines = [
            "🌍 *Info Gempa Terakhir*\n",
            f"Waktu: {gempa.get('Tanggal', '-')} {gempa.get('Jam', '-')}",
            f"Magnitudo: {gempa.get('Magnitude', '-')}",
            f"Kedalaman: {gempa.get('Kedalaman', '-')}",
            f"Lokasi: {gempa.get('Wilayah', '-')}",
            f"Potensi Tsunami: {potensi}",
        ]
        return "\n".join(lines)
    except Exception:
        logger.exception("Gagal format ringkasan gempa")
        return "Data gempa berhasil diambil tapi gagal diformat. Coba lagi nanti."
