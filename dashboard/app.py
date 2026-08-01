"""
Dashboard Command Center — Streamlit.

Jalankan dari root folder project:
    streamlit run dashboard/app.py
"""
import os
import sys

# Supaya `bot.services.*` bisa di-import meskipun Streamlit dijalankan
# dengan cwd di root project (script dir != root saat streamlit run).
_ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT_DIR not in sys.path:
    sys.path.insert(0, _ROOT_DIR)

import pandas as pd
import streamlit as st
from streamlit_folium import st_folium

from dashboard.components.filters import render_sidebar_filters
from dashboard.components.map_view import build_map
from dashboard.services.data_loader import (
    load_mutual_aid_reports,
    load_petabencana_reports,
    load_recent_quakes,
)
from dashboard.services.report_filter import filter_reports

st.set_page_config(
    page_title="Command Center — Bencana & Bantuan Warga",
    page_icon="🆘",
    layout="wide",
)

st.title("🆘 Command Center — Info Bencana & Bantuan Warga")
st.caption(
    "Dashboard real-time buat relawan/NGO memantau gempa, laporan bencana, "
    "dan permintaan/tawaran bantuan dari warga."
)

filters = render_sidebar_filters()

# --- Load data (cached) ---
with st.spinner("Memuat data terkini..."):
    quakes = load_recent_quakes()
    petabencana_data = load_petabencana_reports(timeperiod=filters["timeperiod"])
    all_reports = load_mutual_aid_reports()

# --- Apply filter di sisi client (data sudah di-cache, filter murah) ---
filtered_reports = filter_reports(
    all_reports, filters["status"], filters["report_type"]
)

# --- Metrics ---
col1, col2, col3 = st.columns(3)
col1.metric("🌍 Gempa M≥5.0 (terkini)", len(quakes))
col2.metric(
    "🔵 Laporan PetaBencana",
    len(petabencana_data.get("features", [])) if petabencana_data else 0,
)
col3.metric("🟢 Laporan Bantuan Warga (filtered)", len(filtered_reports))

# --- Peta ---
st.subheader("Peta Situasi")
fmap = build_map(
    quakes=quakes,
    petabencana_geojson=petabencana_data,
    mutual_aid_reports=filtered_reports,
)
st_folium(fmap, width=None, height=550, returned_objects=[])

# --- Tabel laporan bantuan warga ---
st.subheader("Daftar Laporan Bantuan Warga")
if filtered_reports:
    df = pd.DataFrame(filtered_reports)
    display_cols = [
        c
        for c in [
            "created_at",
            "report_type",
            "status",
            "description",
            "contact_name",
            "telegram_username",
            "reporter_id",
        ]
        if c in df.columns
    ]
    st.dataframe(df[display_cols], use_container_width=True)
else:
    st.info("Belum ada laporan yang cocok dengan filter saat ini.")

st.divider()
st.caption(
    "Sumber data: BMKG (gempa), PetaBencana.id (laporan bencana crowdsource), "
    "Supabase (laporan bantuan warga via Telegram Bot)."
)
