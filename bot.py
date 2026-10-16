import os
import re
import math
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler, CallbackQueryHandler,
    ContextTypes, ConversationHandler, filters
)

# ============================================================
# KONFIGURASI
# ============================================================
BOT_TOKEN = os.getenv("BOT_TOKEN", "ISI_TOKEN_BOTFATHER_DI_SINI")
VIP_URL = os.getenv("VIP_URL", "https://t.me/username_anda")
GROWTH_RATE = 0.50  # 50% per tahun - hanya asumsi simulasi, BUKAN angka pasti

NAME, AGE, TARGET_AGE, INITIAL_SAVINGS = range(4)


def rupiah(value: float) -> str:
    return "Rp " + f"{round(value):,}".replace(",", ".")


def parse_number(text: str) -> float:
    # Menerima: 200000000 / 200.000.000 / 200,000,000
    cleaned = re.sub(r"[^\d]", "", text)
    if not cleaned:
        raise ValueError
    return float(cleaned)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text(
        "📈 *SIMULASI GRATIS*\n\n"
        "Saya akan membantu membuat simulasi sederhana berdasarkan data yang Anda masukkan.\n\n"
        "⚠️ Hasil adalah simulasi/ilustrasi, bukan jaminan keuntungan.\n\n"
        "Masukkan *Nama* Anda:",
        parse_mode="Markdown"
    )
    return NAME


async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["name"] = update.message.text.strip()
    await update.message.reply_text("Masukkan *Umur Anda*:", parse_mode="Markdown")
    return AGE


async def get_age(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        age = int(parse_number(update.message.text))
        if age < 1 or age > 100:
            raise ValueError
    except ValueError:
        await update.message.reply_text("Mohon masukkan umur dalam angka, contoh: *50*.", parse_mode="Markdown")
        return AGE

    context.user_data["age"] = age
    await update.message.reply_text("Target pensiun umur berapa?\nContoh: *60*", parse_mode="Markdown")
    return TARGET_AGE


async def get_target_age(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        target = int(parse_number(update.message.text))
        age = context.user_data["age"]
        if target <= age or target > 100:
            raise ValueError
    except ValueError:
        await update.message.reply_text(
            "Target pensiun harus lebih besar dari umur sekarang.\nContoh: *60*",
            parse_mode="Markdown"
        )
        return TARGET_AGE

    context.user_data["target_age"] = target
    await update.message.reply_text(
        "Masukkan *Tabungan Awal*:\nContoh: *200000000*",
        parse_mode="Markdown"
    )
    return INITIAL_SAVINGS


async def get_initial_savings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        savings = parse_number(update.message.text)
        if savings <= 0:
            raise ValueError
    except ValueError:
        await update.message.reply_text(
            "Mohon masukkan nominal dalam angka.\nContoh: *200000000*",
            parse_mode="Markdown"
        )
        return INITIAL_SAVINGS

    context.user_data["initial_savings"] = savings

    name = context.user_data["name"]
    age = context.user_data["age"]
    target = context.user_data["target_age"]
    years = target - age

    balance = savings
    lines = []
    for year in range(1, years + 1):
        balance *= (1 + GROWTH_RATE)
        lines.append(f"Tahun {year}: {rupiah(balance)}")

    result = (
        f"📈 *SIMULASI UNTUK {name.upper()}*\n\n"
        f"Umur sekarang : {age}\n"
        f"Target pensiun: {target}\n"
        f"Durasi        : {years} tahun\n"
        f"Tabungan Awal : {rupiah(savings)}\n\n"
        f"Growth asumsi : {GROWTH_RATE*100:.0f}% / tahun\n"
        f"⚠️ Ini hanya skenario ilustrasi, BUKAN angka fix atau jaminan hasil.\n\n"
        f"📊 *PERKEMBANGAN:*\n"
        + "\n".join(lines)
        + "\n\n"
        f"🔥 *Estimasi akhir:*\n"
        f"{rupiah(balance)}\n\n"
        "💎 *Ingin tahu caranya?*\n"
        "Akses strategi lengkap di komunitas VIP."
    )

    keyboard = [[InlineKeyboardButton("💎 DAFTAR VIP", url=VIP_URL)]]
    await update.message.reply_text(
        result,
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

    # Tombol simulasi ulang
    keyboard2 = [[InlineKeyboardButton("🔄 SIMULASI LAGI", callback_data="again")]]
    await update.message.reply_text(
        "Mau membuat simulasi untuk angka yang berbeda?",
        reply_markup=InlineKeyboardMarkup(keyboard2)
    )

    return ConversationHandler.END


async def again(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data.clear()
    await query.message.reply_text(
        "📈 *SIMULASI GRATIS*\n\nMasukkan *Nama* Anda:",
        parse_mode="Markdown"
    )
    return NAME


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text("Simulasi dibatalkan. Ketik /start jika ingin mulai lagi.")
    return ConversationHandler.END


def main():
    if not BOT_TOKEN or BOT_TOKEN == "ISI_TOKEN_BOTFATHER_DI_SINI":
        raise RuntimeError("Isi BOT_TOKEN dari @BotFather terlebih dahulu.")

    app = Application.builder().token(BOT_TOKEN).build()

    conversation = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_name)],
            AGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_age)],
            TARGET_AGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_target_age)],
            INITIAL_SAVINGS: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_initial_savings)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(conversation)
    app.add_handler(CallbackQueryHandler(again, pattern="^again$"))

    print("Bot berjalan...")
    app.run_polling()


if __name__ == "__main__":
    main()
