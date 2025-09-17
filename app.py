import os
import logging
import tempfile
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters
import yt_dlp

# إعدادات التسجيل
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# التوكن من متغير البيئة
TOKEN = os.getenv('TOKEN', '8088815454:AAGRIznmC-xZU_VWQdyaR8PVdDEp0pINBws')

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('مرحباً! أرسل لي رابط يوتيوب وسأساعدك في تحميله.')

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('أرسل لي رابط فيديو يوتيوب وسأقدم لك خيارات للتحميل.')

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    if 'youtube.com/' in url or 'youtu.be/' in url:
        keyboard = [
            [InlineKeyboardButton("📹 تحميل فيديو", callback_data=f'video_{url}')],
            [InlineKeyboardButton("🔊 تحميل صوت", callback_data=f'audio_{url}')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text('اختر نوع التحميل:', reply_markup=reply_markup)
    else:
        await update.message.reply_text('يرجى إرسال رابط يوتيوب صحيح.')

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    data = query.data
    url = data.split('_', 1)[1]
    
    if data.startswith('video_'):
        await query.edit_message_text(text="جاري تحميل الفيديو... قد يستغرق بعض الوقت")
        await download_video(url, query, context)
    elif data.startswith('audio_'):
        await query.edit_message_text(text="جاري تحميل الصوت... قد يستغرق بعض الوقت")
        await download_audio(url, query, context)

async def download_video(url, query, context):
    try:
        with tempfile.TemporaryDirectory() as tmp_dir:
            ydl_opts = {
                'format': 'best[height<=720]',
                'outtmpl': f'{tmp_dir}/%(title)s.%(ext)s',
                'quiet': True,
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                file_path = ydl.prepare_filename(info)
            
            with open(file_path, 'rb') as video_file:
                await context.bot.send_video(
                    chat_id=query.message.chat_id, 
                    video=video_file,
                    caption=f"📹 {info.get('title', 'فيديو')}"
                )
                
        await query.edit_message_text(text="تم التحميل بنجاح!")
        
    except Exception as e:
        logger.error(f"Error downloading video: {e}")
        await query.edit_message_text(text=f"حدث خطأ أثناء التحميل: {str(e)}")

async def download_audio(url, query, context):
    try:
        with tempfile.TemporaryDirectory() as tmp_dir:
            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': f'{tmp_dir}/%(title)s.%(ext)s',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
                'quiet': True,
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                file_path = ydl.prepare_filename(info).replace('.webm', '.mp3').replace('.m4a', '.mp3')
            
            with open(file_path, 'rb') as audio_file:
                await context.bot.send_audio(
                    chat_id=query.message.chat_id, 
                    audio=audio_file,
                    caption=f"🔊 {info.get('title', 'صوت')}"
                )
                
        await query.edit_message_text(text="تم التحميل بنجاح!")
        
    except Exception as e:
        logger.error(f"Error downloading audio: {e}")
        await query.edit_message_text(text=f"حدث خطأ أثناء التحميل: {str(e)}")

def main():
    application = Application.builder().token(TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    application.run_polling()

if __name__ == '__main__':
    main()
