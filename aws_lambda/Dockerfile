# Specify a base image
FROM python:3.9-slim

# Set the working directory
WORKDIR /aws_lambda

# Copy the lambda function code into the container
COPY lambda_function.py .

# Install any dependencies if needed
# COPY requirements.txt .
# RUN pip install -r requirements.txt

# Command to run the lambda function (if needed for testing)
# CMD ["python", "lambda_function.py"]
