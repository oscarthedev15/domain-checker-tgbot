import json
import os
import os
import openai
import requests
import logging
from pip._vendor import requests

logging.basicConfig(level=logging.DEBUG)
logging.debug("Starting lambda function")

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

def handler(event, context):
    logging.info("Lambda function invoked")
    logging.info(f"Received event: {event}")
    body = json.loads(event.get("body", "{}"))
    message = body.get("message", {})
    chat_id = message.get("chat", {}).get("id")
    text = message.get("text", "")
    token = os.environ["TELEGRAM_TOKEN"]
    
    if text and token:
        reply = f"You said: {text}"
        logging.info(f"Sending reply: {reply}")
        response = requests.post(f"https://api.telegram.org/bot{token}/sendMessage", 
                                 json={"chat_id": chat_id, "text": reply})
        logging.info(f"Telegram response: {response.json()}")
        return {"statusCode": 200, "body": json.dumps("OK Pu$$y")}
    
    if not token: 
        logging.error("TELEGRAM_TOKEN is not set")
        return {"statusCode": 500, "body": json.dumps("Error: TELEGRAM_TOKEN is not set")}

