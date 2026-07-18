FROM python:3.11-slim

WORKDIR /app

# System deps for Pillow / matplotlib
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc libjpeg62-turbo-dev zlib1g-dev && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ app/
COPY streamlit_app.py .

EXPOSE 8000 8501
