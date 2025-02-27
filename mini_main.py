import os
import sys
import uvicorn
from fastapi import FastAPI, HTTPException, Query, Depends
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, Any, List, Optional

# 創建模擬模塊
class DummyModule:
    def __getattr__(self, name):
        return lambda *args, **kwargs: None

# 繞過複雜依賴
sys.modules["faiss"] = DummyModule()
sys.modules["sentence_transformers"] = DummyModule()

# 設置基本環境變量
os.environ["DUMMY_KEY"] = "dummy"

# 顯式加載.env文件
from dotenv import load_dotenv
print("正在加載.env文件...")
# 嘗試不同的路徑
possible_paths = ['.env', '../.env', '../../.env']
for path in possible_paths:
    if os.path.exists(path):
        load_dotenv(path)
        print(f"成功從 {path} 加載.env文件")
        break
else:
    print("警告: 找不到.env文件")

# 列印環境變量檢查
for key in ["OPENAI_API_KEY", "ANTHROPIC_API_KEY", "GOOGLE_API_KEY"]:
    value = os.environ.get(key)
    if value:
        print(f"√ 環境變量 {key} 已設置 (長度: {len(value)})")
    else:
        print(f"× 環境變量 {key} 未設置")

# 導入基礎組件
from app.utils.config import settings
from app.models.users import UserModel
from app.schema.schema import db_functions, get_table_schema_description

# 創建簡化版API
app = FastAPI(title="TextToSQL API (簡化版)", description="文本到SQL轉換服務的簡化版API")

# 添加CORS中間件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "TextToSQL API 簡化版已啟動", "status": "ok"}

@app.get("/api/functions", tags=["資料庫"])
def get_functions():
    """獲取所有可用的資料庫函數"""
    return {"functions": list(db_functions.keys())}

@app.get("/api/schema", tags=["資料庫"])
def get_schema():
    """獲取資料庫結構描述"""
    return {"schema": get_table_schema_description()}

class SimplifiedSQLResult:
    """簡化版SQL結果"""
    def __init__(self, sql: str, description: str):
        self.sql = sql
        self.description = description

@app.post("/api/text-to-sql", tags=["轉換"])
def text_to_sql(query: str = Query(..., description="自然語言查詢"),
               model: str = Query("gpt-3.5-turbo", description="使用的模型")):
    """將自然語言轉換為SQL查詢（模擬）"""
    # 這是模擬實現，實際版本會調用LLM生成SQL
    return {
        "query": query,
        "sql": "SELECT * FROM n8n_booking_users WHERE 1=1 -- 這是模擬生成的SQL",
        "description": "這是一個模擬的SQL生成結果。在完整版本中，會使用LLM生成實際的SQL查詢。",
        "model": model
    }

# 運行伺服器
if __name__ == "__main__":
    print("啟動簡化版TextToSQL API...")
    uvicorn.run("mini_main:app", host="0.0.0.0", port=8000, reload=True)