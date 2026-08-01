"""Q-01, Q-03: earthquake handler."""
from unittest.mock import AsyncMock, patch

import pytest

from bot.handlers.quake import quake_callback
from tests.conftest import make_callback_update


@pytest.mark.asyncio
async def test_quake_callback_shows_summary_when_data_ok(mock_user):
    quake_data = {
        "Infogempa": {
            "gempa": {
                "Tanggal": "01 Agu",
                "Jam": "10:00",
                "Magnitude": "5.0",
                "Kedalaman": "10 km",
                "Wilayah": "Laut",
                "Potensi": "Tidak berpotensi tsunami",
            }
        }
    }
    update, query = make_callback_update("cmd_quake", mock_user)

    with patch("bot.handlers.quake.bmkg.fetch_latest_quake", new_callable=AsyncMock) as fetch:
        fetch.return_value = quake_data
        await quake_callback(update, None)

    query.edit_message_text.assert_awaited()
    args = query.edit_message_text.await_args
    assert "5.0" in args[0][0]
    assert "tsunami" in args[0][0].lower()


@pytest.mark.asyncio
async def test_quake_callback_fallback_when_api_down(mock_user):
    update, query = make_callback_update("cmd_quake", mock_user)

    with patch("bot.handlers.quake.bmkg.fetch_latest_quake", new_callable=AsyncMock) as fetch:
        fetch.return_value = None
        await quake_callback(update, None)

    args = query.edit_message_text.await_args[0][0]
    assert "tidak bisa diakses" in args.lower() or "bmkg" in args.lower()
