"""
Render peta Folium multi-layer: zona gempa (merah), titik bencana PetaBencana
(biru), dan laporan gotong royong warga (hijau/oranye). Lihat RFC.md § Dashboard.
bagian 6.2.
"""
import folium


def _format_contact_html(report: dict) -> str:
    """Format baris kontak untuk popup peta."""
    report_type = report.get("report_type", "INFO_ONLY")
    if report_type == "INFO_ONLY":
        return ""

    contact_name = report.get("contact_name")
    username = report.get("telegram_username")
    if not contact_name and not username:
        return ""

    if username:
        return (
            f"Kontak: {contact_name or '-'} "
            f"(<a href=\"https://t.me/{username}\" target=\"_blank\">@{username}</a>)<br>"
        )
    return f"Kontak: {contact_name}<br>"


def build_map(
    quakes: list[dict],
    petabencana_geojson: dict | None,
    mutual_aid_reports: list[dict],
    center: tuple[float, float] = (-2.5, 118.0),  # tengah Indonesia
    zoom_start: int = 5,
) -> folium.Map:
    fmap = folium.Map(location=center, zoom_start=zoom_start, tiles="OpenStreetMap")

    # --- Layer 1: Zona gempa (merah) ---
    quake_layer = folium.FeatureGroup(name="🔴 Gempa (M ≥ 5.0)")
    for q in quakes:
        try:
            lat_str, lon_str = q.get("Coordinates", "0,0").split(",")
            lat, lon = float(lat_str), float(lon_str)
            folium.CircleMarker(
                location=(lat, lon),
                radius=8,
                color="red",
                fill=True,
                fill_color="red",
                fill_opacity=0.6,
                popup=folium.Popup(
                    f"<b>M{q.get('Magnitude', '-')}</b><br>"
                    f"{q.get('Wilayah', '-')}<br>"
                    f"{q.get('Tanggal', '-')} {q.get('Jam', '-')}",
                    max_width=250,
                ),
            ).add_to(quake_layer)
        except (ValueError, AttributeError):
            continue
    quake_layer.add_to(fmap)

    # --- Layer 2: Laporan bencana PetaBencana (biru) ---
    if petabencana_geojson and petabencana_geojson.get("features"):
        disaster_layer = folium.FeatureGroup(name="🔵 Laporan Bencana (PetaBencana)")
        folium.GeoJson(
            petabencana_geojson,
            style_function=lambda _: {
                "color": "blue",
                "fillColor": "blue",
                "fillOpacity": 0.5,
            },
        ).add_to(disaster_layer)
        disaster_layer.add_to(fmap)

    # --- Layer 3: Laporan bantuan warga (hijau/oranye) ---
    aid_layer = folium.FeatureGroup(name="🟢 Laporan Bantuan Warga")
    for r in mutual_aid_reports:
        report_type = r.get("report_type", "INFO_ONLY")
        color = {
            "NEED_HELP": "orange",
            "OFFER_HELP": "green",
            "INFO_ONLY": "gray",
        }.get(report_type, "gray")

        lat, lon = r.get("latitude"), r.get("longitude")
        if lat is None or lon is None:
            continue

        folium.Marker(
            location=(lat, lon),
            icon=folium.Icon(color=color, icon="info-sign"),
            popup=folium.Popup(
                f"<b>{report_type}</b><br>"
                f"{r.get('description', '-')}<br>"
                f"Status: {r.get('status', '-')}<br>"
                f"{_format_contact_html(r)}",
                max_width=250,
            ),
        ).add_to(aid_layer)
    aid_layer.add_to(fmap)

    folium.LayerControl(collapsed=False).add_to(fmap)
    return fmap
