"""L-01–L-04: wilayah find_best_match."""
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
