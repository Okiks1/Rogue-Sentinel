import os
import re
import time
import threading
import logging
import telebot
from urllib.parse import urlparse
from flask import Flask, request, abort
from telebot.types import Update, InputMediaPhoto, InputMediaVideo, InputMediaDocument
from telebot.formatting import format_text

# --- CONFIGURATION ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

BOT_TOKEN = os.environ.get("BOT_TOKEN")
OWNER_ID = os.environ.get("OWNER_ID")
WEBHOOK_URL = os.environ.get("WEBHOOK_URL")
WEBHOOK_SECRET = os.environ.get("WEBHOOK_SECRET")

if not all([BOT_TOKEN, OWNER_ID, WEBHOOK_URL, WEBHOOK_SECRET]):
    raise ValueError("Missing required environment variables. Check BOT_TOKEN, OWNER_ID, WEBHOOK_URL, WEBHOOK_SECRET.")

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

TARGET_LINK = "https://t.me/+ckfO94UHyhllODg0"
BOT_USERNAME = "@roguenomad_bot"
FOOTER = "\n\n━━━━━━━━━━━━━━\n\n⚡ Rogue Nomad\n\nJoin our community:\n<a href=\"https://t.me/+ckfO94UHyhllODg0\">https://t.me/+ckfO94UHyhllODg0</a>\n\nGive Credits !!!\n\nRogue Nomad"

media_group_cache = {}

# --- TEXT PROCESSING ENGINE ---
def process_text(text, entities):
    if not text: 
        return FOOTER
        
    try:
        # Telebot's internal engine handles UTF-16 offsets flawlessly
        html_text = format_text(text, entities)
    except Exception as e:
        logging.error(f"Formatting error: {e}")
        html_text = text
        
    # 1. Extract hidden links (Text Links)
    def link_replacer(match):
        url = match.group(1)
        txt = match.group(2)
        # Skip target link or tg:// links
        if TARGET_LINK in url or url.startswith("tg://"):
            return match.group(0)
        parsed = urlparse(url)
        domain = parsed.netloc.replace('www.', '')
        if not domain: domain = parsed.path
        # Replace "Click here" with "Domain — URL"
        return f'<a href="{url}">{domain} — {url}</a>'
        
    html_text = re.sub(r'<a href="([^"]+)">(.*?)</a>', link_replacer, html_text)
    
    # 2. Replace Mentions with @roguenomad_bot
    # First, replace auto-linked mentions
    html_text = re.sub(
        r'<a href="(https://t\.me/[^"]+)">(@[a-zA-Z0-9_]+)</a>', 
        f'<a href="{TARGET_LINK}">{BOT_USERNAME}</a>', 
        html_text
    )
    # Then, replace raw text mentions
    html_text = re.sub(
        r'(?<![\w\./])@[a-zA-Z0-9_]+', 
        f'<a href="{TARGET_LINK}">{BOT_USERNAME}</a>', 
        html_text
    )
    
    # 3. Format Title
    parts = html_text.split('\n', 1)
    title = parts[0]
    body = parts[1] if len(parts) > 1 else ""
    
    # Strip tags from title to apply clean bold styling
    clean_title = re.sub(r'<[^>]+>', '', title)
    final_text = f"<b>{clean_title}</b>\n\n{body}" if body else f"<b>{clean_title}</b>"
    
    return final_text + FOOTER

# --- ALBUM PROCESSING ---
def process_album(group_id, chat_id):
    if group_id not in media_group_cache: return
    messages = media_group_cache.pop(group_id)
    media = []
    
    for i, msg in enumerate(messages):
        caption = None
        if i == 0:
            # Process text/caption for the first item in the album
            raw_text = msg.caption or ""
            entities = msg.caption_entities or []
            caption = process_text(raw_text, entities)
            
        if msg.content_type == 'photo':
            media.append(InputMediaPhoto(msg.photo[-1].file_id, caption=caption, parse_mode='HTML'))
        elif msg.content_type == 'video':
            media.append(InputMediaVideo(msg.video.file_id, caption=caption, parse_mode='HTML'))
        elif msg.content_type == 'document':
            media.append(InputMediaDocument(msg.document.file_id, caption=caption, parse_mode='HTML'))
            
    if media:
        try:
            bot.send_media_group(chat_id, media)
        except Exception as e:
            logging.error(f"Album send failed: {e}")

# --- BOT HANDLERS ---
def owner_only(func):
    def wrapper(message):
        if str(message.from_user.id) != str(OWNER_ID):
            bot.reply_to(message, "❌ Unauthorized. You are not the owner.")
            return
        return func(message)
    return wrapper

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    text = "🤖 **Rogue Sentinel**\n\nForward me messages from other channels. I will strip the original attribution, process hidden links, and add branding.\n\nCommands:\n/start - Start\n/id - Get your Telegram ID\n/help - Instructions\n/status - Bot status"
    bot.reply_to(message, text, parse_mode='Markdown')

@bot.message_handler(commands=['id'])
def send_id(message):
    bot.reply_to(message, f"Your Telegram ID: `{message.from_user.id}`", parse_mode='Markdown')

@bot.message_handler(commands=['status'])
def send_status(message):
    bot.reply_to(message, "✅ Rogue Sentinel is online and operational.")

@bot.message_handler(content_types=['text', 'photo', 'video', 'document', 'audio', 'animation'])
@owner_only
def handle_incoming(message):
    try:
        # Handle Albums
        if message.media_group_id:
            if message.media_group_id not in media_group_cache:
                media_group_cache[message.media_group_id] = []
                threading.Timer(1.5, process_album, args=(message.media_group_id, message.chat.id)).start()
            media_group_cache[message.media_group_id].append(message)
            return

        # Handle Single Messages
        raw_text = message.text or message.caption or ""
        entities = message.entities or message.caption_entities or []
        final_text = process_text(raw_text, entities)
        
        if message.content_type == 'text':
            bot.send_message(message.chat.id, final_text, parse_mode='HTML', disable_web_page_preview=True)
        elif message.content_type == 'photo':
            bot.send_photo(message.chat.id, message.photo[-1].file_id, caption=final_text, parse_mode='HTML')
        elif message.content_type == 'video':
            bot.send_video(message.chat.id, message.video.file_id, caption=final_text, parse_mode='HTML')
        elif message.content_type == 'document':
            bot.send_document(message.chat.id, message.document.file_id, caption=final_text, parse_mode='HTML')
        elif message.content_type == 'audio':
            bot.send_audio(message.chat.id, message.audio.file_id, caption=final_text, parse_mode='HTML')
        elif message.content_type == 'animation':
            bot.send_animation(message.chat.id, message.animation.file_id, caption=final_text, parse_mode='HTML')

    except Exception as e:
        logging.error(f"Error handling message: {e}")
        bot.reply_to(message, f"❌ Error: {e}")

# --- WEBHOOK SETUP & FLASK ROUTES ---
@app.route(f'/{WEBHOOK_SECRET}', methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = Update.de_json(json_string)
        bot.process_new_updates([update])
        return '', 200
    else:
        abort(403)

@app.route('/')
def index():
    return "Rogue Sentinel is running."

# Gunicorn runs the app, so we must set the webhook outside of __main__
if WEBHOOK_URL and WEBHOOK_SECRET:
    try:
        bot.remove_webhook()
        bot.set_webhook(url=f"{WEBHOOK_URL}/{WEBHOOK_SECRET}", secret_token=WEBHOOK_SECRET)
        logging.info("Webhook set successfully.")
    except Exception as e:
        logging.error(f"Failed to set webhook: {e}")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
