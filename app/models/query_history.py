from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
from uuid import UUID, uuid4
from .base import BaseDBModel


class QueryHistoryModel(BaseDBModel):
    """查詢歷史模型"""
    
    user_query: str = Field(description="用戶的自然語言查詢")
    generated_sql: str = Field(description="生成的 SQL 查詢")
    explanation: str = Field(description="SQL 查詢的解釋")
    executed: bool = Field(default=False, description="是否執行了查詢")
    execution_time: Optional[float] = Field(default=None, description="執行時間（毫秒）")
    error_message: Optional[str] = Field(default=None, description="錯誤訊息，如果有的話")
    
    # 對話支持字段
    conversation_id: Optional[str] = Field(default=None, description="對話ID")
    references_query_id: Optional[str] = Field(default=None, description="參考的查詢ID")
    resolved_query: Optional[str] = Field(default=None, description="解析後的查詢")
    entity_references: Dict[str, Any] = Field(default_factory=dict, description="實體引用")
    
    # 參數化查詢支持
    parameters: Dict[str, Any] = Field(default_factory=dict, description="SQL參數")
    
    # 收藏與模板支持
    is_favorite: bool = Field(default=False, description="是否被收藏")
    is_template: bool = Field(default=False, description="是否作為查詢模板")
    template_name: Optional[str] = Field(default=None, description="模板名稱")
    template_description: Optional[str] = Field(default=None, description="模板描述")
    template_tags: List[str] = Field(default_factory=list, description="模板標籤")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174008",
                "user_query": "列出所有活躍的商家",
                "generated_sql": "SELECT * FROM n8n_booking_businesses WHERE is_active = true;",
                "explanation": "此查詢從商家表中選擇所有活躍的商家。",
                "executed": True,
                "execution_time": 15.7,
                "created_at": "2025-01-15T10:00:00+08:00",
                "conversation_id": "98765432-abcd-5678-efgh-987654321234",
                "resolved_query": "列出所有活躍的商家",
                "is_favorite": False,
                "is_template": True,
                "template_name": "活躍商家查詢",
                "template_description": "查詢所有目前活躍的商家記錄",
                "template_tags": ["商家", "基礎查詢"]
            }
        }
    }


class QueryTemplateModel(BaseDBModel):
    """查詢模板模型"""
    
    name: str = Field(description="模板名稱")
    description: Optional[str] = Field(default=None, description="模板描述")
    user_query: str = Field(description="用戶的自然語言查詢")
    generated_sql: str = Field(description="生成的 SQL 查詢")
    explanation: Optional[str] = Field(default=None, description="SQL 查詢的解釋")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="SQL參數")
    tags: List[str] = Field(default_factory=list, description="模板標籤")
    usage_count: int = Field(default=0, description="使用次數")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174008",
                "name": "活躍商家查詢",
                "description": "查詢所有目前活躍的商家記錄",
                "user_query": "列出所有活躍的商家",
                "generated_sql": "SELECT * FROM n8n_booking_businesses WHERE is_active = true;",
                "explanation": "此查詢從商家表中選擇所有活躍的商家。",
                "parameters": {},
                "tags": ["商家", "基礎查詢"],
                "usage_count": 5,
                "created_at": "2025-01-15T10:00:00+08:00",
                "updated_at": "2025-01-20T15:30:00+08:00"
            }
        }
    }