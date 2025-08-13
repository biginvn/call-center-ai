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
    libatk-bridge2.0-0 \
    libcups2 \
    libexpat1 \
    libxcb1 \
    libxkbcommon0 \
    libatspi2.0-0 \
    libx11-6 \
    libxcomposite1 \
    libxdamage1 \
    libxext6 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libcairo2 \
    libpango-1.0-0 \
    libasound2 \
    fonts-liberation \
    fonts-unifont \
    libgtk-3-0 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

RUN python -m playwright install --with-deps chromium
# RUN playwright install-deps

# Copy toàn bộ source (sẽ bị filter bới .dockerignore)
COPY . .

# Nếu muốn giữ WORKDIR ở /app thì CMD phải là app.main
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers"]
