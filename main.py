import uvicorn
from app.api import app
import os
from dotenv import load_dotenv

# 載入環境變數
load_dotenv()

if __name__ == "__main__":
    # 啟動 FastAPI 應用程式
    uvicorn.run(
        "app.api:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", "8000")),
        reload=True
    )