import os
import telebot

# Bot configuration
BOT_TOKEN = os.getenv("BOT_TOKEN")
OWNER_ID = os.getenv("OWNER_ID")
CHANNEL_LINK = "https://t.me/+ckfO94UHyhllODg0"

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN is missing")

if not OWNER_ID:
    raise ValueError("OWNER_ID is missing")

bot = telebot.TeleBot(BOT_TOKEN)

OWNER_ID = int(OWNER_ID)


# Start command
@bot.message_handler(commands=["start"])
def start(message):
    if message.from_user.id != OWNER_ID:
        return

    bot.reply_to(
        message,
        "⚡ Rogue Nomad Forwarder is online!\n\n"
        "Send or forward content to me and I'll process it."
    )


# Get your Telegram user ID
@bot.message_handler(commands=["id"])
def get_id(message):
    bot.reply_to(
        message,
        f"Your Telegram ID is: {message.from_user.id}"
    )


# Process forwarded messages and media
@bot.message_handler(
    content_types=[
        "text",
        "photo",
        "video",
        "document",
        "audio",
        "voice",
        "animation",
        "video_note",
        "sticker"
    ]
)
def forward_content(message):

    # Only allow the bot owner
    if message.from_user.id != OWNER_ID:
        return

    try:
        # Copy without the original forwarding attribution
        bot.copy_message(
            chat_id=message.chat.id,
            from_chat_id=message.chat.id,
            message_id=message.message_id
        )

        # Add a clearly labelled channel invitation
        bot.send_message(
            message.chat.id,
            f"⚡ Get more resources through "
            f'<a href="{CHANNEL_LINK}">Rogue Nomad</a>',
            parse_mode="HTML"
        )

    except Exception as error:
        bot.reply_to(
            message,
            f"Something went wrong: {error}"
        )


print("Rogue Nomad Forwarder is running...")

bot.infinity_polling(skip_pending=True)
