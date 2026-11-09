import telebot
import re
import os
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

BOT_TOKEN = os.environ.get("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN environment variable is missing.")

bot = telebot.TeleBot(BOT_TOKEN)

TARGET_LINK = "https://t.me/+ckfO94UHyhllODg0"
CREDITS = "\n\n<b>Give Credits !!!</b>\n<i>Rogue Nomad</i>"

def process_text(text):
    if not text:
        return CREDITS
    
    # 1. Nuke all t.me links completely (with or without https://)
    # This catches bare "t.me/..." and full "https://t.me/..."
    tme_pattern = r'(?:https?://)?t\.me/[^\s]+'
    
    def replace_tme(match):
        original_url = match.group(0)
        # If it's already your target, leave it alone
        if TARGET_LINK in original_url:
            return original_url
        # Completely replace the visible text with your link
        return f'<a href="{TARGET_LINK}">{TARGET_LINK}</a>'
    
    processed = re.sub(tme_pattern, replace_tme, text)
    
    # 2. Cloak normal web links (http/https) that are NOT telegram links
    url_pattern = r'https?://[^\s]+'
    
    def replace_url(match):
        original_url = match.group(0)
        # Skip if it's your target link
        if TARGET_LINK in original_url:
            return original_url
        # Cloak the normal link (show original text, link to your channel)
        return f'<a href="{TARGET_LINK}">{original_url}</a>'
    
    processed = re.sub(url_pattern, replace_url, processed)
    
    # Append the credit footer
    return processed + CREDITS

@bot.message_handler(content_types=['text', 'photo', 'video', 'document', 'audio', 'animation', 'voice'])
def handle_forward(message):
    try:
        raw_text = message.text or message.caption
        final_text = process_text(raw_text)
        
        if message.photo:
            bot.send_photo(message.chat.id, message.photo[-1].file_id, caption=final_text, parse_mode='HTML')
        elif message.video:
            bot.send_video(message.chat.id, message.video.file_id, caption=final_text, parse_mode='HTML')
        elif message.document:
            bot.send_document(message.chat.id, message.document.file_id, caption=final_text, parse_mode='HTML')
        elif message.audio:
            bot.send_audio(message.chat.id, message.audio.file_id, caption=final_text, parse_mode='HTML')
        elif message.animation:
            bot.send_animation(message.chat.id, message.animation.file_id, caption=final_text, parse_mode='HTML')
        elif message.voice:
            bot.send_voice(message.chat.id, message.voice.file_id, caption=final_text, parse_mode='HTML')
        elif message.text:
            bot.send_message(message.chat.id, text=final_text, parse_mode='HTML', disable_web_page_preview=True)
            
    except Exception as e:
        logging.error(f"Error processing message: {e}")

if __name__ == "__main__":
    logging.info("CAT's Total Hijack Bot is live. Executing.")
    bot.infinity_polling()
