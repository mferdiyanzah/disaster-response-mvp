"""Konfigurasi bot — load semua env var di satu tempat."""
import os

from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")

BMKG_WEATHER_URL = os.getenv(
    "BMKG_WEATHER_URL", "https://api.bmkg.go.id/publik/prakiraan-cuaca"
)
BMKG_QUAKE_LATEST_URL = os.getenv(
    "BMKG_QUAKE_LATEST_URL", "https://data.bmkg.go.id/DataMKG/TEWS/autogempa.json"
)
BMKG_QUAKE_RECENT_URL = os.getenv(
    "BMKG_QUAKE_RECENT_URL", "https://data.bmkg.go.id/DataMKG/TEWS/gempaterkini.json"
)

PETABENCANA_BASE_URL = os.getenv("PETABENCANA_BASE_URL", "https://data.petabencana.id")
PETABENCANA_USER_AGENT = os.getenv(
    "PETABENCANA_USER_AGENT", "disaster-response-mvp/1.0"
)

WILAYAH_API_BASE_URL = os.getenv(
    "WILAYAH_API_BASE_URL", "https://emsifa.github.io/api-wilayah-indonesia/api"
)

WEBHOOK_URL = os.getenv("WEBHOOK_URL", "")
PORT = int(os.getenv("PORT", "8000"))


def validate_config() -> None:
    """Panggil ini di startup buat fail-fast kalau env var penting belum diisi."""
    missing = []
    if not TELEGRAM_BOT_TOKEN:
        missing.append("TELEGRAM_BOT_TOKEN")
    if not SUPABASE_URL:
        missing.append("SUPABASE_URL")
    if not SUPABASE_KEY:
        missing.append("SUPABASE_KEY")

    if missing:
        raise RuntimeError(
            f"Env var wajib belum diisi: {', '.join(missing)}. "
            "Cek file .env kamu (copy dari .env.example)."
        )
