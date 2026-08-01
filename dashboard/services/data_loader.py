"""
Fungsi fetch data buat dashboard, semua dibungkus @st.cache_data(ttl=60)
supaya interaksi filter/widget tidak spam API eksternal berkali-kali.
Lihat PROJECT_SPEC.md bagian 6.1.

NOTE: dashboard jalan sinkron (Streamlit rerun model), jadi di sini pakai
httpx.Client (sync), BEDA dengan bot/services/*.py yang async. Kalau mau
DRY, bisa refactor service jadi sync+async dual API — tapi buat MVP,
duplikasi kecil ini lebih cepat dan lebih gampang di-debug.
"""
import logging

import httpx
import streamlit as st

from bot import config
from bot.services import supabase_client

logger = logging.getLogger(__name__)


@st.cache_data(ttl=60)
def load_recent_quakes() -> list[dict]:
    """Ambil daftar gempa M>5.0 terakhir dari BMKG."""
    try:
        with httpx.Client(timeout=10.0) as client:
            resp = client.get(config.BMKG_QUAKE_RECENT_URL)
            resp.raise_for_status()
            data = resp.json()
            return data.get("Infogempa", {}).get("gempa", [])
    except Exception:
        logger.exception("Gagal load data gempa buat dashboard")
        return []


@st.cache_data(ttl=60)
def load_petabencana_reports(timeperiod: str = "3h") -> dict | None:
    """Ambil laporan bencana crowdsource (GeoJSON) dari PetaBencana.id."""
    try:
        headers = {"User-Agent": config.PETABENCANA_USER_AGENT}
        with httpx.Client(timeout=15.0) as client:
            resp = client.get(
                f"{config.PETABENCANA_BASE_URL}/reports",
                params={"geoformat": "geojson", "timeperiod": timeperiod},
                headers=headers,
            )
            resp.raise_for_status()
            return resp.json()
    except Exception:
        logger.exception("Gagal load laporan PetaBencana buat dashboard")
        return None


@st.cache_data(ttl=60)
def load_mutual_aid_reports(status_filter: str | None = None) -> list[dict]:
    """Ambil laporan gotong royong warga dari Supabase."""
    return supabase_client.get_reports(status=status_filter)
