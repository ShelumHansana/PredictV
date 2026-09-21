FROM python:3.11-slim

WORKDIR /app

# Install system dependencies needed for compiling packages like LightGBM, CatBoost
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY . .

# Expose default port
EXPOSE 7860

# Run FastAPI app
CMD ["python", "server.py"]
