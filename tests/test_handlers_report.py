"""R-01–R-07: report ConversationHandler flow."""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from telegram.ext import ConversationHandler

from bot.handlers.report import (
    CHOOSING_TYPE,
    SHARING_LOCATION,
    TYPING_DESCRIPTION,
    cancel_report,
    choose_type_callback,
    receive_description,
    receive_location,
    report_entry,
)
from tests.conftest import make_callback_update, make_message_update


@pytest.mark.asyncio
async def test_report_entry_shows_three_types(mock_user):
    update, query = make_callback_update("cmd_report", mock_user)
    ctx = MagicMock()
    ctx.user_data = {}

    state = await report_entry(update, ctx)
    assert state == CHOOSING_TYPE
    args = query.edit_message_text.await_args
    assert "lapor" in args[0][0].lower()
    markup = args[1]["reply_markup"]
    callbacks = [b.callback_data for row in markup.inline_keyboard for b in row]
    assert len(callbacks) == 3


@pytest.mark.asyncio
async def test_choose_type_moves_to_description(mock_user):
    update, query = make_callback_update("report_type_NEED_HELP", mock_user)
    ctx = MagicMock()
    ctx.user_data = {}

    state = await choose_type_callback(update, ctx)
    assert state == TYPING_DESCRIPTION
    assert ctx.user_data["report_type"] == "NEED_HELP"


@pytest.mark.asyncio
async def test_receive_description_prompts_location(mock_user):
    update, message = make_message_update("Air mulai masuk rumah", user=mock_user)
    ctx = MagicMock()
    ctx.user_data = {"report_type": "NEED_HELP"}

    state = await receive_description(update, ctx)
    assert state == SHARING_LOCATION
    assert ctx.user_data["description"] == "Air mulai masuk rumah"
    message.reply_text.assert_awaited()


@pytest.mark.asyncio
async def test_receive_location_saves_report(mock_user):
    loc = MagicMock()
    loc.latitude = -6.2
    loc.longitude = 106.8
    update, message = make_message_update(location=loc, user=mock_user)
    ctx = MagicMock()
    ctx.user_data = {
        "report_type": "NEED_HELP",
        "description": "Butuh perahu",
    }

    with patch("bot.handlers.report.supabase_client.upsert_user", return_value={}) as upsert:
        with patch(
            "bot.handlers.report.supabase_client.insert_mutual_aid_report",
            return_value={"id": "uuid"},
        ) as insert:
            state = await receive_location(update, ctx)

    assert state == ConversationHandler.END
    insert.assert_called_once_with(
        reporter_id=mock_user.id,
        report_type="NEED_HELP",
        description="Butuh perahu",
        latitude=-6.2,
        longitude=106.8,
    )
    success_text = message.reply_text.await_args[0][0]
    assert "berhasil" in success_text.lower()


@pytest.mark.asyncio
async def test_receive_location_db_failure_message(mock_user):
    loc = MagicMock()
    loc.latitude = -6.2
    loc.longitude = 106.8
    update, message = make_message_update(location=loc, user=mock_user)
    ctx = MagicMock()
    ctx.user_data = {"report_type": "OFFER_HELP", "description": "Ada perahu"}

    with patch("bot.handlers.report.supabase_client.upsert_user", return_value={}):
        with patch(
            "bot.handlers.report.supabase_client.insert_mutual_aid_report",
            return_value=None,
        ):
            await receive_location(update, ctx)

    assert "gagal" in message.reply_text.await_args[0][0].lower()


@pytest.mark.asyncio
async def test_receive_location_reprompts_without_location(mock_user):
    update, message = make_message_update(text="not a location", user=mock_user)
    ctx = MagicMock()
    ctx.user_data = {"report_type": "INFO_ONLY", "description": "info"}

    state = await receive_location(update, ctx)
    assert state == SHARING_LOCATION
    assert "lokasi" in message.reply_text.await_args[0][0].lower()


@pytest.mark.asyncio
async def test_cancel_report_clears_state(mock_user):
    update, message = make_message_update(user=mock_user)
    ctx = MagicMock()
    ctx.user_data = {"report_type": "NEED_HELP"}

    state = await cancel_report(update, ctx)
    assert state == ConversationHandler.END
    assert ctx.user_data == {}
    assert "dibatalkan" in message.reply_text.await_args[0][0].lower()
