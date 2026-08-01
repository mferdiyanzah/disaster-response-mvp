"""
Wrapper koneksi Supabase, dipakai bareng oleh bot dan dashboard.
Pakai satu client singleton biar tidak re-init koneksi tiap request.
"""
import logging

from supabase import Client, create_client

from bot import config

logger = logging.getLogger(__name__)

_client: Client | None = None


def get_client() -> Client:
    global _client
    if _client is None:
        _client = create_client(config.SUPABASE_URL, config.SUPABASE_KEY)
    return _client


def upsert_user(telegram_id: int, kode_adm4: str | None = None) -> dict | None:
    """Daftarkan user baru atau update kode_adm4 kalau sudah ada."""
    try:
        client = get_client()
        payload = {"telegram_id": telegram_id}
        if kode_adm4:
            payload["kode_adm4"] = kode_adm4
        result = (
            client.table("users")
            .upsert(payload, on_conflict="telegram_id")
            .execute()
        )
        return result.data[0] if result.data else None
    except Exception:
        logger.exception("Gagal upsert user telegram_id=%s", telegram_id)
        return None


def insert_mutual_aid_report(
    reporter_id: int,
    report_type: str,
    description: str,
    latitude: float,
    longitude: float,
    contact_name: str | None = None,
    telegram_username: str | None = None,
) -> dict | None:
    """Simpan laporan gotong royong (butuh bantuan / tawarkan bantuan)."""
    try:
        client = get_client()
        payload = {
            "reporter_id": reporter_id,
            "report_type": report_type,
            "description": description,
            "latitude": latitude,
            "longitude": longitude,
            "status": "OPEN",
        }
        if contact_name is not None:
            payload["contact_name"] = contact_name
        if telegram_username is not None:
            payload["telegram_username"] = telegram_username
        result = (
            client.table("mutual_aid_reports")
            .insert(payload)
            .execute()
        )
        return result.data[0] if result.data else None
    except Exception:
        logger.exception("Gagal insert laporan dari reporter_id=%s", reporter_id)
        return None


def get_reports(status: str | None = None) -> list[dict]:
    """Ambil semua laporan, opsional filter by status. Dipakai dashboard."""
    try:
        client = get_client()
        query = client.table("mutual_aid_reports").select("*")
        if status:
            query = query.eq("status", status)
        result = query.order("created_at", desc=True).execute()
        return result.data or []
    except Exception:
        logger.exception("Gagal fetch laporan dari Supabase")
        return []
