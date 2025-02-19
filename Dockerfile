# Use an official Python runtime as a parent image
FROM python:3.11

# Set the working directory
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install any needed packages specified in requirements.txt
RUN apt-get update && apt-get install -y libssl-dev && \
    pip install --no-cache-dir -r requirements.txt

# Expose port 8080
EXPOSE 8080

# Run domain_checker.py when the container launches
CMD ["python", "domain_checker.py"]