import os
import logging
from threading import Thread
from flask import Flask
from dotenv import load_dotenv

# ប្រើប្រាស់ translators library ដែលមានស្ថេរភាពខ្ពស់
import translators as ts

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)

# Load environment variables
load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")
GITHUB_URL = os.getenv("GITHUB_URL", "https://github.com")
DEV_NAME = os.getenv("DEV_NAME", "@developer")

# Setup Logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

app = Flask(__name__)

@app.route("/")
def home():
    return "Telegram Translator Bot is running!"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

# Command Handler: /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = (
        "👋 **សូមស្វាគមន៍មកកាន់ Telegram Translator Bot!**\n\n"
        "🤖 កម្មវិធីនេះអាចស្វែងរកភាសាដើមដោយស្វ័យប្រវត្តិ (Auto-detect) "
        "និងបកប្រែទៅជាភាសា **ខ្មែរ** ឬ **English**។\n\n"
        "សូមផ្ញើសារ ឬអត្ថបទណាមួយដែលអ្នកចង់បកប្រែមកកាន់ Bot នេះ!"
    )
    
    keyboard = [
        [
            InlineKeyboardButton("🔗 GitHub Project", url=GITHUB_URL),
            InlineKeyboardButton("👨‍💻 Developer", url=f"https://t.me/{DEV_NAME.replace('@', '')}")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        welcome_text, parse_mode="Markdown", reply_markup=reply_markup
    )

# Message Handler: ទទួលអត្ថបទ
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    context.user_data["text_to_translate"] = user_text
    
    response_msg = (
        f"📝 **អត្ថបទដើម:** {user_text}\n\n"
        "👇 សូមជ្រើសរើសភាសាដែលអ្នកចង់បកប្រែទៅ៖"
    )
    
    keyboard = [
        [
            InlineKeyboardButton("🇰🇭 ខ្មែរ (Khmer)", callback_data="translate_km"),
            InlineKeyboardButton("🇬🇧 English", callback_data="translate_en")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        response_msg, parse_mode="Markdown", reply_markup=reply_markup
    )

# Callback Query Handler: បកប្រែភាសា
async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    target_lang = "km" if query.data == "translate_km" else "en"
    lang_name = "ភាសាខ្មែរ 🇰🇭" if target_lang == "km" else "English 🇬🇧"
    
    original_text = context.user_data.get("text_to_translate", "")
    
    if not original_text:
        await query.edit_message_text("❌ មិនមានអត្ថបទសម្រាប់បកប្រែទេ។ សូមផ្ញើសារថ្មីម្តងទៀត!")
        return

    translated_text = None

    # ១. សាកល្បងបកប្រែតាម Google (via translators)
    try:
        translated_text = ts.translate_text(original_text, translator='google', to_language=target_lang)
    except Exception:
        pass

    # ២. ប្រសិនបើ Google មានបញ្ហា រត់ទៅប្រើ Bing
    if not translated_text:
        try:
            translated_text = ts.translate_text(original_text, translator='bing', to_language=target_lang)
        except Exception:
            pass

    if not translated_text:
        await query.edit_message_text("❌ បរាជ័យក្នុងការបកប្រែ! សូមសាកល្បងម្ដងទៀតនៅពេលបន្តិចទៀត។")
        return

    result_text = (
        f"🌐 **ការបកប្រែជា {lang_name}:**\n\n"
        f"{translated_text}\n\n"
        f"---"
    )
    
    await query.edit_message_text(result_text, parse_mode="Markdown")

def main():
    server_thread = Thread(target=run_flask)
    server_thread.daemon = True
    server_thread.start()

    application = Application.builder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(CallbackQueryHandler(button_callback))

    print("🤖 Bot is running successfully...")
    application.run_polling()

if __name__ == "__main__":
    main()