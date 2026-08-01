"""
Handler flow "Laporkan Bencana / Minta Bantuan" — pakai ConversationHandler
buat state machine: pilih jenis -> deskripsi -> lokasi -> simpan ke Supabase.

Cara wire ini ke bot/main.py:

    from telegram.ext import ConversationHandler, CallbackQueryHandler, MessageHandler, filters
    from bot.handlers.report import (
        CHOOSING_TYPE, TYPING_DESCRIPTION, SHARING_LOCATION,
        report_entry, choose_type_callback, receive_description, receive_location,
        cancel_report,
    )

    report_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(report_entry, pattern="^cmd_report$")],
        states={
            CHOOSING_TYPE: [CallbackQueryHandler(choose_type_callback, pattern="^report_type_")],
            TYPING_DESCRIPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_description)],
            SHARING_LOCATION: [MessageHandler(filters.LOCATION, receive_location)],
        },
        fallbacks=[CommandHandler("cancel", cancel_report)],
    )
    app.add_handler(report_conv)
"""
import logging

from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
    Update,
)
from telegram.ext import ContextTypes, ConversationHandler

from bot.services import supabase_client

logger = logging.getLogger(__name__)

# States buat ConversationHandler
CHOOSING_TYPE, TYPING_DESCRIPTION, SHARING_LOCATION = range(3)

REPORT_TYPE_LABELS = {
    "NEED_HELP": "🆘 Butuh Bantuan",
    "OFFER_HELP": "🤝 Tawarkan Bantuan",
    "INFO_ONLY": "ℹ️ Info Saja",
}

DESCRIPTION_PROMPTS = {
    "NEED_HELP": (
        "Sekarang, jelaskan kebutuhan kamu secara singkat "
        "(contoh: 'Air mulai masuk rumah, ada balita, butuh perahu karet'):"
    ),
    "OFFER_HELP": (
        "Sekarang, jelaskan bantuan yang kamu tawarkan "
        "(contoh: 'Saya punya perahu karet 2 unit, bisa bantu evakuasi'):"
    ),
    "INFO_ONLY": (
        "Sekarang, jelaskan situasi yang kamu lihat secara singkat "
        "(contoh: 'Jalan Raya X tergenang 50cm, kendaraan masih bisa lewat'):"
    ),
}

LOCATION_PROMPTS = {
    "NEED_HELP": "Bagikan lokasi kamu supaya relawan bisa menemukan kamu:",
    "OFFER_HELP": "Bagikan lokasi kamu sekarang supaya yang butuh bantuan tahu posisimu:",
    "INFO_ONLY": "Bagikan lokasi kejadian supaya bisa ditandai di peta:",
}

SUCCESS_MESSAGES = {
    "NEED_HELP": (
        "✅ Permintaan bantuan kamu sudah tersimpan dan akan muncul di "
        "dashboard tim relawan. Semoga segera ada yang bisa membantu!"
    ),
    "OFFER_HELP": (
        "✅ Tawaran bantuan kamu sudah tersimpan dan akan muncul di dashboard. "
        "Terima kasih atas kepedulianmu!"
    ),
    "INFO_ONLY": (
        "✅ Info kamu sudah tersimpan dan akan muncul di dashboard tim relawan. "
        "Terima kasih sudah berbagi informasi!"
    ),
}

ERROR_MESSAGES = {
    "NEED_HELP": (
        "Waduh, permintaan bantuan kamu gagal tersimpan karena gangguan sistem. "
        "Coba kirim ulang beberapa saat lagi ya."
    ),
    "OFFER_HELP": (
        "Waduh, tawaran bantuan kamu gagal tersimpan karena gangguan sistem. "
        "Coba kirim ulang beberapa saat lagi ya."
    ),
    "INFO_ONLY": (
        "Waduh, info kamu gagal tersimpan karena gangguan sistem. "
        "Coba kirim ulang beberapa saat lagi ya."
    ),
}


async def report_entry(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Entry point: user tap tombol 'Laporkan Bencana / Minta Bantuan'."""
    query = update.callback_query
    await query.answer()

    keyboard = [
        [InlineKeyboardButton(label, callback_data=f"report_type_{key}")]
        for key, label in REPORT_TYPE_LABELS.items()
    ]
    await query.edit_message_text(
        "Kamu mau lapor apa?", reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return CHOOSING_TYPE


async def choose_type_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    report_type = query.data.replace("report_type_", "")
    context.user_data["report_type"] = report_type

    prompt = DESCRIPTION_PROMPTS.get(report_type, DESCRIPTION_PROMPTS["INFO_ONLY"])
    await query.edit_message_text(
        f"Kamu pilih: {REPORT_TYPE_LABELS.get(report_type, report_type)}\n\n{prompt}"
    )
    return TYPING_DESCRIPTION


async def receive_description(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["description"] = update.message.text
    report_type = context.user_data.get("report_type", "INFO_ONLY")

    location_button = KeyboardButton("📍 Bagikan Lokasi Saya", request_location=True)
    keyboard = ReplyKeyboardMarkup(
        [[location_button]], one_time_keyboard=True, resize_keyboard=True
    )
    prompt = LOCATION_PROMPTS.get(report_type, LOCATION_PROMPTS["INFO_ONLY"])
    await update.message.reply_text(prompt, reply_markup=keyboard)
    return SHARING_LOCATION


async def receive_location(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.effective_user
    location = update.message.location

    if location is None:
        await update.message.reply_text(
            "Sepertinya itu bukan data lokasi. Tap tombol '📍 Bagikan Lokasi Saya' ya."
        )
        return SHARING_LOCATION

    report_type = context.user_data.get("report_type", "INFO_ONLY")
    description = context.user_data.get("description", "")

    contact_name = None
    telegram_username = None
    if report_type in ("NEED_HELP", "OFFER_HELP"):
        contact_name = user.full_name or user.first_name
        telegram_username = user.username

    # Pastikan user sudah terdaftar (harusnya sudah dari /start, tapi jaga-jaga)
    supabase_client.upsert_user(telegram_id=user.id)

    saved = supabase_client.insert_mutual_aid_report(
        reporter_id=user.id,
        report_type=report_type,
        description=description,
        latitude=location.latitude,
        longitude=location.longitude,
        contact_name=contact_name,
        telegram_username=telegram_username,
    )

    if saved is None:
        error_msg = ERROR_MESSAGES.get(report_type, ERROR_MESSAGES["INFO_ONLY"])
        await update.message.reply_text(error_msg, reply_markup=ReplyKeyboardRemove())
    else:
        success_msg = SUCCESS_MESSAGES.get(report_type, SUCCESS_MESSAGES["INFO_ONLY"])
        await update.message.reply_text(success_msg, reply_markup=ReplyKeyboardRemove())

    context.user_data.clear()
    return ConversationHandler.END


async def cancel_report(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.clear()
    await update.message.reply_text(
        "Laporan dibatalkan. Ketik /start buat kembali ke menu utama.",
        reply_markup=ReplyKeyboardRemove(),
    )
    return ConversationHandler.END
