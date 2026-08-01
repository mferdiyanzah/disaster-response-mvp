"""
Handler flow "Cek Cuaca Terkini".

Flow: GPS atau ketik nama wilayah → auto-detect level → fetch BMKG.
Kecamatan langsung tanpa drill-down; provinsi/kab masih pakai inline buttons.
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
from telegram.ext import ContextTypes

from bot.services import bmkg, nominatim, wilayah

logger = logging.getLogger(__name__)

AWAITING_WEATHER_INPUT = "awaiting_weather_input"
_BACK_MENU_BTN = InlineKeyboardButton("⬅️ Kembali ke Menu", callback_data="cmd_back")


async def _display_weather(
    reply_fn,
    kode_adm4: str,
    *,
    location_label: str | None = None,
) -> None:
    """Fetch BMKG dan tampilkan via reply_fn (reply_text or edit_message_text)."""
    keyboard = InlineKeyboardMarkup([[_BACK_MENU_BTN]])
    prefix = f"Lokasi: *{location_label}*\n\n" if location_label else ""

    weather_data = await bmkg.fetch_weather(kode_adm4)
    if weather_data is None:
        await reply_fn(
            f"{prefix}Data cuaca sedang tidak bisa diakses. Coba lagi beberapa saat lagi ya.",
            reply_markup=keyboard,
            parse_mode="Markdown",
        )
        return

    summary = bmkg.format_weather_summary(weather_data)
    await reply_fn(f"{prefix}{summary}", reply_markup=keyboard, parse_mode="Markdown")


async def _fetch_weather_for_district_id(
    update: Update,
    district_id: str,
    *,
    district_name: str | None = None,
    via_callback: bool = False,
) -> None:
    """Resolve adm4 dari district lalu tampilkan cuaca."""
    keyboard = InlineKeyboardMarkup([[_BACK_MENU_BTN]])

    try:
        kode_adm4 = await wilayah.resolve_adm4_for_bmkg(district_id)
    except Exception:
        logger.exception("Gagal fetch villages untuk district %s", district_id)
        text = "Gagal memuat data wilayah. Coba lagi nanti."
        if via_callback:
            await update.callback_query.edit_message_text(text, reply_markup=keyboard)
        else:
            await update.message.reply_text(text, reply_markup=keyboard)
        return

    if kode_adm4 is None:
        text = "Tidak ada data kelurahan untuk kecamatan ini."
        if via_callback:
            await update.callback_query.edit_message_text(text, reply_markup=keyboard)
        else:
            await update.message.reply_text(text, reply_markup=keyboard)
        return

    if via_callback:
        await _display_weather(
            update.callback_query.edit_message_text,
            kode_adm4,
            location_label=district_name,
        )
    else:
        await _display_weather(
            update.message.reply_text,
            kode_adm4,
            location_label=district_name,
        )


async def weather_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Entry point: pilih GPS atau ketik nama wilayah."""
    query = update.callback_query
    await query.answer()

    context.user_data["state"] = AWAITING_WEATHER_INPUT
    keyboard = [
        [InlineKeyboardButton("📍 Pakai Lokasi Saya", callback_data="cmd_weather_gps")],
        [InlineKeyboardButton("✏️ Ketik Nama Wilayah", callback_data="cmd_weather_text")],
        [_BACK_MENU_BTN],
    ]
    await query.edit_message_text(
        "Pilih cara cek cuaca:",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


async def weather_gps_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """User pilih GPS → minta share lokasi."""
    query = update.callback_query
    await query.answer()

    context.user_data["state"] = AWAITING_WEATHER_INPUT
    location_button = KeyboardButton("📍 Bagikan Lokasi Saya", request_location=True)
    reply_keyboard = ReplyKeyboardMarkup(
        [[location_button]], one_time_keyboard=True, resize_keyboard=True
    )

    await query.message.reply_text(
        "Bagikan lokasi kamu (tap tombol di bawah):",
        reply_markup=reply_keyboard,
    )


async def weather_text_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """User pilih ketik manual."""
    query = update.callback_query
    await query.answer()

    context.user_data["state"] = AWAITING_WEATHER_INPUT
    await query.edit_message_text(
        "Ketik nama *provinsi*, *kota/kabupaten*, atau *kecamatan* kamu:\n"
        "(contoh: _Banten_, _Tangerang Selatan_, _Pondok Aren_)",
        parse_mode="Markdown",
    )
    await query.message.reply_text(
        "Ketik nama wilayah kamu di chat ini.",
        reply_markup=ReplyKeyboardRemove(),
    )


async def handle_weather_location(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Terima GPS selama flow cuaca aktif."""
    if context.user_data.get("state") != AWAITING_WEATHER_INPUT:
        return

    location = update.message.location
    if location is None:
        return

    context.user_data["state"] = None
    await update.message.reply_text(
        "Mendeteksi lokasi kamu... 🔍",
        reply_markup=ReplyKeyboardRemove(),
    )

    geo = await nominatim.reverse_geocode(location.latitude, location.longitude)
    if geo is None:
        context.user_data["state"] = AWAITING_WEATHER_INPUT
        await update.message.reply_text(
            "Tidak bisa mendeteksi lokasi dari GPS.\n\n"
            "Silakan ketik nama *kecamatan* atau *kota* kamu "
            "(contoh: _Pondok Aren_, _Tangerang Selatan_).",
            parse_mode="Markdown",
        )
        return

    try:
        district = await wilayah.match_nominatim_to_emsifa(geo)
    except Exception:
        logger.exception("Gagal match Nominatim ke Emsifa")
        context.user_data["state"] = AWAITING_WEATHER_INPUT
        await update.message.reply_text(
            "Gagal memuat data wilayah. Ketik nama kecamatan/kota kamu secara manual."
        )
        return

    if district is None:
        context.user_data["state"] = AWAITING_WEATHER_INPUT
        display = geo.get("display_name", "lokasi ini")
        await update.message.reply_text(
            f"Lokasi *{display}* tidak cocok dengan data wilayah kami.\n\n"
            "Silakan ketik nama *kecamatan* atau *kota* kamu.",
            parse_mode="Markdown",
        )
        return

    await _fetch_weather_for_district_id(
        update,
        district["id"],
        district_name=district["name"].title(),
    )


async def handle_location_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """User ketik nama wilayah → auto-detect level."""
    if context.user_data.get("state") != AWAITING_WEATHER_INPUT:
        return

    query_text = update.message.text.strip()
    await update.message.reply_text("Sebentar, lagi cari wilayahnya... 🔍")

    try:
        result = await wilayah.smart_search(query_text)
    except Exception:
        logger.exception("Gagal search wilayah")
        await update.message.reply_text(
            "Gagal memuat data wilayah. Coba lagi nanti, atau ketik /start.",
        )
        return

    if result is None:
        await update.message.reply_text(
            f"Wilayah \"{query_text}\" tidak ditemukan.\n\n"
            "Coba ketik ulang nama *provinsi*, *kab/kota*, atau *kecamatan* "
            "(contoh: _Banten_, _Tangerang Selatan_, _Pondok Aren_).",
            parse_mode="Markdown",
        )
        return

    level, match = result

    if level == "district":
        context.user_data["state"] = None
        await _fetch_weather_for_district_id(
            update,
            match["id"],
            district_name=match["name"].title(),
        )
        return

    context.user_data["state"] = None

    if level == "province":
        try:
            regencies = await wilayah.get_regencies(match["id"])
        except Exception:
            await update.message.reply_text(
                "Gagal memuat daftar kab/kota. Coba lagi nanti."
            )
            return
        buttons = [
            [InlineKeyboardButton(r["name"].title(), callback_data=f"wr_{r['id']}")]
            for r in regencies
        ]
        buttons.append([_BACK_MENU_BTN])
        await update.message.reply_text(
            f"Provinsi: *{match['name'].title()}*\nPilih kabupaten/kota:",
            reply_markup=InlineKeyboardMarkup(buttons),
            parse_mode="Markdown",
        )

    elif level == "regency":
        try:
            districts = await wilayah.get_districts(match["id"])
        except Exception:
            await update.message.reply_text(
                "Gagal memuat daftar kecamatan. Coba lagi nanti."
            )
            return
        buttons = [
            [InlineKeyboardButton(d["name"].title(), callback_data=f"wd_{d['id']}")]
            for d in districts
        ]
        buttons.append([_BACK_MENU_BTN])
        await update.message.reply_text(
            f"Kab/Kota: *{match['name'].title()}*\nPilih kecamatan:",
            reply_markup=InlineKeyboardMarkup(buttons),
            parse_mode="Markdown",
        )


async def weather_regency_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """User pilih kab/kota dari button → tampilkan kecamatan."""
    query = update.callback_query
    await query.answer()

    regency_id = query.data.replace("wr_", "")

    try:
        districts = await wilayah.get_districts(regency_id)
    except Exception:
        await query.edit_message_text(
            "Gagal memuat daftar kecamatan. Coba lagi nanti.",
            reply_markup=InlineKeyboardMarkup([[_BACK_MENU_BTN]]),
        )
        return

    buttons = [
        [InlineKeyboardButton(d["name"].title(), callback_data=f"wd_{d['id']}")]
        for d in districts
    ]
    buttons.append([_BACK_MENU_BTN])

    await query.edit_message_text(
        "Pilih *kecamatan*:",
        reply_markup=InlineKeyboardMarkup(buttons),
        parse_mode="Markdown",
    )


async def weather_district_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """User pilih kecamatan dari button → fetch cuaca."""
    query = update.callback_query
    await query.answer()

    district_id = query.data.replace("wd_", "")
    await query.edit_message_text("Mengambil data cuaca... 🔍")
    await _fetch_weather_for_district_id(
        update,
        district_id,
        via_callback=True,
    )
