Replace the code in main.py with a Telegram bot script. 

First, install `python-telegram-bot` and `yt-dlp` using pip, and make sure `ffmpeg` is available. 

Here is the Python script:

import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)
import yt_dlp

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

TOKEN = "8490646104:AAFktstlYB3vPEDaeJDiJ1sRUMUiOBWfvvs"

if not os.path.exists('downloads'):
    os.makedirs('downloads')

user_urls = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("أهلاً بك! أرسل لي أي رابط من شبكات التواصل الاجتماعي لبدء التحميل.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()
    
    if not url.startswith("http"):
        await update.message.reply_text("من فضلك أرسل رابطاً صحيحاً يبدأ بـ http أو https.")
        return

    user_id = update.message.from_user.id
    user_urls[user_id] = url

    keyboard = [
        [
            InlineKeyboardButton("🎬 MP4 (أعلى جودة)", callback_data='mp4_best'),
            InlineKeyboardButton("🎬 MP4 (720p)", callback_data='mp4_720'),
        ],
        [
            InlineKeyboardButton("🎬 MP4 (480p)", callback_data='mp4_480'),
            InlineKeyboardButton("🎵 صوت MP3", callback_data='mp3'),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("تم استلام الرابط، اختر الصيغة والدقة المطلوبة:", reply_markup=reply_markup)

async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    url = user_urls.get(user_id)

    if not url:
        await query.edit_message_text("حدث خطأ، يرجى إرسال الرابط من جديد.")
        return

    choice = query.data
    await query.edit_message_text("⏳ جاري التحميل... يرجى الانتظار.")

    ydl_opts = {
        'outtmpl': f'downloads/{user_id}_%(title)s.%(ext)s',
        'quiet': True,
    }

    if choice == 'mp3':
        ydl_opts.update({
            'format': 'bestaudio/best',
            'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': '192'}],
        })
    elif choice == 'mp4_best':
        ydl_opts['format'] = 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best'
    elif choice == 'mp4_720':
        ydl_opts['format'] = 'bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[height<=720][ext=mp4]/best'
    elif choice == 'mp4_480':
        ydl_opts['format'] = 'bestvideo[height<=480][ext=mp4]+bestaudio[ext=m4a]/best[height<=480][ext=mp4]/best'

    file_path = None
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            file_path = filename if choice != 'mp3' else os.path.splitext(filename)[0] + '.mp3'

        await query.edit_message_text("📤 جاري رفع الملف إلى تلجرام...")
        
        with open(file_path, 'rb') as f:
            if choice == 'mp3':
                await context.bot.send_audio(chat_id=user_id, audio=f)
            else:
                await context.bot.send_video(chat_id=user_id, video=f)
        
        await query.message.delete()
    except Exception as e:
        await query.edit_message_text(f"حدث خطأ أثناء التحميل: {str(e)}")
    finally:
        if file_path and os.path.exists(file_path):
            os.remove(file_path)

if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CallbackQueryHandler(button_click))
    print("البوت يعمل الآن...")
    app.run_polling()
