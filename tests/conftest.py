"""Shared fixtures for bot handler tests."""
from unittest.mock import AsyncMock, MagicMock

import pytest


@pytest.fixture
def mock_user():
    user = MagicMock()
    user.id = 12345
    user.first_name = "Warga"
    return user


@pytest.fixture
def mock_context():
    ctx = MagicMock()
    ctx.user_data = {}
    return ctx


def make_callback_update(callback_data: str, user=None):
    query = MagicMock()
    query.data = callback_data
    query.answer = AsyncMock()
    query.edit_message_text = AsyncMock()

    update = MagicMock()
    update.callback_query = query
    update.effective_user = user
    return update, query


def make_message_update(text: str | None = None, location=None, user=None):
    message = MagicMock()
    message.text = text
    message.location = location
    message.reply_text = AsyncMock()

    update = MagicMock()
    update.message = message
    update.effective_user = user
    return update, message
