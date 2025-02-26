import os
import openai
import requests
import logging
import time
import json
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, 
    CallbackContext, filters, PicklePersistence
)

load_dotenv()

# Load API keys from environment variables
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
WHOIS_API_KEY = os.getenv("WHOIS_API_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
URL = os.getenv("URL")

WHOIS_API_URL = "https://www.whoisxmlapi.com/whoisserver/WhoisService"

# Set up logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# OpenAI API setup
openai.api_key = OPENAI_API_KEY

# Constants for rate limiting
REQUEST_LIMIT = 3
TIME_WINDOW = 60  # 60 seconds
SEARCH_COOLDOWN = 60  # 60 seconds cooldown for /search command

def generate_domain_ideas(theme):
    prompt = f"""Generate a list of 3 domain names ending in .ai based on the theme: {theme}. 
    The names should be closest to the theme. Example theme: english soccer teams 
    Example domain names: chelsea.ai, liverpool.ai, manchesterunited.ai
    Provide each domain name on a new line without any numbering or additional text."""

    client = openai.OpenAI(api_key=OPENAI_API_KEY)
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "system", "content": "You are a helpful AI domain name generator."},
                  {"role": "user", "content": prompt}]
    )
    message_content = response.choices[0].message.content.strip()
    domains = message_content.split("\n")
    cleaned_domains = [domain.split()[-1] for domain in domains if domain.strip()]
    logging.info(f"Generated domains: {cleaned_domains}")
    return cleaned_domains

def check_domain_availability(domain):
    params = {
        "apiKey": WHOIS_API_KEY,
        "domainName": domain,
        "outputFormat": "json"
    }
    response = requests.get(WHOIS_API_URL, params=params)
    data = response.json()

    if 'WhoisRecord' in data and data['WhoisRecord'].get('dataError') == 'MISSING_WHOIS_DATA':
        logging.info(f"Domain {domain} is available")
        return True
    else:
        logging.info(f"Domain {domain} is not available")
        return False

async def start(update: Update, context: CallbackContext):
    # Initialize user data if not present
    if 'state' not in context.user_data:
        context.user_data['state'] = None
    if 'search_timestamp' not in context.user_data:
        context.user_data['search_timestamp'] = 0
    if 'request_count' not in context.user_data:
        context.user_data['request_count'] = 0
    if 'request_start_time' not in context.user_data:
        context.user_data['request_start_time'] = time.time()
        
    await update.message.reply_text('Welcome! Use /search to find .ai domain ideas based on a theme.')

async def search(update: Update, context: CallbackContext):
    # Initialize user data if not present
    if 'state' not in context.user_data:
        context.user_data['state'] = None
    if 'search_timestamp' not in context.user_data:
        context.user_data['search_timestamp'] = 0
        
    current_time = time.time()

    # Check if the user is within the cooldown period
    elapsed_time = current_time - context.user_data['search_timestamp']
    if elapsed_time < SEARCH_COOLDOWN:
        remaining_time = int(SEARCH_COOLDOWN - elapsed_time)
        await update.message.reply_text(f"⏳ Please wait {remaining_time} seconds before using /search again.")
        return

    # Set the state before updating the timestamp
    context.user_data['state'] = 'waiting_for_theme'
    # Update the last search timestamp
    context.user_data['search_timestamp'] = current_time
    
    # Save the user data to ensure persistence
    await context.application.persistence.update_user_data(update.effective_user.id, context.user_data)
    
    await update.message.reply_text('Please send me a theme to generate domain ideas.')

async def handle_message(update: Update, context: CallbackContext):
    # Initialize user data if not present
    if 'state' not in context.user_data:
        context.user_data['state'] = None
    if 'request_count' not in context.user_data:
        context.user_data['request_count'] = 0
    if 'request_start_time' not in context.user_data:
        context.user_data['request_start_time'] = time.time()
    
    # Debug logging to help diagnose the issue
    logging.info(f"Current state for user {update.effective_user.id}: {context.user_data['state']}")
        
    current_time = time.time()

    # Check if the time window has passed
    elapsed_time = current_time - context.user_data['request_start_time']
    if elapsed_time > TIME_WINDOW:
        context.user_data['request_count'] = 0
        context.user_data['request_start_time'] = current_time

    # Check if the user has exceeded the request limit
    if context.user_data['request_count'] >= REQUEST_LIMIT:
        await update.message.reply_text("⚠️ You have exceeded the request limit. Please try again later.")
        return

    if context.user_data['state'] == 'waiting_for_theme':
        # Increment the request count
        context.user_data['request_count'] += 1
        
        theme = update.message.text
        await update.message.reply_text(f"🔍 Generating domain ideas based on theme: {theme}...")

        loading_message = await update.message.reply_text("⏳ Checking availability, please wait...")

        domains = generate_domain_ideas(theme)
        
        results = []
        keyboard = []
        for domain in domains:
            available = check_domain_availability(domain)
            status = "✅ Available" if available else "❌ Taken"
            results.append(f"{domain}: {status}")
            
            if available:
                # Create a separate row for each button
                button = InlineKeyboardButton(f"Buy {domain} on GoDaddy", url=f"https://www.godaddy.com/domainsearch/find?checkAvail=1&tmskey=&domainToCheck={domain}")
                keyboard.append([button])  # Each button in its own row

        # Combine results and buttons in a single message
        result_text = "\n".join(results)
        if keyboard:
            result_text += "\n\nAvailable domains:"
            reply_markup = InlineKeyboardMarkup(keyboard)
            await loading_message.edit_text(result_text, reply_markup=reply_markup)
        else:
            await loading_message.edit_text(result_text)

        # Reset state and save user data
        context.user_data['state'] = None
        await context.application.persistence.update_user_data(update.effective_user.id, context.user_data)
    else:
        await update.message.reply_text("❗ Please use /search to start a new theme search.")

def main():
    if not TELEGRAM_TOKEN or not URL:
        logging.error("Environment variables TELEGRAM_TOKEN or URL are not set.")
        return

    # Set up persistence with PicklePersistence
    persistence = PicklePersistence(filepath='bot_data.pickle')

    # Build the application with persistence
    application = ApplicationBuilder().token(TELEGRAM_TOKEN).persistence(persistence).build()

    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("search", search))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    PORT = 8080
    HOOK_URL = f"{URL}/{TELEGRAM_TOKEN}"
    logging.info(f"Starting webhook on port {PORT} with URL {HOOK_URL}")

    # Manually set the webhook
    application.bot.set_webhook(url=HOOK_URL)

    # Start the webhook server
    application.run_webhook(listen='0.0.0.0', port=PORT, url_path=TELEGRAM_TOKEN, webhook_url=HOOK_URL)

if __name__ == "__main__":
    main()
