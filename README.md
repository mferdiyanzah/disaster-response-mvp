# Sistem Informasi Bencana & Gotong Royong (Telegram Bot + Streamlit Dashboard)

MVP hackathon: peringatan dini bencana dan peta gotong royong — Telegram Bot (B2C) + dashboard Streamlit (B2B).

**Dokumen untuk judges:** [PRD.md](PRD.md) (product) · [RFC.md](RFC.md) (engineering, API, deploy)

## Fitur Inti

- **Cek Cuaca Terkini** — GPS atau ketik wilayah; prakiraan BMKG per adm4
- **Info Gempa Terbaru** — data gempa terkini dari BMKG
- **Laporkan Bencana / Minta Bantuan** — laporan warga (butuh/tawarkan bantuan/info), tersimpan ke Supabase dengan kontak Telegram untuk bantuan
- **Dashboard Command Center** — peta Folium: gempa (BMKG), PetaBencana.id, laporan bantuan warga; filter status/tipe/waktu

## Tech Stack

| Layer | Teknologi |
|---|---|
| Bot | `python-telegram-bot` v20+ (async) |
| Dashboard | Streamlit + `streamlit-folium` |
| Database | Supabase (PostgreSQL) |
| Bahasa | Python 3.10+ |
| Deployment | Dev: polling lokal · Prod: VPS + Cloudflare (`deploy/`) atau Render/Streamlit Cloud |

## Setup Cepat

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
# isi TELEGRAM_BOT_TOKEN, SUPABASE_URL, SUPABASE_KEY

# Database: jalankan database/schema.sql di Supabase SQL Editor

python -m bot.main
streamlit run dashboard/app.py
```

## Verifikasi

```powershell
pytest tests/ -v
python -c "from bot import config; config.validate_config(); print('config OK')"
python -c "from bot.main import build_app; build_app(); print('bot app OK')"
```

## Struktur Folder

```
disaster-response-mvp/
├── PRD.md / RFC.md
├── bot/
│   ├── main.py              # dev polling
│   ├── main_production.py   # prod webhook (FastAPI)
│   ├── handlers/            # start, weather, quake, report
│   └── services/            # bmkg, wilayah, nominatim, petabencana, supabase
├── dashboard/
├── database/schema.sql
├── deploy/                  # systemd + run_production.sh (VPS)
├── tests/
└── utils/retry.py
```

## Sumber Data (Open Data)

- **BMKG** — cuaca (`adm4`) + gempa JSON
- **emsifa/api-wilayah-indonesia** — kode wilayah administratif
- **OpenStreetMap Nominatim** — reverse geocode GPS (cuaca)
- **PetaBencana.id** — laporan bencana crowdsource (GeoJSON)

Detail endpoint, rate limit, skema DB: [RFC.md](RFC.md) dan [database/schema.sql](database/schema.sql).

## Production (VPS)

```bash
./deploy/run_production.sh
```

Set `WEBHOOK_URL` di `.env` (Cloudflare tunnel / domain publik). Lihat [RFC.md](RFC.md) § Runtime modes.
