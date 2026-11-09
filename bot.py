import os
import telebot
from flask import Flask, request, abort

# =====================================
# ROGUE NOMAD FORWARDER
# =====================================

BOT_TOKEN = os.environ["BOT_TOKEN"]
OWNER_ID = int(os.environ["OWNER_ID"])
WEBHOOK_URL = os.environ["WEBHOOK_URL"].rstrip("/")
WEBHOOK_SECRET = os.environ["WEBHOOK_SECRET"]

CHANNEL_LINK = "https://t.me/+ckfO94UHyhllODg0"

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)


# =====================================
# HEALTH CHECK
# =====================================

@app.route("/", methods=["GET"])
def home():
    return "Rogue Nomad Forwarder is running!", 200


# =====================================
# START COMMAND
# =====================================

@bot.message_handler(commands=["start"])
def start(message):

    if message.from_user.id != OWNER_ID:
        return

    bot.reply_to(
        message,
        "⚡ Rogue Nomad Forwarder is online!\n\n"
        "Forward text, pictures, videos or documents to me."
    )


# =====================================
# USER ID COMMAND
# =====================================

@bot.message_handler(commands=["id"])
def get_id(message):

    bot.reply_to(
        message,
        f"Your Telegram ID: {message.from_user.id}"
    )


# =====================================
# MESSAGE PROCESSING
# =====================================

@bot.message_handler(
    content_types=[
        "text",
        "photo",
        "video",
        "document",
        "audio",
        "voice",
        "video_note",
        "animation",
        "sticker",
        "contact",
        "location",
        "venue",
        "poll",
        "dice"
    ]
)
def process_content(message):

    # Only the owner can use this bot
    if not message.from_user:
        return

    if message.from_user.id != OWNER_ID:
        return

    try:

        # Copy the original content without forwarding attribution
        bot.copy_message(
            chat_id=message.chat.id,
            from_chat_id=message.chat.id,
            message_id=message.message_id
        )

        # Add a clearly identified channel invitation
        bot.send_message(
            message.chat.id,
            "⚡ <b>ROGUE NOMAD</b>\n"
            "Join our community for more resources:\n"
            f'<a href="{CHANNEL_LINK}">Join Rogue Nomad</a>',
            parse_mode="HTML"
        )

    except Exception as error:

        print(f"Message processing error: {error}")

        bot.reply_to(
            message,
            "❌ I couldn't process this message. "
            "Please try again."
        )


# =====================================
# TELEGRAM WEBHOOK
# =====================================

@app.route("/webhook", methods=["POST"])
def webhook():

    received_secret = request.headers.get(
        "X-Telegram-Bot-Api-Secret-Token"
    )

    if received_secret != WEBHOOK_SECRET:
        abort(403)

    try:

        update = telebot.types.Update.de_json(
            request.get_data().decode("utf-8")
        )

        bot.process_new_updates([update])

        return "OK", 200

    except Exception as error:

        print(f"Webhook error: {error}")

        return "Error", 500


# =====================================
# REGISTER WEBHOOK
# =====================================

webhook_response = bot.set_webhook(
    url=f"{WEBHOOK_URL}/webhook",
    secret_token=WEBHOOK_SECRET,
    allowed_updates=["message"]
)

print("Webhook registration:", webhook_response)
print("Rogue Nomad Forwarder is ready!")
