"""W-01, C-02: start menu and app build."""
import pytest

from bot.handlers.start import build_main_menu


def test_main_menu_has_three_commands():
    markup = build_main_menu()
    callbacks = [
        btn.callback_data
        for row in markup.inline_keyboard
        for btn in row
    ]
    assert "cmd_weather" in callbacks
    assert "cmd_quake" in callbacks
    assert "cmd_report" in callbacks
    assert len(callbacks) == 3


def test_build_app_registers_handlers(monkeypatch):
    import bot.config as cfg

    monkeypatch.setattr(cfg, "TELEGRAM_BOT_TOKEN", "test-token")
    monkeypatch.setattr(cfg, "SUPABASE_URL", "https://example.supabase.co")
    monkeypatch.setattr(cfg, "SUPABASE_KEY", "test-key")

    from bot.main import build_app

    app = build_app()
    assert app is not None
    assert len(app.handlers) > 0
