from fastapi import FastAPI, HTTPException, Query, Depends, Body
from pydantic import BaseModel, Field, validator
from .services import (
    TextToSQLService, 
    SQLResult, 
    DatabaseService, 
    llm_service, 
    LLMResponse
)
from .models import QueryHistoryModel
from .utils import settings
import logging
from typing import List, Optional, Dict, Any, Union
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# 設定日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 建立應用
app = FastAPI(
    title="TextToSQL API",
    description="將自然語言轉換為 SQL 查詢的 API",
    version="0.1.0"
)

# 允許跨域請求
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 初始化服務
text_to_sql_service = TextToSQLService()
db_service = DatabaseService()


class QueryRequest(BaseModel):
    """查詢請求模型"""
    query: str = Field(..., description="自然語言查詢")
    execute: bool = Field(default=False, description="是否執行生成的查詢")
    model: Optional[str] = Field(default=None, description="使用的模型名稱")
    session_id: Optional[str] = Field(default=None, description="會話ID，用於對話上下文管理")
    
    @validator('model')
    def validate_model(cls, v):
        if v is not None and v not in settings.models:
            available_models = list(settings.models.keys())
            raise ValueError(f"未知的模型: {v}。可用模型: {available_models}")
        return v


class ModelRatingRequest(BaseModel):
    """模型評分請求"""
    request_id: str = Field(..., description="請求ID")
    score: float = Field(..., description="評分 (1-5)")
    reason: Optional[str] = Field(default=None, description="評分原因")
    
    @validator('score')
    def validate_score(cls, v):
        if v < 1 or v > 5:
            raise ValueError("評分必須在 1-5 之間")
        return v


class TableSchemaResponse(BaseModel):
    """表結構響應模型"""
    table_name: str
    columns: List[Dict[str, Any]]
    primary_keys: List[str]
    foreign_keys: List[Dict[str, Any]]


class SQLResultResponse(SQLResult):
    """SQL結果響應模型"""
    parameters: Optional[Dict[str, Any]] = Field(default=None, description="SQL參數")


@app.post("/api/text-to-sql", response_model=SQLResultResponse)
async def convert_text_to_sql(request: QueryRequest):
    """
    將自然語言轉換為 SQL 查詢
    
    - 如果 execute=True，將執行生成的查詢並返回結果
    - 可以指定使用的模型，默認使用設定中的默認模型
    """
    try:
        logger.info(f"接收到查詢: {request.query}, execute={request.execute}, model={request.model or settings.default_model}")
        
        # 臨時設置默認模型
        original_default = settings.default_model
        if request.model:
            settings.default_model = request.model
            
        # 執行查詢
        result = text_to_sql_service.text_to_sql(
            query=request.query, 
            session_id=request.session_id,
            execute=request.execute
        )
        
        # 恢復默認模型
        if request.model:
            settings.default_model = original_default
            
        return result
    except Exception as e:
        logger.error(f"處理查詢時發生錯誤: {e}")
        raise HTTPException(status_code=500, detail=f"處理查詢時發生錯誤: {str(e)}")


@app.get("/api/history", response_model=List[QueryHistoryModel])
async def get_query_history(
    limit: int = Query(20, description="返回結果數量限制"),
    offset: int = Query(0, description="偏移量")
):
    """獲取查詢歷史記錄"""
    try:
        history = text_to_sql_service.get_history(limit, offset)
        return history
    except Exception as e:
        logger.error(f"獲取查詢歷史時發生錯誤: {e}")
        raise HTTPException(status_code=500, detail=f"獲取查詢歷史時發生錯誤: {str(e)}")


@app.post("/api/execute-sql")
async def execute_sql(sql: str = Query(..., description="要執行的 SQL 查詢")):
    """
    直接執行 SQL 查詢
    
    注意：僅允許執行只讀查詢
    """
    try:
        logger.info(f"執行 SQL 查詢: {sql}")
        
        # 檢查 SQL 安全性
        is_safe, reason = db_service.is_safe_query(sql)
        if not is_safe:
            raise HTTPException(status_code=400, detail=reason)
        
        # 執行查詢
        result = text_to_sql_service.execute_sql(sql)
        
        if result.error:
            logger.error(f"SQL 查詢執行錯誤: {result.error}")
            return JSONResponse(
                status_code=400,
                content={"error": result.error}
            )
        
        return result.to_dict()
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"執行 SQL 查詢時發生錯誤: {e}")
        raise HTTPException(status_code=500, detail=f"執行 SQL 查詢時發生錯誤: {str(e)}")


@app.get("/api/tables")
async def get_tables():
    """獲取所有表名"""
    try:
        tables = db_service.get_tables()
        return {"tables": tables}
    except Exception as e:
        logger.error(f"獲取表名時發生錯誤: {e}")
        raise HTTPException(status_code=500, detail=f"獲取表名時發生錯誤: {str(e)}")


@app.get("/api/table/{table_name}/schema", response_model=TableSchemaResponse)
async def get_table_schema(table_name: str):
    """獲取表結構"""
    try:
        schema = db_service.get_table_schema(table_name)
        if "error" in schema:
            raise HTTPException(status_code=400, detail=schema["error"])
        return schema
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"獲取表結構時發生錯誤: {e}")
        raise HTTPException(status_code=500, detail=f"獲取表結構時發生錯誤: {str(e)}")




@app.get("/api/models")
async def get_available_models():
    """獲取可用的模型列表"""
    try:
        models = llm_service.get_available_models()
        default_model = settings.default_model
        return {
            "models": models,
            "default": default_model
        }
    except Exception as e:
        logger.error(f"獲取模型列表時發生錯誤: {e}")
        raise HTTPException(status_code=500, detail=f"獲取模型列表時發生錯誤: {str(e)}")


@app.post("/api/rate-model")
async def rate_model(request: ModelRatingRequest):
    """為模型回應評分"""
    try:
        # 從 request_id 獲取回應
        # 目前這個功能需要改進，應該實現一個臨時存儲來保存 request_id -> response 的映射
        # 這裡只是一個示例
        dummy_response = LLMResponse(
            content="",
            model=settings.default_model,
            request_id=request.request_id,
        )
        
        # 添加評分
        llm_service.rate_response(
            response=dummy_response,
            score=request.score,
            reason=request.reason
        )
        
        return {"message": "評分已接收"}
    except Exception as e:
        logger.error(f"評分失敗: {e}")
        raise HTTPException(status_code=500, detail=f"評分失敗: {str(e)}")


@app.get("/api/model-performance")
async def get_model_performance(model_name: Optional[str] = None):
    """獲取模型性能統計"""
    try:
        performance = llm_service.get_model_performance(model_name)
        return performance
    except Exception as e:
        logger.error(f"獲取模型性能失敗: {e}")
        raise HTTPException(status_code=500, detail=f"獲取模型性能失敗: {str(e)}")


@app.get("/health")
async def health_check():
    """健康檢查端點"""
    db_status = "connected" if db_service.is_connected() else "disconnected"
    models = llm_service.get_available_models()
    
    return {
        "status": "ok",
        "database": db_status,
        "models": {
            "default": settings.default_model,
            "available": len(models),
            "names": models[:3] + (["..."] if len(models) > 3 else [])
        }
    }