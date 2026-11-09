import telebot
import re
import os
import logging
import threading
import html
from urllib.parse import urlparse
from http.server import BaseHTTPRequestHandler, HTTPServer
from telebot.formatting import format_text

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
    
    # 1. Convert ALL entities to HTML safely using Telebot's engine
    try:
        html_text = format_text(text, entities)
    except Exception as e:
        logging.error(f"Formatting error: {e}")
        html_text = html.escape(text)

    # 2. Split the HTML into Title and Body safely
    parts = html_text.split('\n', 1)
    title_html = parts[0].strip()
    body_html = parts[1] if len(parts) > 1 else ""

    # 3. Process Title (Coating it in your link)
    # Strip all HTML tags and unescape entities to get clean text for the title
    title_clean = re.sub(r'<[^>]+>', '', title_html)
    title_clean = html.unescape(title_clean)
    # Strip any raw URLs from the title
    title_clean = re.sub(r'(?:https?://|//)?(?:t\.me|www\.)[^\s]+', '', title_clean).strip()
    # Hijack mentions in title
    title_clean = re.sub(r'(?<![\w\.])@[a-zA-Z0-9_]+', '@rogueen', title_clean)
    
    # Wrap the entire clean title in your channel link
    final_title = f'<a href="{TARGET_LINK}">{title_clean}</a>' if title_clean else ""

    # 4. Process Body
    # A. Nuke any plain text t.me links that Telegram didn't format as entities
    body_html = re.sub(r'(?:https?://|//)?t\.me/[^\s<]+', TARGET_LINK, body_html)

    # B. Hijack formatted <a> tags (like the "LINK" word pointing to mlh.com)
    def replacer(match):
        url = match.group(1)
        txt = match.group(2)
        
        if TARGET_INVITE_CODE in url:
            return match.group(0)
            
        if 't.me/' in url:
            return TARGET_LINK
            
        # Extract the domain name to keep the blockquote clean
        try:
            domain = urlparse(url).netloc.replace('www.', '')
            if not domain: domain = txt
        except:
            domain = txt
            
        # Return the clean domain text, but pointing to TARGET_LINK
        return f'<a href="{TARGET_LINK}">{domain}</a>'
        
    body_html = re.sub(r'<a href="([^"]+)">(.*?)</a>', replacer, body_html)
    
    # C. Hijack remaining raw mentions in the body text
    body_html = re.sub(r'(?<![\w\.])@[a-zA-Z0-9_]+', f'<a href="{TARGET_LINK}">@rogueen</a>', body_html)
    
    # D. Cloak any remaining plain text URLs in body
    placeholder = "___TARGET_LINK_PLACEHOLDER___"
    body_html = body_html.replace(TARGET_LINK, placeholder)
    body_html = re.sub(r'(?:https?://|www\.)[^\s<]+', lambda m: f'<a href="{TARGET_LINK}">{m.group(0)}</a>', body_html)
    body_html = body_html.replace(placeholder, TARGET_LINK)

    # 5. Combine and add credits
    final_text = f"{final_title}\n\n{body_html}" if final_title and body_html else final_title or body_html
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
            
        bot.reply_to(message, "✅ Formatting fixed, links hijacked, posted.")
            
    except Exception as e:
        logging.error(f"Error processing message: {e}")
        bot.reply_to(message, f"❌ Failed: {e}")

if __name__ == "__main__":
    threading.Thread(target=run_dummy_server, daemon=True).start()
    logging.info("CAT's Entity Hijacker Bot is live. Executing.")
    bot.infinity_polling()
