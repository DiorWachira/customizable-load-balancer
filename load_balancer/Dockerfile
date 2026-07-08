FROM python:3.11-slim

# Install system dependencies including docker cli tool
RUN apt-get update && apt-get install -y docker.io curl && rm -rf /var/lib/apt/lists/*

WORKDIR /app

RUN pip install --no-cache-dir flask requests

COPY consistent_hash.py app.py ./

EXPOSE 5000

CMD ["python", "app.py"]
