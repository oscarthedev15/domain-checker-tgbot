import os
import openai
import requests
import logging
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackContext, filters
from telegram.ext.filters import TEXT, COMMAND

load_dotenv()


# Load API keys from environment variables
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
WHOIS_API_KEY = os.getenv("WHOIS_API_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")


WHOIS_API_URL = "https://www.whoisxmlapi.com/whoisserver/WhoisService"

# Set up logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# OpenAI API setup
openai.api_key = OPENAI_API_KEY

# Add a dictionary to track user states
user_states = {}

# Get the port from the environment variable
port = int(os.environ.get("PORT", 8080))

def generate_domain_ideas(theme):
    prompt = f"""Generate a list of 5 domain names ending in .ai based on the theme: {theme}. 
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
    # Clean up domain names to remove any numbering or extra characters
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
    logging.info(f"Response: {response.json()} \n\n\n\n")
    data = response.json()

    # Check for domain availability based on the presence of 'MISSING_WHOIS_DATA'
    
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
    user_states[user_id] = 'waiting_for_theme'
    await update.message.reply_text('Please send me a theme to generate domain ideas.')

async def handle_message(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    if user_states.get(user_id) == 'waiting_for_theme':
        theme = update.message.text
        await update.message.reply_text(f"Generating domain ideas based on theme: {theme}...")

        # Show loading message
        loading_message = await update.message.reply_text("Checking availability, please wait...")

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

def main():
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("search", search))
    application.add_handler(MessageHandler(TEXT & ~COMMAND, handle_message))

    application.run_polling()

if __name__ == "__main__":
    main()
