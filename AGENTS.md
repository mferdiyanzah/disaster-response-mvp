# AGENTS.md — Sistem Informasi Bencana & Gotong Royong

## Mission

Hackathon MVP: Telegram Bot (B2C) + Streamlit dashboard (B2B) untuk peringatan dini bencana
dan koordinasi gotong royong. **Source of truth teknis:** [`PROJECT_SPEC.md`](PROJECT_SPEC.md).
Untuk workflow phased build, pakai skill `/continue-mvp` (lihat [`.cursor/skills/continue-mvp/SKILL.md`](.cursor/skills/continue-mvp/SKILL.md)).

## Dev Commands (PowerShell)

```powershell
# Virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1

# Dependencies
pip install -r requirements.txt

# Env (jangan commit .env)
Copy-Item .env.example .env
# Isi TELEGRAM_BOT_TOKEN, SUPABASE_URL, SUPABASE_KEY

# Database: jalankan database/schema.sql di Supabase SQL Editor

# Bot (terminal 1, long polling)
python -m bot.main

# Dashboard (terminal 2)
streamlit run dashboard/app.py
```

## Verification (per phase)

Jalankan setelah selesai satu fase. Gagal = fase belum done.

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
```

**Fase 4 — Dashboard**
```powershell
python -c "from dashboard.services.data_loader import load_recent_quakes; print('dashboard import OK')"
```

**Fase 5 — Deploy prep**
```powershell
python -c "from bot.main import build_app; build_app(); print('webhook-ready check OK')"
# Pastikan tidak ada secret di kode; WEBHOOK_URL hanya di .env
```

## Boundaries

**Always do**
- Baca `PROJECT_SPEC.md` sebelum ubah arsitektur atau API contract
- Bot handlers: `async def` + `httpx.AsyncClient` (bukan `requests`)
- External API calls: `try/except` + pesan fallback ke user
- Dashboard fetch: `@st.cache_data(ttl=60)` di `dashboard/services/data_loader.py`
- Secrets lewat `.env` / `bot/config.py` saja

**Ask first**
- Ubah skema DB di luar `database/schema.sql`
- Tambah dependency baru ke `requirements.txt`
- Pindah dari long polling ke webhook di production

**Never do**
- Commit `.env` atau hardcode credentials
- Microservices, migration tooling, atau abstraction layer berlebihan
- NLP klasifikasi urgensi, WhatsApp migration (pasca-hackathon roadmap)
- Buat file contoh/docs baru kecuali diminta user

## Phase Index (PROJECT_SPEC §8)

| Fase | Fokus | File utama | Done when |
|------|-------|------------|-----------|
| 1 | Setup fondasi | `.env`, `database/schema.sql`, `bot/config.py` | `validate_config()` lulus; schema ter-apply di Supabase |
| 2 | Data pipeline | `bot/services/*.py`, `utils/retry.py` | BMKG, PetaBencana, wilayah fetch + try/except + fallbacks |
| 3 | Bot front-end | `bot/handlers/*`, `bot/main.py` | Menu, cuaca, gempa, ConversationHandler laporan → Supabase |
| 4 | Dashboard | `dashboard/*` | Peta multi-layer Folium + filter + cached loaders |
| 5 | Deployment | `bot/main.py` webhook | Webhook path siap Render; tidak ada secret di repo |

## Starter Prompts

**Auto — lanjut fase berikutnya**
```
/continue-mvp
```
Assess repo state, kerjakan fase pertama yang belum selesai, verify, ringkas sisa kerja.

**Fase 1**
```
/continue-mvp fase 1 — pastikan .env.example lengkap, validate_config jalan, dan schema.sql siap di Supabase
```

**Fase 2**
```
/continue-mvp fase 2 — harden bot/services (BMKG, PetaBencana, wilayah) dengan try/except dan fallback
```

**Fase 3**
```
/continue-mvp fase 3 — selesaikan bot handlers; laporan gotong royong tersimpan ke Supabase
```

**Fase 4**
```
/continue-mvp fase 4 — dashboard peta multi-layer + filter status, semua fetch pakai cache ttl=60
```

**Fase 5**
```
/continue-mvp fase 5 — siapkan webhook production di bot/main.py tanpa commit secret
```

**Resume setelah pause**
```
lanjut — /continue-mvp dari fase terakhir yang belum done
```
