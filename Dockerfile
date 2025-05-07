# syntax=docker/dockerfile:1
FROM python:3.12-slim

# Laravel best practice: group các layer để tận dụng cache tốt hơn
WORKDIR /app

# Copy requirements và cài đặt trước
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy toàn bộ source (sẽ bị filter bới .dockerignore)
COPY . .

# Nếu muốn giữ WORKDIR ở /app thì CMD phải là app.main
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
