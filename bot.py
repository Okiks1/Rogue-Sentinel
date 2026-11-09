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

def process_text(text):
    if not text:
        return CREDITS
    
    # 1. Obliterate ANY Telegram link that doesn't have your invite code
    tme_pattern = r'(?:https?://)?t\.me/[^\s]+'
    
    def remove_tme(match):
        original_url = match.group(0)
        # If it's your target link, keep it
        if TARGET_INVITE_CODE in original_url:
            return original_url
        # If it's some other t.me link, erase it completely
        return ""
    
    processed = re.sub(tme_pattern, remove_tme, text)
    
    # 2. Cloak normal web links (http/https) to point to your channel
    url_pattern = r'https?://[^\s]+'
    
    def cloak_url(match):
        original_url = match.group(0)
        # Skip if it's your target link
        if TARGET_INVITE_CODE in original_url:
            return original_url
        # Cloak the normal link
        return f'<a href="{TARGET_LINK}">{original_url}</a>'
    
    processed = re.sub(url_pattern, cloak_url, processed)
    
    # Clean up any double spaces left behind by the deleted links
    processed = re.sub(r' +', ' ', processed).strip()
    
    return processed + CREDITS

@bot.message_handler(content_types=['text', 'photo', 'video', 'document', 'audio', 'animation', 'voice'])
def handle_forward(message):
    try:
        raw_text = message.text or message.caption
        final_text = process_text(raw_text)
        
        # Send to your CHANNEL_ID, not back to the user
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
            
        # Optional: Let the user know it was posted
        bot.reply_to(message, "✅ Content scrubbed and posted to the channel.")
            
    except Exception as e:
        logging.error(f"Error processing message: {e}")
        bot.reply_to(message, "❌ Failed to post. Check bot admin rights and Channel ID.")

if __name__ == "__main__":
    logging.info("CAT's Total Hijack Bot is live. Executing.")
    bot.infinity_polling()
