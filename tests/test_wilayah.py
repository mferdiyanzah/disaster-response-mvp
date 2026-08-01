"""L-01–L-06: wilayah find_best_match and resolve_adm4_for_bmkg."""
from unittest.mock import AsyncMock, patch

import pytest

from bot.services.wilayah import find_best_match

CANDIDATES = [
    {"id": "31", "name": "BANTEN"},
    {"id": "36", "name": "TANGERANG SELATAN"},
]


def test_find_best_match_exact():
    assert find_best_match("BANTEN", CANDIDATES)["id"] == "31"


def test_find_best_match_substring():
    match = find_best_match("tangerang", CANDIDATES)
    assert match is not None
    assert "TANGERANG" in match["name"]


def test_find_best_match_none():
    assert find_best_match("UNKNOWN", CANDIDATES) is None


def test_find_best_match_case_insensitive():
    assert find_best_match("banten", CANDIDATES)["id"] == "31"


@pytest.mark.asyncio
async def test_resolve_adm4_for_bmkg_returns_formatted_code():
    """L-05: resolve_adm4_for_bmkg returns BMKG adm4 from first village."""
    mock_villages = [{"id": "3674060001", "name": "Desa A"}]
    with patch("bot.services.wilayah.get_villages", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_villages
        from bot.services.wilayah import resolve_adm4_for_bmkg

        result = await resolve_adm4_for_bmkg("367406")
        assert result == "36.74.06.1001"
        mock_get.assert_called_once_with("367406")


@pytest.mark.asyncio
async def test_resolve_adm4_for_bmkg_returns_none_on_empty():
    """L-06: resolve_adm4_for_bmkg returns None if no villages."""
    with patch("bot.services.wilayah.get_villages", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = []
        from bot.services.wilayah import resolve_adm4_for_bmkg

        result = await resolve_adm4_for_bmkg("999999")
        assert result is None
