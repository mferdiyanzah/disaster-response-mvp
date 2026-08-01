"""Sidebar filter widgets. State disimpan di st.session_state biar persist antar rerun."""
import streamlit as st


def render_sidebar_filters() -> dict:
    st.sidebar.header("🔍 Filter")

    status = st.sidebar.multiselect(
        "Status Laporan Gotong Royong",
        options=["OPEN", "IN_PROGRESS", "RESOLVED"],
        default=["OPEN", "IN_PROGRESS"],
        key="filter_status",
    )

    report_type = st.sidebar.multiselect(
        "Jenis Laporan",
        options=["NEED_HELP", "OFFER_HELP", "INFO_ONLY"],
        default=["NEED_HELP", "OFFER_HELP"],
        key="filter_report_type",
    )

    timeperiod = st.sidebar.selectbox(
        "Rentang Waktu Laporan Bencana (PetaBencana)",
        options=["1h", "3h", "6h", "24h"],
        index=1,
        key="filter_timeperiod",
    )

    st.sidebar.caption("Data di-cache 60 detik untuk hindari rate-limit API eksternal.")

    return {
        "status": status,
        "report_type": report_type,
        "timeperiod": timeperiod,
    }
