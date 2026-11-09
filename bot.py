import telebot
import re
import os
import logging
import threading
import copy
from urllib.parse import urlparse
from http.server import BaseHTTPRequestHandler, HTTPServer
from telebot.formatting import format_text, _html_tags

# Ensure blockquotes work flawlessly
_html_tags['blockquote'] = 'blockquote'
_html_tags['expandable_blockquote'] = 'blockquote expandable'

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
def process_text(text, entities):
    if not text: return CREDITS
    
    first_nl = text.find('\n')
    if first_nl == -1:
        title_text = text
        body_text = ""
        title_entities = entities or []
        body_entities = []
    else:
        title_text = text[:first_nl]
        body_text = text[first_nl+1:]
        title_entities = [e for e in entities if e.offset + e.length <= first_nl]
        body_entities = []
        for e in entities:
            if e.offset >= first_nl + 1:
                new_e = copy.copy(e)
                new_e.offset = e.offset - (first_nl + 1)
                body_entities.append(new_e)

    # 1. Process Title (Coating it in your link)
    try:
        html_title = format_text(title_text, title_entities)
    except Exception:
        html_title = title_text
        
    title_clean = re.sub(r'<[^>]+>', '', html_title).strip()
    title_clean = re.sub(r'(?:https?://|//)?(?:t\.me|www\.)[^\s]+', '', title_clean).strip()
    title_clean = re.sub(r'(?<![\w\.])@[a-zA-Z0-9_]+', '@rogueen', title_clean)
    final_title = f'<a href="{TARGET_LINK}">{title_clean}</a>' if title_clean else ""

    # 2. Process Body (Fix the scattered link mess)
    try:
        html_body = format_text(body_text, body_entities)
    except Exception:
        html_body = body_text
        
    def replacer(match):
        url = match.group(1)
        txt = match.group(2)
        
        # Leave your own link alone
        if TARGET_INVITE_CODE in url:
            return match.group(0)
            
        # Nuke other t.me links into plain text
        if 't.me/' in url:
            return TARGET_LINK
            
        # For hidden links (like "LINK" pointing to a massive URL), 
        # extract just the domain so it doesn't break the blockquote layout.
        try:
            domain = urlparse(url).netloc.replace('www.', '')
            if not domain: domain = txt
        except:
            domain = txt
            
        return f'<a href="{TARGET_LINK}">{domain}</a>'
        
    # Hijack all URLs in the body
    html_body = re.sub(r'<a href="([^"]+)">(.*?)</a>', replacer, html_body)
    
    # Hijack mentions in the body
    def mention_replacer(match):
        if TARGET_INVITE_CODE in match.group(1): return match.group(0)
        return f'<a href="{TARGET_LINK}">@rogueen</a>'
        
    html_body = re.sub(r'<a href="(https://t\.me/[^"]+)">(@[a-zA-Z0-9_]+)</a>', mention_replacer, html_body)
    
    # Clean up extra spaces
    html_body = re.sub(r' +', ' ', html_body).strip()
    
    final_text = f"{final_title}\n\n{html_body}" if final_title and html_body else final_title or html_body
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
            
        bot.reply_to(message, "✅ Formatting restored, links hijacked, posted.")
            
    except Exception as e:
        logging.error(f"Error processing message: {e}")
        bot.reply_to(message, f"❌ Failed: {e}")

if __name__ == "__main__":
    threading.Thread(target=run_dummy_server, daemon=True).start()
    logging.info("CAT's Entity Hijacker Bot is live. Executing.")
    bot.infinity_polling()
