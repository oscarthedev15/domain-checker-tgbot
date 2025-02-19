import os
import openai
import requests
import logging
from flask import Flask, request
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackContext, filters

load_dotenv()

app = Flask(__name__)

# Load API keys from environment variables
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
WHOIS_API_KEY = os.getenv("WHOIS_API_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# Initialize Telegram Bot
application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

# Set up logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# User states tracking
user_states = {}

@app.route("/", methods=["GET"])
def home():
    return "Domain Checker Bot is running!"

@app.route("/webhook", methods=["POST"])
def webhook():
    """Handle Telegram webhook updates."""
    update = Update.de_json(request.get_json(), application.bot)
    application.update_queue.put(update)
    return "ok", 200

async def start(update: Update, context: CallbackContext):
    await update.message.reply_text('Welcome! Use /search to find .ai domain ideas based on a theme.')

async def search(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    user_states[user_id] = 'waiting_for_theme'
    await update.message.reply_text('Please send me a theme to generate domain ideas.')

async def handle_message(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    if user_states.get(user_id) == 'waiting_for_theme':
        theme = update.message.text
        await update.message.reply_text(f"Generating domain ideas based on theme: {theme}...")

        # Show loading message
        loading_message = await update.message.reply_text("Checking availability, please wait...")

        # Generate domain ideas
        domains = generate_domain_ideas(theme)

        results = []
        for domain in domains:
            available = check_domain_availability(domain)
            status = "✅ Available" if available else "❌ Taken"
            results.append(f"{domain}: {status}")

        # Edit the loading message with the results
        await loading_message.edit_text("\n".join(results))

        # Reset the state
        user_states[user_id] = None
    else:
        await update.message.reply_text("Please use /search to start a new theme search.")

def set_webhook():
    """Set up the webhook for Telegram."""
    webhook_url = "https://domain-checker-tgbot-641042907649.us-central1.run.app"
    application.bot.set_webhook(url=f"{webhook_url}/webhook")
    logging.info(f"Webhook set: {webhook_url}/webhook")

if __name__ == "__main__":
    set_webhook()  # Set webhook on startup
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
