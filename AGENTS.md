# AGENTS.md — Sistem Informasi Bencana & Gotong Royong

## Mission

Hackathon MVP: Telegram Bot (B2C) + Streamlit dashboard (B2B) untuk peringatan dini bencana
dan koordinasi gotong royong.

**Source of truth:** [PRD.md](PRD.md) (requirements) · [RFC.md](RFC.md) (architecture, API, deploy) · [database/schema.sql](database/schema.sql) (DDL)

Untuk workflow phased build, pakai skill `/continue-mvp` (lihat [`.cursor/skills/continue-mvp/SKILL.md`](.cursor/skills/continue-mvp/SKILL.md)).

## Dev Commands (PowerShell)

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env

# Bot (terminal 1, long polling)
python -m bot.main

# Dashboard (terminal 2)
streamlit run dashboard/app.py

# Tests
pytest tests/ -v
```

## Verification (per phase)

**Fase 1 — Setup**
```powershell
python -c "from bot import config; config.validate_config(); print('config OK')"
```

**Fase 2 — Data pipeline**
```powershell
python -c "from bot.services import bmkg, petabencana, wilayah; print('services import OK')"
```

**Fase 3 — Bot**
```powershell
python -c "from bot.main import build_app; build_app(); print('bot app OK')"
pytest tests/ -v
```

**Fase 4 — Dashboard**
```powershell
python -c "from dashboard.services.data_loader import load_recent_quakes; print('dashboard import OK')"
```

**Fase 5 — Deploy prep**
```powershell
python -c "from bot.main import build_app; build_app(); print('webhook-ready check OK')"
# Prod: python -m bot.main_production + WEBHOOK_URL di .env
# VPS: deploy/run_production.sh
```

## Boundaries

**Always do**
- Baca PRD.md + RFC.md sebelum ubah arsitektur atau API contract
- Bot handlers: `async def` + `httpx.AsyncClient` (bukan `requests`)
- External API calls: `try/except` + pesan fallback ke user
- Dashboard fetch: `@st.cache_data(ttl=60)` di `dashboard/services/data_loader.py`
- Secrets lewat `.env` / `bot/config.py` saja
- Jalankan `pytest tests/ -v` sebelum claim selesai

**Ask first**
- Ubah skema DB di luar `database/schema.sql`
- Tambah dependency baru ke `requirements.txt`

**Never do**
- Commit `.env` atau hardcode credentials
- Microservices, migration tooling, atau abstraction layer berlebihan
- NLP klasifikasi urgensi, WhatsApp migration (pasca-hackathon roadmap)
- Buat file contoh/docs baru kecuali diminta user

## Phase Index

| Fase | Fokus | File utama | Done when |
|------|-------|------------|-----------|
| 1 | Setup fondasi | `.env`, `database/schema.sql`, `bot/config.py` | `validate_config()` lulus; schema ter-apply di Supabase |
| 2 | Data pipeline | `bot/services/*.py`, `utils/retry.py` | BMKG, PetaBencana, wilayah, nominatim fetch + fallbacks |
| 3 | Bot front-end | `bot/handlers/*`, `bot/main.py` | Menu, cuaca, gempa, laporan → Supabase; pytest green |
| 4 | Dashboard | `dashboard/*` | Peta multi-layer + filter + cached loaders |
| 5 | Deployment | `bot/main_production.py`, `deploy/` | Webhook + dashboard live; no secrets in repo |

## Starter Prompts

```
/continue-mvp
```

Assess repo state, kerjakan fase pertama yang belum selesai, verify, ringkas sisa kerja.
