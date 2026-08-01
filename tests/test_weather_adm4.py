"""W-08: adm4 conversion for BMKG."""
from bot.handlers.weather import _format_adm4_for_bmkg


def test_format_adm4_for_bmkg_village_id():
    assert _format_adm4_for_bmkg("3674060001") == "36.74.06.1001"
