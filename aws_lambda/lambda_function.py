import json
import os
import openai
import requests
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackContext
from dotenv import load_dotenv
import asyncio

logging.basicConfig(level=logging.DEBUG)
logging.debug("Starting lambda function")

# Load environment variables from .env file
load_dotenv()

# Load environment variables
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

# OpenAI API setup
openai.api_key = OPENAI_API_KEY

# Initialize the bot application
app = Application.builder().token(TELEGRAM_TOKEN).build()

# Start command handler
async def start(update: Update, context: CallbackContext):
    await update.message.reply_text('Welcome! Use /search to find .ai domain ideas based on a theme.')

# Set up the handlers for the bot
def setup_handlers():
    app.add_handler(CommandHandler("start", start))
    # Add other handlers as needed

# Call setup_handlers once when the Lambda container is initialized
setup_handlers()

def generate_domain_ideas(theme):
    prompt = f"""Generate a list of 5 domain names ending in .ai based on the theme: {theme}. 
    The names should be closest to the theme. Example theme: english soccer teams 
    Example domain names: chelsea.ai, liverpool.ai, manchesterunited.ai
    Provide each domain name on a new line without any numbering or additional text."""

    client = os.environ["OPENAI_API_KEY"]

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

# Lambda handler function for webhook
def handler(event, context):
    logging.info("Lambda function invoked")
    logging.info(f"Received event: {event}")

    # Extract the incoming Telegram webhook update from the event body
    body = json.loads(event.get("body", "{}"))

    # Parse the update object from the incoming body
    update = Update.de_json(body, app.bot)

    # Initialize and process the update
    async def process():
        await app.initialize()
        await app.process_update(update)

    asyncio.run(process())

    return {
        "statusCode": 200,
        "body": json.dumps("OK")
    }
