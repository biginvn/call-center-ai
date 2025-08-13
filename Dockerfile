# syntax=docker/dockerfile:1
FROM python:3.12-slim

# Laravel best practice: group các layer để tận dụng cache tốt hơn
WORKDIR /app

# Copy requirements và cài đặt trước
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
# Cài đặt Playwright và các dependencies cần thiết
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget \
    unzip \
    libglib2.0-0 \
    libnss3 \
    libnspr4 \
    libatk-bridge2.0-0 \
    libdrm2 \
    libxkbcommon0 \
    libgtk-3-0 \
    libatspi2.0-0 \
    libxss1 \
    libasound2 \
    libgbm1 \
    libgtk-4-1 \
    fonts-liberation \
    fonts-noto-color-emoji \
    fonts-unifont \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install Playwright browser without system dependencies (we handle them above)
RUN python -m playwright install chromium

# Copy toàn bộ source (sẽ bị filter bới .dockerignore)
COPY . .

# Nếu muốn giữ WORKDIR ở /app thì CMD phải là app.main
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers"]
