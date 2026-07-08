# Use a lightweight official Python image
FROM python:3.11-slim

# Set the working directory inside the container
WORKDIR /app

# Install Flask
RUN pip install --no-cache-dir flask

# Copy our server code into the container
COPY server.py .

# Expose port 5000
EXPOSE 5000

# Run the application
CMD ["python", "server.py"]
