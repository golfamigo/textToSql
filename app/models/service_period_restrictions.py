from pydantic import Field
from typing import Optional
from datetime import datetime
from uuid import UUID
from .base import BaseDBModel


class ServicePeriodRestrictionModel(BaseDBModel):
    """服務時段限制模型 - 對應 n8n_booking_service_period_restrictions 表"""
    
    service_id: UUID = Field(description="服務ID")
    period_id: UUID = Field(description="時段ID")
    is_allowed: bool = Field(default=True, description="是否允許在該時段預約此服務")
    created_at: Optional[datetime] = Field(default=None, description="創建時間")
    updated_at: Optional[datetime] = Field(default=None, description="更新時間")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174300",
                "service_id": "123e4567-e89b-12d3-a456-426614174002",
                "period_id": "123e4567-e89b-12d3-a456-426614174003",
                "is_allowed": True
            }
        }
    }