FROM python:3.10-slim

WORKDIR /app

# Install system dependencies for scapy & network utilities
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    tcpdump \
    libpcap-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8501

HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health || exit 1

ENTRYPOINT ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0", "--server.headless=true"]
