"""Handler flow "Info Gempa Terbaru"."""
import logging

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

from bot.services import bmkg

logger = logging.getLogger(__name__)


async def quake_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Dipanggil saat user tap tombol 'Info Gempa Terbaru'."""
    query = update.callback_query
    await query.answer()

    quake_data = await bmkg.fetch_latest_quake()
    keyboard = InlineKeyboardMarkup(
        [[InlineKeyboardButton("⬅️ Kembali ke Menu", callback_data="cmd_back")]]
    )

    if quake_data is None:
        await query.edit_message_text(
            "Data gempa sedang tidak bisa diakses. Coba lagi beberapa saat lagi ya.\n\n"
            "Sementara, kamu bisa cek langsung di https://data.bmkg.go.id/gempabumi/",
            reply_markup=keyboard,
        )
        return

    summary = bmkg.format_quake_summary(quake_data)
    await query.edit_message_text(
        summary, reply_markup=keyboard, parse_mode="Markdown"
    )
