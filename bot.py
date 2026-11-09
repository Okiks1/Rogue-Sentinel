import telebot
import re
import os
import logging

# Set up bulletproof logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

BOT_TOKEN = os.environ.get("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN environment variable is missing. Do not run this without it.")

bot = telebot.TeleBot(BOT_TOKEN)

TARGET_LINK = "https://t.me/+ckfO94UHyhllODg0"
CREDITS = "\n\n<b>Give Credits !!!</b>\n<i>Rogue Nomad</i>"

def process_text(text):
    if not text:
        return CREDITS
    
    # Regex to catch http://, https://, and bare t.me/ links
    url_pattern = r'(https?://[^\s]+|(?<!\w)t\.me/[^\s]+)'
    
    def replace(match):
        original_url = match.group(0)
        
        # If it's already your target link, leave it untouched
        if TARGET_LINK in original_url:
            return original_url
            
        # Otherwise, cloak the original text to point to your channel
        # We use HTML anchor tags for Telegram's text_link entity
        return f'<a href="{TARGET_LINK}">{original_url}</a>'
    
    # Replace all matched links
    processed = re.sub(url_pattern, replace, text)
    
    # Append the credit footer
    return processed + CREDITS

@bot.message_handler(content_types=['text', 'photo', 'video', 'document', 'audio', 'animation', 'voice'])
def handle_forward(message):
    try:
        # Get the raw text or caption
        raw_text = message.text or message.caption
        final_text = process_text(raw_text)
        
        # Send WITHOUT the forward tag using copy/send methods
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
    logging.info("CAT's Cloaker Bot is live. Executing.")
    bot.infinity_polling()
