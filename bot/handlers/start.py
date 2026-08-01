"""Handler /start dan menu utama (inline keyboard)."""
import logging

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

from bot.services import supabase_client

logger = logging.getLogger(__name__)


def build_main_menu() -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton("🌤 Cek Cuaca Terkini", callback_data="cmd_weather")],
        [InlineKeyboardButton("🌍 Info Gempa Terbaru", callback_data="cmd_quake")],
        [
            InlineKeyboardButton(
                "🆘 Laporkan Bencana / Minta Bantuan", callback_data="cmd_report"
            )
        ],
    ]
    return InlineKeyboardMarkup(keyboard)


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handler untuk /start — registrasi user + tampilkan menu utama."""
    user = update.effective_user
    if user is None:
        return

    supabase_client.upsert_user(telegram_id=user.id)

    text = (
        f"Halo, {user.first_name}! 👋\n\n"
        "Selamat datang di *Sistem Informasi Bencana & Gotong Royong*.\n"
        "Silakan pilih menu di bawah:"
    )
    await update.message.reply_text(
        text, reply_markup=build_main_menu(), parse_mode="Markdown"
    )


async def back_to_menu_callback(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Dipanggil dari tombol 'Kembali ke Menu' di sub-flow lain."""
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "Silakan pilih menu:", reply_markup=build_main_menu()
    )
