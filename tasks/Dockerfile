FROM python:3.10-slim

WORKDIR /app
COPY ./requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Install system dependencies for Playwright + Firefox
RUN apt-get update && apt-get install -y \
    firefox-esr \
    libgtk-3-0 \
    libdbus-glib-1-2 \
    fonts-liberation \
    libnss3 \
    libx11-xcb1 \
    libxcomposite1 \
    libxdamage1 \
    libxrandr2 \
    libxss1 \
    libxtst6 \
    xdg-utils \
    wget \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

COPY . /app
CMD ["python", "worker.py"]


