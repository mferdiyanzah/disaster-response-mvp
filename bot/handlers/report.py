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

    await query.edit_message_text(
        f"Kamu pilih: {REPORT_TYPE_LABELS.get(report_type, report_type)}\n\n"
        "Sekarang, jelaskan situasinya secara singkat "
        "(contoh: 'Air mulai masuk rumah, ada balita, butuh perahu karet'):"
    )
    return TYPING_DESCRIPTION


async def receive_description(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["description"] = update.message.text

    location_button = KeyboardButton("📍 Bagikan Lokasi Saya", request_location=True)
    keyboard = ReplyKeyboardMarkup(
        [[location_button]], one_time_keyboard=True, resize_keyboard=True
    )
    await update.message.reply_text(
        "Terima kasih. Sekarang bagikan lokasi kamu ya (tap tombol di bawah):",
        reply_markup=keyboard,
    )
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

    # Pastikan user sudah terdaftar (harusnya sudah dari /start, tapi jaga-jaga)
    supabase_client.upsert_user(telegram_id=user.id)

    saved = supabase_client.insert_mutual_aid_report(
        reporter_id=user.id,
        report_type=report_type,
        description=description,
        latitude=location.latitude,
        longitude=location.longitude,
    )

    if saved is None:
        await update.message.reply_text(
            "Waduh, laporan kamu gagal tersimpan karena gangguan sistem. "
            "Coba kirim ulang beberapa saat lagi ya.",
            reply_markup=ReplyKeyboardRemove(),
        )
    else:
        await update.message.reply_text(
            "✅ Laporan kamu berhasil tersimpan dan akan muncul di dashboard "
            "tim relawan. Terima kasih sudah berpartisipasi!",
            reply_markup=ReplyKeyboardRemove(),
        )

    context.user_data.clear()
    return ConversationHandler.END


async def cancel_report(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.clear()
    await update.message.reply_text(
        "Laporan dibatalkan. Ketik /start buat kembali ke menu utama.",
        reply_markup=ReplyKeyboardRemove(),
    )
    return ConversationHandler.END
