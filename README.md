# Domain Checker Telegram Bot

This is a Telegram bot that generates and checks the availability of `.ai` domain names based on a given theme.

## Features

- Generate domain name ideas using OpenAI's API.
- Check domain availability using WHOIS API.
- Interact with users via Telegram.

## Prerequisites

- Python 3.11
- Docker
- Git

## Setup

1. **Clone the Repository:**

   ```bash
   git clone git@github.com:oscarthedev15/domain-checker-tgbot.git
   cd domain-checker-tgbot
   ```

2. **Install Dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

3. **Environment Variables:**

   Create a `.env` file and add your API keys:

   ```plaintext
   OPENAI_API_KEY=your_openai_api_key
   WHOIS_API_KEY=your_whois_api_key
   TELEGRAM_BOT_TOKEN=your_telegram_bot_token
   ```

## Running Locally

1. **Run the Bot:**

   ```bash
   python domain_checker.py
   ```

## Docker

1. **Build the Docker Image:**

   ```bash
   docker build -t domain-checker-tgbot .
   ```

2. **Run the Docker Container:**

   ```bash
   docker run --env-file .env domain-checker-tgbot
   ```

## Deployment

- Follow the instructions to deploy on AWS or any other cloud provider.

## Contributing

Feel free to submit issues or pull requests.

## License

This project is licensed under the MIT License.
