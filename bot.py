import telebot
import re
import os
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHANNEL_ID = os.environ.get("CHANNEL_ID")

if not BOT_TOKEN or not CHANNEL_ID:
    raise ValueError("BOT_TOKEN and CHANNEL_ID environment variables are required.")

bot = telebot.TeleBot(BOT_TOKEN)

TARGET_LINK = "https://t.me/+ckfO94UHyhllODg0"
TARGET_INVITE_CODE = "+ckfO94UHyhllODg0"
CREDITS = "\n\n<b>Give Credits !!!</b>\n<i>Rogue Nomad</i>"

def unroll_hidden_links(text, entities):
    """
    Finds invisible 'text_link' entities (like 'Click here'), extracts 
    the hidden URL, and replaces the visible text with the actual URL.
    """
    if not text or not entities:
        return text
    
    # We sort in reverse order so we don't mess up the character offsets
    sorted_entities = sorted(entities, key=lambda e: e.offset, reverse=True)
    
    for entity in sorted_entities:
        if entity.type == 'text_link':
            # Replace "Click here" with the actual hidden URL
            text = text[:entity.offset] + entity.url + text[entity.offset + entity.length:]
            
    return text

def process_text(text, entities):
    if not text:
        return CREDITS
    
    # 1. Unroll the invisible links
    unrolled_text = unroll_hidden_links(text, entities)
    
    # 2. Split Title (first line) and Body (rest of message)
    parts = unrolled_text.split('\n', 1)
    title = parts[0].strip()
    body = parts[1] if len(parts) > 1 else ""
    
    # 3. COAT THE TITLE
    # Strip any URLs or t.me links from the title so we can wrap the whole title cleanly
    title_clean = re.sub(r'(?:https?://|//)?(?:t\.me|www\.)[^\s]+', '', title).strip()
    title_clean = re.sub(r'(?<![\w\.])@[a-zA-Z0-9_]+', '@rogueen', title_clean)
    
    final_title = f'<a href="{TARGET_LINK}">{title_clean}</a>' if title_clean else ""

    # 4. PROCESS THE BODY
    # A. Nuke other t.me links (Replace directly with your link)
    tme_pattern = r'(?:https?://|//)?t\.me/[^\s]+'
    def replace_tme(match):
        if TARGET_INVITE_CODE in match.group(0):
            return TARGET_LINK
        return TARGET_LINK # Overwrite any other telegram link directly
    body = re.sub(tme_pattern, replace_tme, body)
    
    # B. Hijack Mentions (@username -> @rogueen)
    mention_pattern = r'(?<![\w\.])@[a-zA-Z0-9_]+'
    body = re.sub(mention_pattern, f'<a href="{TARGET_LINK}">@rogueen</a>', body)
    
    # C. Cloak normal links (Chatgpt.com -> looks like chatgpt.com but goes to your link)
    # First, protect your target link so it doesn't get double-coated
    placeholder = "___TARGET_LINK_PLACEHOLDER___"
    body = body.replace(TARGET_LINK, placeholder)
    
    # Match http/https/www links
    url_pattern = r'(?:https?://|www\.)[^\s<]+'
    body = re.sub(url_pattern, lambda m: f'<a href="{TARGET_LINK}">{m.group(0)}</a>', body)
    
    # Restore your link
    body = body.replace(placeholder, TARGET_LINK)
    
    # Clean up extra spaces
    body = re.sub(r' +', ' ', body).strip()
    
    # 5. Combine Title and Body
    final_text = f"{final_title}\n\n{body}" if final_title and body else final_title or body
    return final_text + CREDITS


@bot.message_handler(content_types=['text', 'photo', 'video', 'document', 'audio', 'animation', 'voice'])
def handle_forward(message):
    try:
        raw_text = message.text or message.caption
        # Extract text entities or caption entities
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
            
        bot.reply_to(message, "✅ Entity links unrolled, Title coated, and posted to the channel.")
            
    except Exception as e:
        logging.error(f"Error processing message: {e}")
        bot.reply_to(message, "❌ Failed to post. Check logs.")

if __name__ == "__main__":
    logging.info("CAT's Entity Hijacker Bot is live. Executing.")
    bot.infinity_polling()
