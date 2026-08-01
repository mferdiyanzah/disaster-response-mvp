"""C-01: config validation."""
import pytest

import bot.config as cfg


def test_validate_config_raises_when_token_missing(monkeypatch):
    monkeypatch.setattr(cfg, "TELEGRAM_BOT_TOKEN", "")
    monkeypatch.setattr(cfg, "SUPABASE_URL", "https://example.supabase.co")
    monkeypatch.setattr(cfg, "SUPABASE_KEY", "test-key")

    with pytest.raises(RuntimeError, match="TELEGRAM_BOT_TOKEN"):
        cfg.validate_config()


def test_validate_config_passes_when_required_set(monkeypatch):
    monkeypatch.setattr(cfg, "TELEGRAM_BOT_TOKEN", "token")
    monkeypatch.setattr(cfg, "SUPABASE_URL", "https://example.supabase.co")
    monkeypatch.setattr(cfg, "SUPABASE_KEY", "test-key")

    cfg.validate_config()
