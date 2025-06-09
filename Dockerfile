# Base image with Python
FROM python:3.12-slim

# Avoids interactive prompts
ENV DEBIAN_FRONTEND=noninteractive

# Install Chrome dependencies and Chrome itself
RUN apt-get update && apt-get install -y \
    wget gnupg unzip curl gnupg2 ca-certificates fonts-liberation libappindicator3-1 libasound2 libatk-bridge2.0-0 \
    libatk1.0-0 libcups2 libdbus-1-3 libgdk-pixbuf2.0-0 libnspr4 libnss3 libx11-xcb1 libxcomposite1 libxdamage1 \
    libxrandr2 xdg-utils libu2f-udev libvulkan1 libxss1 libnss3-tools \
    --no-install-recommends && \
    rm -rf /var/lib/apt/lists/*

# Install Google Chrome
RUN wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb && \
    apt install -y ./google-chrome-stable_current_amd64.deb && \
    rm google-chrome-stable_current_amd64.deb

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . /app
WORKDIR /app

# Expose Flask port
EXPOSE 3306

# Run the app
CMD ["python", "flask_app.py"]
