FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# 設定環境變數
ENV PYTHONUNBUFFERED=1

# 暴露 API 服務的端口
EXPOSE 8000

# 啟動 API 服務
CMD ["python", "main.py"]