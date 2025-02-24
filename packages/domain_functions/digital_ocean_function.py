import os
import requests
from telegram import Update
from telegram.ext import CallbackContext

# Load API key from environment variable
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# Telegram API URL
TELEGRAM_API_URL = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"

def main(request):
    """
    DigitalOcean Function handler for Telegram webhook.
    """
    try:
        update = Update.de_json(request.json, None)
        chat_id = update.message.chat_id
        text = update.message.text

        # Reply logic
        reply_text = f"You said: {text}"
        
        # Send response to Telegram
        requests.post(TELEGRAM_API_URL, json={"chat_id": chat_id, "text": reply_text})

        return {"statusCode": 200, "body": "Message sent"}

    except Exception as e:
        return {"statusCode": 500, "body": str(e)}
