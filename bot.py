import telebot
import re
import os
import logging
import threading
import copy
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

# --- ENTITY PARSER (THE MAGIC) ---
def process_chunked(text, entities):
    if not text: return ""
    
    # Fallback if no entities exist (catches stray text)
    if not entities:
        t = re.sub(r'(?:https?://|//)?t\.me/[^\s]+', TARGET_LINK, text)
        t = re.sub(r'(?<![\w\.])@[a-zA-Z0-9_]+', f'<a href="{TARGET_LINK}">@rogueen</a>', t)
        t = re.sub(r'(?:https?://|www\.)[^\s]+', lambda m: f'<a href="{TARGET_LINK}">{m.group(0)}</a>', t)
        return t

    # Sort entities by offset descending so we can modify string without breaking offsets
    sorted_entities = sorted(entities, key=lambda e: e.offset, reverse=True)
    chunks = []
    last_idx = len(text)

    for e in sorted_entities:
        start = e.offset
        end = e.offset + e.length
        if end > len(text): continue

        plain_chunk = text[end:last_idx]
        if plain_chunk:
            chunks.append(("plain", plain_chunk))

        content = text[start:end]
        chunks.append((e.type, content, getattr(e, 'url', None)))
        last_idx = start

    if last_idx > 0:
        chunks.append(("plain", text[:last_idx]))

    chunks.reverse()
    result = []

    for chunk in chunks:
        if chunk[0] == "plain":
            t = chunk[1]
            t = re.sub(r'(?:https?://|//)?t\.me/[^\s]+', TARGET_LINK, t)
            t = re.sub(r'(?<![\w\.])@[a-zA-Z0-9_]+', f'<a href="{TARGET_LINK}">@rogueen</a>', t)
            t = re.sub(r'(?:https?://|www\.)[^\s]+', lambda m: f'<a href="{TARGET_LINK}">{m.group(0)}</a>', t)
            result.append(t)
        else:
            e_type, content, url = chunk[0], chunk[1], chunk[2]
            
            if e_type == 'text_link':
                # Keep original text, hijack the URL
                result.append(f'<a href="{TARGET_LINK}">{content}</a>')
            elif e_type == 'mention':
                # Replace mention text, hijack URL
                result.append(f'<a href="{TARGET_LINK}">@rogueen</a>')
            elif e_type == 'url':
                if 't.me/' in content and TARGET_INVITE_CODE not in content:
                    # Nuke other telegram links as raw text
                    result.append(TARGET_LINK)
                else:
                    # Cloak normal web links
                    result.append(f'<a href="{TARGET_LINK}">{content}</a>')
            elif e_type == 'bold':
                result.append(f'<b>{content}</b>')
            elif e_type == 'italic':
                result.append(f'<i>{content}</i>')
            elif e_type == 'underline':
                result.append(f'<u>{content}</u>')
            elif e_type == 'strikethrough':
                result.append(f'<s>{content}</s>')
            elif e_type == 'code':
                result.append(f'<code>{content}</code>')
            elif e_type == 'pre':
                result.append(f'<pre>{content}</pre>')
            elif e_type == 'blockquote':
                result.append(f'<blockquote>{content}</blockquote>')
            elif e_type == 'expandable_blockquote':
                result.append(f'<blockquote expandable>{content}</blockquote>')
            else:
                result.append(content)
                
    return "".join(result)

def process_text(text, entities):
    if not text: return CREDITS
    
    # 1. Split Title and Body safely at the first newline
    first_nl = text.find('\n')
    if first_nl == -1:
        title_text = text
        body_text = ""
        title_entities = entities
        body_entities = []
    else:
        title_text = text[:first_nl]
        body_text = text[first_nl+1:]
        
        title_entities = []
        body_entities = []
        for e in entities:
            if e.offset + e.length <= first_nl:
                title_entities.append(e)
            elif e.offset >= first_nl + 1:
                new_e = copy.copy(e)
                new_e.offset = e.offset - (first_nl + 1)
                body_entities.append(new_e)

    # 2. Process entities to HTML
    title_html = process_chunked(title_text, title_entities)
    body_html = process_chunked(body_text, body_entities)

    # 3. Coat the Title
    # Strip blockquotes from title so it wraps perfectly
    title_clean = title_html.replace('<blockquote>', '').replace('</blockquote>', '').replace('<blockquote expandable>', '').strip()
    final_title = f'<a href="{TARGET_LINK}">{title_clean}</a>' if title_clean else ""

    # 4. Combine
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
            
        bot.reply_to(message, "✅ Formatting preserved, links hijacked, posted.")
            
    except Exception as e:
        logging.error(f"Error processing message: {e}")
        bot.reply_to(message, f"❌ Failed: {e}")

if __name__ == "__main__":
    threading.Thread(target=run_dummy_server, daemon=True).start()
    logging.info("CAT's Entity Hijacker Bot is live. Executing.")
    bot.infinity_polling()
