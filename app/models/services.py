from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict, Any
from datetime import datetime, date, timedelta
from uuid import UUID
from .base import BaseDBModel


class ServiceModel(BaseDBModel):
    """服務項目模型 - 對應 n8n_booking_services 表"""
    
    business_id: UUID = Field(description="所屬商家ID")
    name: str = Field(description="服務名稱")
    description: Optional[str] = Field(default=None, description="服務描述")
    duration: int = Field(description="服務時長(分鐘)")
    price: Optional[float] = Field(default=None, description="服務價格")
    max_capacity: Optional[int] = Field(default=None, description="最大容量")
    is_active: bool = Field(default=True, description="是否啟用")
    image_url: Optional[str] = Field(default=None, description="服務圖片URL")
    created_at: Optional[datetime] = Field(default=None, description="創建時間")
    updated_at: Optional[datetime] = Field(default=None, description="更新時間")
    business_hours_override_id: Optional[UUID] = Field(default=None, description="營業時間覆蓋ID")
    min_booking_lead_time: Optional[str] = Field(default=None, description="最小預約提前時間")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174002",
                "business_id": "123e4567-e89b-12d3-a456-426614174000",
                "name": "基礎美容護理",
                "description": "深層清潔和基本護理",
                "duration": 60,  # 60分鐘
                "price": 1800.0,
                "max_capacity": 1,
                "is_active": True,
                "min_booking_lead_time": "2 hours"
            }
        }
    }