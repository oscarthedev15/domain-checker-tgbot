import os
import openai
import requests
import logging
from dotenv import load_dotenv
from telegram import Update

load_dotenv()

# Load API keys from environment variables
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
WHOIS_API_KEY = os.getenv("WHOIS_API_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

WHOIS_API_URL = "https://www.whoisxmlapi.com/whoisserver/WhoisService"

# Set up logging
logging.basicConfig(level=logging.INFO)
openai.api_key = OPENAI_API_KEY

def generate_domain_ideas(theme):
    prompt = f"Generate a list of 5 domain names ending in .ai based on the theme: {theme}."
    response = openai.Completion.create(
        engine="text-davinci-003",
        prompt=prompt,
        max_tokens=50
    )
    domains = response.choices[0].text.strip().split("\n")
    return [domain.strip() for domain in domains if domain.strip()]

def check_domain_availability(domain):
    params = {"apiKey": WHOIS_API_KEY, "domainName": domain, "outputFormat": "json"}
    response = requests.get(WHOIS_API_URL, params=params)
    data = response.json()
    return 'WhoisRecord' in data and data['WhoisRecord'].get('dataError') == 'MISSING_WHOIS_DATA'

def handle_telegram_webhook(params):
    update = Update.de_json(params, None)
    message = update.message.text.strip()
    chat_id = update.message.chat_id
    
    if message.startswith("/search"):
        domains = generate_domain_ideas(message)
        results = [f"{domain}: {'✅ Available' if check_domain_availability(domain) else '❌ Taken'}" for domain in domains]
        send_message(chat_id, "\n".join(results))
    else:
        send_message(chat_id, "Hello, received message")
    
    return {"statusCode": 200}

def main(params):
    return handle_telegram_webhook(params)

def send_message(chat_id, text):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": chat_id, "text": text}
    requests.post(url, json=payload)