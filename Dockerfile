FROM python:3.12-slim

WORKDIR /app


COPY requirements.txt .

# Install system dependencies
RUN apt-get update && apt-get install -y \
    supervisor \
    libpq-dev \
    gcc \
    wget \
    gnupg \
    ca-certificates \
    apt-transport-https \
    && wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google.list \
    && apt-get update && apt-get install -y \
    google-chrome-stable \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

COPY . .    

RUN pip install --no-cache-dir -r requirements.txt


RUN mkdir -p /root/.wdm/drivers/ && chmod -R 755 /root/.wdm/


# Create necessary directories
RUN mkdir -p /app/logs /app/data

# Make port 3306 available
EXPOSE 3306

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:3306/_stcore/health || exit 1

# Run the application
CMD ["streamlit", "run", "app.py", "--server.address=0.0.0.0", "--server.port=3306", "--server.headless=true", "--server.fileWatcherType=none"]