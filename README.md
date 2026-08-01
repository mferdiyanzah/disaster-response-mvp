# Sistem Informasi Bencana & Gotong Royong (Telegram Bot + Streamlit Dashboard)

MVP untuk hackathon (target 4-5 jam pengerjaan): platform peringatan dini bencana
dan peta gotong royong, dengan Telegram Bot sebagai antarmuka warga (B2C) dan
dashboard Streamlit sebagai command center relawan/NGO (B2B).

> Baca `PROJECT_SPEC.md` untuk spesifikasi teknis lengkap (skema DB, kontrak API,
> flow bot, dsb). File itu juga jadi referensi utama buat Cursor AI kalau kamu
> minta bantuan lanjutin coding — sudah dirujuk di `.cursorrules`.

## Fitur Inti

- **Cek Cuaca Terkini** — prakiraan cuaca BMKG per wilayah (adm4)
- **Info Gempa Terbaru** — data gempa terkini dari BMKG
- **Laporkan Bencana / Minta Bantuan** — crowdsource laporan warga (butuh bantuan / tawarkan bantuan), tersimpan ke Supabase
- **Dashboard Command Center** — peta interaktif (Folium) yang overlay: zona gempa (BMKG), area terdampak (PetaBencana.id), dan laporan gotong royong warga (Supabase)

## Tech Stack

| Layer | Teknologi |
|---|---|
| Bot | `python-telegram-bot` v20+ (async) |
| Dashboard | Streamlit + `streamlit-folium` |
| Database | Supabase (PostgreSQL) |
| Bahasa | Python 3.10+ |
| Deployment | Render.com (bot) + Streamlit Community Cloud (dashboard) |

## Setup Cepat

```powershell
# 1. Clone / buka folder ini di Cursor

# 2. Buat virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1

# 3. Install dependencies
pip install -r requirements.txt

# 4. Copy env template dan isi credentials
Copy-Item .env.example .env
# isi TELEGRAM_BOT_TOKEN, SUPABASE_URL, SUPABASE_KEY

# 5. Setup database
# Buka Supabase SQL Editor, jalankan isi database/schema.sql

# 6. Jalankan bot (mode polling, buat development)
python -m bot.main

# 7. Jalankan dashboard (di terminal terpisah)
streamlit run dashboard/app.py
```

## Struktur Folder

```
disaster-response-mvp/
├── PROJECT_SPEC.md          # spesifikasi teknis lengkap
├── .cursorrules             # konteks project buat Cursor AI
├── .env.example
├── requirements.txt
├── bot/
│   ├── main.py               # entrypoint bot (polling/webhook)
│   ├── config.py              # load env vars
│   ├── handlers/
│   │   ├── start.py           # /start + menu utama
│   │   ├── weather.py         # flow cek cuaca
│   │   ├── quake.py           # flow info gempa
│   │   └── report.py          # ConversationHandler lapor bencana
│   └── services/
│       ├── bmkg.py            # client API BMKG
│       ├── wilayah.py         # lookup kode wilayah adm4
│       ├── petabencana.py     # client API PetaBencana.id
│       └── supabase_client.py # koneksi Supabase
├── dashboard/
│   ├── app.py                 # entrypoint Streamlit
│   ├── components/
│   │   ├── map_view.py        # render peta Folium multi-layer
│   │   └── filters.py         # sidebar filter widgets
│   └── services/
│       └── data_loader.py     # fetch data + @st.cache_data
├── database/
│   └── schema.sql             # DDL Supabase (3 tabel + RLS)
└── utils/
    └── retry.py               # exponential backoff w/ jitter buat rate limit
```

## Sumber Data (Open Data)

- **BMKG**: `https://api.bmkg.go.id/publik/prakiraan-cuaca?adm4={kode}` (cuaca), `https://data.bmkg.go.id/DataMKG/TEWS/autogempa.json` (gempa terakhir)
- **Wilayah Indonesia**: `emsifa/api-wilayah-indonesia` (GitHub Pages, statis) — buat mapping nama wilayah ke kode adm4
- **PetaBencana.id**: `https://data.petabencana.id/reports` — laporan bencana crowdsource (GeoJSON)

Detail lengkap tiap endpoint (field JSON, rate limit, dsb) ada di `PROJECT_SPEC.md`.

## Roadmap Pasca-Hackathon

- Migrasi Telegram → WhatsApp Cloud API (jangkauan lebih luas di Indonesia, tapi ada approval template & tier limit)
- Tambah NLP/LLM buat klasifikasi urgensi laporan warga otomatis dari teks bebas
