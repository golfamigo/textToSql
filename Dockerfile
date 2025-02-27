FROM python:3.11-slim

WORKDIR /app

# 安裝構建依賴項
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# 複製並安裝依賴項（使用緩存層和增加超時）
COPY requirements.txt .
RUN pip install --no-cache-dir --timeout 100 -r requirements.txt && \
    pip cache purge && \
    rm -rf /tmp/* /var/tmp/*

# 預加載常用模型（防止首次運行時下載）但減少層大小
RUN mkdir -p /root/.cache/torch/sentence_transformers && \
    python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')" && \
    rm -rf /root/.cache/pip

# 僅複製必要文件，全部在一個層中，減少總層數
COPY app ./app
COPY database_function ./database_function
COPY n8n_booking_schemas ./n8n_booking_schemas
COPY main.py ./ 
COPY setup.py ./

# 創建並初始化向量存儲目錄（避免運行時創建）
RUN mkdir -p /app/vector_store

# 設定環境變數
ENV PYTHONUNBUFFERED=1
ENV PORT=8000

# 暴露 API 服務的埠
EXPOSE 8000

# 啟動 API 服務
CMD ["python", "main.py"]