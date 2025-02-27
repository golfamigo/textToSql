from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict, Any
from datetime import datetime, date, timedelta
from uuid import UUID
from .base import BaseDBModel


class ServiceModel(BaseDBModel):
    """服務項目模型"""
    
    business_id: UUID = Field(description="所屬商家ID")
    name: str = Field(description="服務名稱")
    description: Optional[str] = Field(default=None, description="服務描述")
    duration: timedelta = Field(description="服務時長")
    price: float = Field(description="服務價格")
    color: Optional[str] = Field(default=None, description="顯示顏色")
    is_active: bool = Field(default=True, description="是否啟用")
    max_bookings_per_slot: Optional[int] = Field(default=None, description="每個時段最大預約數")
    business_hours_override_id: Optional[UUID] = Field(default=None, description="營業時間覆蓋ID")
    category: Optional[str] = Field(default=None, description="服務類別")
    image_url: Optional[str] = Field(default=None, description="服務圖片URL")
    settings: Optional[Dict[str, Any]] = Field(default=None, description="服務設定")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174002",
                "business_id": "123e4567-e89b-12d3-a456-426614174000",
                "name": "基礎美容護理",
                "description": "深層清潔和基本護理",
                "duration": "PT1H",  # 1小時
                "price": 1800.0,
                "color": "#FF5733",
                "is_active": True
            }
        }
    }