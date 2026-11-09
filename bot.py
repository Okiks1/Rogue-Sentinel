import telebot
import re
import os
import logging
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHANNEL_ID = os.environ.get("CHANNEL_ID")

if not BOT_TOKEN or not CHANNEL_ID:
    raise ValueError("BOT_TOKEN and CHANNEL_ID environment variables are required.")

bot = telebot.TeleBot(BOT_TOKEN)

TARGET_LINK = "https://t.me/+ckfO94UHyhllODg0"
TARGET_INVITE_CODE = "+ckfO94UHyhllODg0"
CREDITS = "\n\n<b>Give Credits !!!</b>\n<i>Rogue Nomad</i>"

# --- FAKE WEB SERVER FOR RENDER ---
class DummyHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is alive.")

def run_dummy_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(('0.0.0.0', port), DummyHandler)
    logging.info(f"Dummy server running on port {port}")
    server.serve_forever()

# --- BOT LOGIC ---
def unroll_hidden_links(text, entities):
    if not text or not entities:
        return text
    sorted_entities = sorted(entities, key=lambda e: e.offset, reverse=True)
    for entity in sorted_entities:
        if entity.type == 'text_link':
            text = text[:entity.offset] + entity.url + text[entity.offset + entity.length:]
    return text

def process_text(text, entities):
    if not text:
        return CREDITS
    
    unrolled_text = unroll_hidden_links(text, entities)
    parts = unrolled_text.split('\n', 1)
    title = parts[0].strip()
    body = parts[1] if len(parts) > 1 else ""
    
    title_clean = re.sub(r'(?:https?://|//)?(?:t\.me|www\.)[^\s]+', '', title).strip()
    title_clean = re.sub(r'(?<![\w\.])@[a-zA-Z0-9_]+', '@rogueen', title_clean)
    final_title = f'<a href="{TARGET_LINK}">{title_clean}</a>' if title_clean else ""

    tme_pattern = r'(?:https?://|//)?t\.me/[^\s]+'
    body = re.sub(tme_pattern, lambda m: TARGET_LINK, body)
    
    mention_pattern = r'(?<![\w\.])@[a-zA-Z0-9_]+'
    body = re.sub(mention_pattern, f'<a href="{TARGET_LINK}">@rogueen</a>', body)
    
    placeholder = "___TARGET_LINK_PLACEHOLDER___"
    body = body.replace(TARGET_LINK, placeholder)
    
    url_pattern = r'(?:https?://|www\.)[^\s<]+'
    body = re.sub(url_pattern, lambda m: f'<a href="{TARGET_LINK}">{m.group(0)}</a>', body)
    
    body = body.replace(placeholder, TARGET_LINK)
    body = re.sub(r' +', ' ', body).strip()
    
    final_text = f"{final_title}\n\n{body}" if final_title and body else final_title or body
    return final_text + CREDITS

@bot.message_handler(content_types=['text', 'photo', 'video', 'document', 'audio', 'animation', 'voice'])
def handle_forward(message):
    try:
        raw_text = message.text or message.caption
        entities = message.entities or message.caption_entities
        final_text = process_text(raw_text, entities)
        
        if message.photo:
            bot.send_photo(CHANNEL_ID, message.photo[-1].file_id, caption=final_text, parse_mode='HTML')
        elif message.video:
            bot.send_video(CHANNEL_ID, message.video.file_id, caption=final_text, parse_mode='HTML')
        elif message.document:
            bot.send_document(CHANNEL_ID, message.document.file_id, caption=final_text, parse_mode='HTML')
        elif message.audio:
            bot.send_audio(CHANNEL_ID, message.audio.file_id, caption=final_text, parse_mode='HTML')
        elif message.animation:
            bot.send_animation(CHANNEL_ID, message.animation.file_id, caption=final_text, parse_mode='HTML')
        elif message.voice:
            bot.send_voice(CHANNEL_ID, message.voice.file_id, caption=final_text, parse_mode='HTML')
        elif message.text:
            bot.send_message(CHANNEL_ID, text=final_text, parse_mode='HTML', disable_web_page_preview=True)
            
        bot.reply_to(message, "✅ Posted to channel.")
            
    except Exception as e:
        logging.error(f"Error processing message: {e}")
        bot.reply_to(message, f"❌ Failed: {e}")

if __name__ == "__main__":
    # 1. Start the dummy web server in the background (Fix for Render)
    threading.Thread(target=run_dummy_server, daemon=True).start()
    
    # 2. Start the bot
    logging.info("CAT's Entity Hijacker Bot is live. Executing.")
    bot.infinity_polling()
