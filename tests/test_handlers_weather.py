"""W-01, W-10, W-11: weather handler GPS/text entry and district shortcut."""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from bot.handlers.weather import (
    AWAITING_WEATHER_INPUT,
    handle_location_text,
    handle_weather_location,
    weather_callback,
)
from tests.conftest import make_callback_update, make_message_update

SAMPLE_WEATHER = {
    "data": [
        {
            "cuaca": [
                [
                    {
                        "local_datetime": "2026-08-01 12:00",
                        "weather_desc": "Cerah",
                        "t": 28,
                        "hu": 80,
                        "ws": 10,
                    }
                ]
            ]
        }
    ]
}


@pytest.mark.asyncio
async def test_weather_callback_shows_gps_and_text_options(mock_user):
    """W-01: entry shows GPS and text input buttons."""
    update, query = make_callback_update("cmd_weather", mock_user)
    ctx = MagicMock()
    ctx.user_data = {}

    await weather_callback(update, ctx)

    assert ctx.user_data["state"] == AWAITING_WEATHER_INPUT
    args = query.edit_message_text.await_args
    assert "Pilih cara cek cuaca" in args[0][0]
    markup = args[1]["reply_markup"]
    callbacks = [b.callback_data for row in markup.inline_keyboard for b in row]
    assert "cmd_weather_gps" in callbacks
    assert "cmd_weather_text" in callbacks


@pytest.mark.asyncio
async def test_handle_location_text_district_shortcut(mock_user):
    """W-10: kecamatan match skips drill-down and fetches weather."""
    update, message = make_message_update("Pondok Aren", user=mock_user)
    ctx = MagicMock()
    ctx.user_data = {"state": AWAITING_WEATHER_INPUT}

    district = {"id": "36.74.06", "name": "pondok aren"}

    with patch(
        "bot.handlers.weather.wilayah.smart_search",
        new_callable=AsyncMock,
        return_value=("district", district),
    ):
        with patch(
            "bot.handlers.weather.wilayah.resolve_adm4_for_bmkg",
            new_callable=AsyncMock,
            return_value="36.74.06.1001",
        ):
            with patch(
                "bot.handlers.weather.bmkg.fetch_weather",
                new_callable=AsyncMock,
                return_value=SAMPLE_WEATHER,
            ):
                await handle_location_text(update, ctx)

    assert ctx.user_data["state"] is None
    message.reply_text.assert_awaited()
    last_call = message.reply_text.await_args_list[-1]
    assert "28" in last_call[0][0]


@pytest.mark.asyncio
async def test_handle_weather_location_nominatim_fail_reprompts(mock_user):
    """W-11: GPS + Nominatim failure keeps flow open and asks for text."""
    loc = MagicMock()
    loc.latitude = -6.25
    loc.longitude = 106.75
    update, message = make_message_update(location=loc, user=mock_user)
    ctx = MagicMock()
    ctx.user_data = {"state": AWAITING_WEATHER_INPUT}

    with patch(
        "bot.handlers.weather.nominatim.reverse_geocode",
        new_callable=AsyncMock,
        return_value=None,
    ):
        await handle_weather_location(update, ctx)

    assert ctx.user_data["state"] == AWAITING_WEATHER_INPUT
    last_call = message.reply_text.await_args_list[-1]
    assert "ketik" in last_call[0][0].lower()
