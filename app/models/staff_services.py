from pydantic import Field
from typing import Optional
from datetime import datetime
from uuid import UUID
from .base import BaseDBModel


class StaffServiceModel(BaseDBModel):
    """員工服務關聯模型 - 對應 n8n_booking_staff_services 表"""
    
    staff_id: UUID = Field(description="員工ID")
    service_id: UUID = Field(description="服務ID")
    is_primary: bool = Field(default=False, description="是否為主要服務")
    proficiency_level: Optional[int] = Field(default=None, description="熟練程度")
    notes: Optional[str] = Field(default=None, description="備註")
    created_at: Optional[datetime] = Field(default=None, description="創建時間")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174100",
                "staff_id": "123e4567-e89b-12d3-a456-426614174001",
                "service_id": "123e4567-e89b-12d3-a456-426614174002",
                "is_primary": True,
                "proficiency_level": 5,
                "notes": "特別專精此項服務"
            }
        }
    }