from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict, Any, Union
from datetime import datetime, date, time, timedelta
from uuid import UUID


class BaseDBModel(BaseModel):
    """基礎資料庫模型類別"""
    
    id: UUID = Field(description="唯一識別碼")
    created_at: Optional[datetime] = Field(default=None, description="創建時間")
    updated_at: Optional[datetime] = Field(default=None, description="更新時間")
    
    class Config:
        from_attributes = True  # 允許從ORM模型建立