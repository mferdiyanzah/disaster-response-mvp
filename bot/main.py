"""
Entrypoint bot Telegram. Mode default: long polling (buat development).

Jalankan:
    python -m bot.main

Untuk production (webhook di Render.com), lihat komentar di bagian bawah
file ini — perlu diintegrasikan dengan FastAPI/uvicorn server. Selama
hackathon jam ke-1 s.d. ke-3, polling sudah cukup (lihat RFC.md § Runtime modes
bagian 5.3).
"""
import logging

from telegram.ext import (
    ApplicationBuilder,
    CallbackQueryHandler,
    CommandHandler,
    ConversationHandler,
    MessageHandler,
    filters,
)

from bot import config
from bot.handlers.quake import quake_callback
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
from bot.handlers.start import back_to_menu_callback, start_command
from bot.handlers.weather import (
    handle_location_text,
    handle_weather_location,
    weather_callback,
    weather_district_callback,
    weather_gps_callback,
    weather_regency_callback,
    weather_text_callback,
)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


def build_app():
    config.validate_config()

    app = ApplicationBuilder().token(config.TELEGRAM_BOT_TOKEN).build()

    # /start + navigasi menu
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CallbackQueryHandler(back_to_menu_callback, pattern="^cmd_back$"))

    # Cek cuaca (GPS atau text search → auto-detect level → drill-down buttons)
    app.add_handler(CallbackQueryHandler(weather_callback, pattern="^cmd_weather$"))
    app.add_handler(CallbackQueryHandler(weather_gps_callback, pattern="^cmd_weather_gps$"))
    app.add_handler(CallbackQueryHandler(weather_text_callback, pattern="^cmd_weather_text$"))
    app.add_handler(CallbackQueryHandler(weather_regency_callback, pattern="^wr_"))
    app.add_handler(CallbackQueryHandler(weather_district_callback, pattern="^wd_"))

    # Info gempa
    app.add_handler(CallbackQueryHandler(quake_callback, pattern="^cmd_quake$"))

    # Laporkan bencana / minta bantuan (ConversationHandler)
    report_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(report_entry, pattern="^cmd_report$")],
        states={
            CHOOSING_TYPE: [
                CallbackQueryHandler(choose_type_callback, pattern="^report_type_")
            ],
            TYPING_DESCRIPTION: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_description)
            ],
            SHARING_LOCATION: [MessageHandler(filters.LOCATION, receive_location)],
        },
        fallbacks=[CommandHandler("cancel", cancel_report)],
    )
    app.add_handler(report_conv)

    # NOTE: Weather flow uses ad-hoc context.user_data["state"] = AWAITING_WEATHER_INPUT
    # (not ConversationHandler). The text/location MessageHandlers below must be
    # registered AFTER report ConversationHandler to avoid conflicts.
    # These handlers early-return if state != AWAITING_WEATHER_INPUT.
    app.add_handler(MessageHandler(filters.LOCATION, handle_weather_location))

    # Fallback text handler untuk weather flow (taruh terakhir)
    app.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_location_text)
    )

    return app


def main() -> None:
    app = build_app()
    logger.info("Bot mulai jalan (long polling)...")
    app.run_polling(allowed_updates=["message", "callback_query"])


if __name__ == "__main__":
    main()


# ============================================================
# TODO (Cursor) — Setup Webhook buat Production di Render.com
# ============================================================
# Ganti app.run_polling() di atas dengan app.run_webhook(...), contoh:
#
#     app.run_webhook(
#         listen="0.0.0.0",
#         port=config.PORT,
#         url_path=config.TELEGRAM_BOT_TOKEN,
#         webhook_url=f"{config.WEBHOOK_URL}/{config.TELEGRAM_BOT_TOKEN}",
#     )
#
# Pastikan WEBHOOK_URL di .env sudah diisi domain Render.com kamu,
# dan pilih start command Render sebagai `python -m bot.main`.
# Lihat RFC.md § Runtime modes buat detail kapan pindah dari
# polling ke webhook.
