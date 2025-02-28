import uvicorn
import os
from dotenv import load_dotenv
from app.core.logging import setup_logging, get_logger

# 設置日誌
setup_logging()
logger = get_logger(__name__)

# 載入環境變數
load_dotenv()

if __name__ == "__main__":
    # 獲取端口
    port = int(os.getenv("PORT", "8000"))
    
    logger.info(f"啟動TextToSQL服務，端口: {port}")
    
    # 啟動 FastAPI 應用程式
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=port,
        reload=True
    )