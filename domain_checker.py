import os
import openai
import requests
import logging
import time
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackContext, filters, AIORateLimiter

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

# Add dictionaries to track user states and rate limits
user_states = {}
user_request_counts = {}
user_search_timestamps = {}  # Store timestamps of last /search command

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
        model="gpt-4o",
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
    await update.message.reply_text('Welcome! Use /search to find .ai domain ideas based on a theme.')

async def search(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    current_time = time.time()

    # Check if the user is within the cooldown period
    if user_id in user_search_timestamps:
        elapsed_time = current_time - user_search_timestamps[user_id]
        if elapsed_time < SEARCH_COOLDOWN:
            remaining_time = SEARCH_COOLDOWN - elapsed_time
            await update.message.reply_text(f"⏳ Please wait {int(remaining_time)} seconds before using /search again.")
            return

    # Update the last search timestamp
    user_search_timestamps[user_id] = current_time

    user_states[user_id] = 'waiting_for_theme'
    await update.message.reply_text('Please send me a theme to generate domain ideas.')

async def handle_message(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    current_time = time.time()

    # Initialize user request data if not present
    if user_id not in user_request_counts:
        user_request_counts[user_id] = {'count': 0, 'start_time': current_time}

    # Check if the time window has passed
    elapsed_time = current_time - user_request_counts[user_id]['start_time']
    if elapsed_time > TIME_WINDOW:
        user_request_counts[user_id] = {'count': 0, 'start_time': current_time}

    # Check if the user has exceeded the request limit
    if user_request_counts[user_id]['count'] >= REQUEST_LIMIT:
        await update.message.reply_text("⚠️ You have exceeded the request limit. Please try again later.")
        return

    # Increment the request count
    user_request_counts[user_id]['count'] += 1

    if user_states.get(user_id) == 'waiting_for_theme':
        theme = update.message.text
        await update.message.reply_text(f"🔍 Generating domain ideas based on theme: {theme}...")

        loading_message = await update.message.reply_text("⏳ Checking availability, please wait...")

        domains = generate_domain_ideas(theme)
        
        results = []
        buttons = []
        for domain in domains:
            available = check_domain_availability(domain)
            status = "✅ Available" if available else "❌ Taken"
            results.append(f"{domain}: {status}")
            
            if available:
                button = InlineKeyboardButton(f"Buy {domain} on GoDaddy", url=f"https://www.godaddy.com/domainsearch/find?checkAvail=1&tmskey=&domainToCheck={domain}")
                buttons.append(button)

        await loading_message.edit_text("\n".join(results))

        if buttons:
            reply_markup = InlineKeyboardMarkup([buttons])
            await update.message.reply_text("Available domains:", reply_markup=reply_markup)

        user_states[user_id] = None
    else:
        await update.message.reply_text("❗ Please use /search to start a new theme search.")

def main():
    if not TELEGRAM_TOKEN or not URL:
        logging.error("Environment variables TELEGRAM_TOKEN or URL are not set.")
        return

    # Configure the rate limiter
    rate_limiter = AIORateLimiter(overall_max_rate=30, overall_time_period=1, group_max_rate=1, group_time_period=60)

    # Build the application with the rate limiter
    application = ApplicationBuilder().token(TELEGRAM_TOKEN).rate_limiter(rate_limiter).build()

    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("search", search, block=True))
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
