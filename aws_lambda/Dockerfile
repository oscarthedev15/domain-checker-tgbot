# Specify a base image
FROM public.ecr.aws/lambda/python:3.11

# Copy the lambda function code into the container
COPY lambda_function.py .

# Install any dependencies if needed
COPY requirements.txt .
RUN pip install -r requirements.txt

# Command to run the lambda function (if needed for testing)
CMD ["lambda_function.handler"]
