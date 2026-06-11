from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

TOKEN = "8217705099:AAG11sK670SK-PoVKXCjpZevX-eKRBGBkeU"
SUPPORT_ID = 5989298023
CARD_NUMBER = "6104338967692712"
SUPPORT_USERNAME = "@samueljacksonk"

PRODUCTS = [
    ("⚡ 20گیگ 200 هزار تومان", "20gb"),
    ("⚡ 50گیگ 450 هزار تومان", "50gb"),
    ("⚡ 110گیگ 900 هزار تومان", "110gb"),
]

PRICES = {
    "20gb": ("20 گیگ", "200,000"),
    "50gb": ("50 گیگ", "450,000"),
    "110gb": ("110 گیگ", "900,000"),
}

def main_menu():
    keyboard = [
        ["🛍 خرید اشتراک"],
        ["📱 سرویس های من", "♻️ تمدید سرویس"],
        ["🏦 کیف پول + شارژ"],
        ["📞 پشتیبانی"],
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("سلام خوش آمدید 👋", reply_markup=main_menu())

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text == "🛍 خرید اشتراک" or text == "🏦 کیف پول + شارژ":
        keyboard = [[InlineKeyboardButton(p[0], callback_data=p[1])] for p in PRODUCTS]
        await update.message.reply_text("انتخاب نوع محصول:", reply_markup=InlineKeyboardMarkup(keyboard))
    elif text == "📞 پشتیبانی":
        await update.message.reply_text(f"برای پشتیبانی:\n{SUPPORT_USERNAME}")
    elif text == "📱 سرویس های من":
        await update.message.reply_text("شما هنوز سرویس فعالی ندارید.")
    elif text == "♻️ تمدید سرویس":
        await update.message.reply_text("سرویسی برای تمدید یافت نشد.")

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    if data.startswith("confirm:"):
        user_id = int(data.split(":")[1])
        config = context.bot_data.get(f"config_{user_id}", "")
        if config:
            await context.bot.send_message(chat_id=user_id, text=f"✅ پرداخت تایید شد!\n\n🔑 کانفیگ شما:\n\n<code>{config}</code>", parse_mode="HTML")
        else:
            await context.bot.send_message(chat_id=user_id, text="✅ پرداخت تایید شد! کانفیگ به زودی ارسال می‌شود.")
        await query.edit_message_caption(caption=query.message.caption + "\n\n✅ تایید شد", reply_markup=None)
    elif data.startswith("reject:"):
        user_id = int(data.split(":")[1])
        await context.bot.send_message(chat_id=user_id, text=f"❌ رسید تایید نشد.\nلطفاً با پشتیبانی تماس بگیرید:\n{SUPPORT_USERNAME}")
        await query.edit_message_caption(caption=query.message.caption + "\n\n❌ رد شد", reply_markup=None)
    elif data in PRICES:
        name, price_toman = PRICES[data]
        price_rial = int(price_toman.replace(",", "")) * 10
        price_rial_formatted = f"{price_rial:,}"
        context.user_data["pending_order"] = {"product": name, "toman": price_toman, "rial": price_rial_formatted}
        msg = (f"🚫 واریز پول و شبا پذیرفته نمیشود.\n\n💳 پرداخت کارت‌به‌کارت\n\nلطفاً مبلغ {price_toman} تومان معادل {price_rial_formatted} ریال را دقیقاً به کارت زیر واریز کنید:\n\n<code>{CARD_NUMBER}</code>\n\n📸 سپس عکس کامل و واضح رسید را همینجا ارسال کنید.\n\n⚠️ مبلغ واریزی باید دقیقاً مطابق فاکتور باشد.\nدر صورت واریز مبلغ اشتباه یا رُند شده، تایید رسید ممکن است با تأخیر انجام شود.")
        await query.edit_message_text(msg, parse_mode="HTML")

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    order = context.user_data.get("pending_order")
    if not order:
        await update.message.reply_text("لطفاً ابتدا یک محصول انتخاب کنید.")
        return
    caption = (f"📥 رسید جدید!\n👤 {user.full_name}\n🆔 ID: {user.id}\n📱 یوزرنیم: @{user.username or 'ندارد'}\n📦 محصول: {order['product']}\n💰 مبلغ: {order['toman']} تومان")
    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("✅ تایید + ارسال کانفیگ", callback_data=f"confirm:{user.id}"), InlineKeyboardButton("❌ رد کردن", callback_data=f"reject:{user.id}")]])
    await context.bot.send_photo(chat_id=SUPPORT_ID, photo=update.message.photo[-1].file_id, caption=caption, reply_markup=keyboard)
    await update.message.reply_text("✅ رسید دریافت شد.\nپس از تایید، کانفیگ ارسال می‌شود. ⏳")
    context.user_data.clear()

async def handle_config(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id != SUPPORT_ID:
        return
    if len(context.args) < 2:
        await update.message.reply_text("استفاده: /config <user_id> <کانفیگ>")
        return
    try:
        user_id = int(context.args[0])
        config_text = " ".join(context.args[1:])
        context.bot_data[f"config_{user_id}"] = config_text
        await update.message.reply_text("✅ کانفیگ ذخیره شد. حالا روی تایید بزن.")
    except Exception as e:
        await update.message.reply_text(f"خطا: {e}")

if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("config", handle_config))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.run_polling()
