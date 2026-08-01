"""M-02–M-06: Folium map layers."""
from dashboard.components.map_view import build_map

QUAKE = {
    "Coordinates": "-6.0,106.0",
    "Magnitude": "5.5",
    "Wilayah": "Test",
    "Tanggal": "01 Agu",
    "Jam": "10:00",
}

GEOJSON = {
    "type": "FeatureCollection",
    "features": [
        {
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [106.0, -6.0]},
            "properties": {},
        }
    ],
}


def test_build_map_includes_quake_layer_name():
    m = build_map([QUAKE], None, [])
    html = m.get_root().render()
    assert "Gempa" in html


def test_build_map_includes_petabencana_layer():
    m = build_map([], GEOJSON, [])
    html = m.get_root().render()
    assert "PetaBencana" in html or "Bencana" in html


def test_build_map_skips_bad_quake_coordinates():
    m = build_map([{"Coordinates": "invalid"}], None, [])
    html = m.get_root().render()
    assert html  # still renders


def test_build_map_need_help_vs_offer_help_colors():
    reports = [
        {
            "report_type": "NEED_HELP",
            "latitude": -6.1,
            "longitude": 106.1,
            "description": "help",
            "status": "OPEN",
        },
        {
            "report_type": "OFFER_HELP",
            "latitude": -6.2,
            "longitude": 106.2,
            "description": "offer",
            "status": "OPEN",
        },
    ]
    m = build_map([], None, reports)
    html = m.get_root().render().lower()
    assert "orange" in html
    assert "green" in html


def test_build_map_skips_reports_without_coordinates():
    m = build_map(
        [],
        None,
        [{"report_type": "NEED_HELP", "latitude": None, "longitude": None}],
    )
    assert m is not None
