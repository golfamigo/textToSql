FROM python:3.11-slim

WORKDIR /app

# 安裝構建依賴項
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# 複製需求檔案
COPY requirements.txt .

# 安裝核心依賴項
RUN pip install --no-cache-dir -r requirements.txt && \
    pip cache purge

# 逐一安裝大型依賴項以減少層大小
RUN pip install --no-cache-dir --timeout 180 faiss-cpu && \
    pip install --no-cache-dir --timeout 180 sentence-transformers && \
    pip install --no-cache-dir --timeout 120 openai && \
    pip install --no-cache-dir --timeout 120 anthropic && \
    pip install --no-cache-dir --timeout 100 google-generativeai && \
    pip install --no-cache-dir --timeout 100 -r requirements.txt && \
    pip cache purge && \
    rm -rf /tmp/* /var/tmp/* /root/.cache/pip

# 僅複製必要文件，減少總層數
COPY app ./app
COPY setup.py ./

# 創建一個簡單的入口點文件
RUN echo 'import uvicorn\nimport os\n\nif __name__ == "__main__":\n    port = int(os.getenv("PORT", "8000"))\n    print(f"啟動TextToSQL服務，端口: {port}")\n    uvicorn.run("app.api:app", host="0.0.0.0", port=port)\n' > main.py

# 設定環境變數
ENV PYTHONUNBUFFERED=1
ENV PORT=8000

# 暴露 API 服務的埠
EXPOSE 8000

# 啟動 API 服務
CMD ["python", "main.py"]