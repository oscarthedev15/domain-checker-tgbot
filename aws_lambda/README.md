local testing instructions:

1. Install docker
2. Run `docker build -t telegram_domain_bot .`
3. Run `docker run --env-file aws_lambda/.env -p 9000:8080 telegram_domain_bot   `
4. Run `curl -X POST http://localhost:9000/2015-03-31/functions/function/invocations -d '{"body": "{\"message\": {\"text\": \"/start\"}}"}'`
