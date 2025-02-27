from pydantic import BaseModel, Field, field_validator
from typing import Optional, Dict, Any
from datetime import datetime, date, time
from uuid import UUID
from enum import Enum
from .base import BaseDBModel


class BookingStatus(str, Enum):
    """預約狀態枚舉"""
    PENDING = "pending"
    CONFIRMED = "confirmed"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    NO_SHOW = "no_show"


class BookingModel(BaseDBModel):
    """預約模型"""
    
    business_id: UUID = Field(description="所屬商家ID")
    customer_id: UUID = Field(description="客戶ID")
    service_id: UUID = Field(description="服務項目ID")
    staff_id: Optional[UUID] = Field(default=None, description="服務人員ID")
    period_id: UUID = Field(description="預約時段ID")
    start_time: datetime = Field(description="預約開始時間")
    end_time: datetime = Field(description="預約結束時間")
    status: BookingStatus = Field(default=BookingStatus.PENDING, description="預約狀態")
    customer_notes: Optional[str] = Field(default=None, description="客戶備註")
    staff_notes: Optional[str] = Field(default=None, description="員工備註")
    notification_status: Optional[Dict[str, Any]] = Field(default=None, description="通知狀態")
    
    @field_validator('end_time')
    def end_time_must_be_after_start_time(cls, v, values):
        """確保結束時間在開始時間之後"""
        if 'start_time' in values.data and v <= values.data['start_time']:
            raise ValueError('結束時間必須晚於開始時間')
        return v
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174004",
                "business_id": "123e4567-e89b-12d3-a456-426614174000",
                "customer_id": "123e4567-e89b-12d3-a456-426614174001",
                "service_id": "123e4567-e89b-12d3-a456-426614174002",
                "staff_id": "123e4567-e89b-12d3-a456-426614174005",
                "period_id": "123e4567-e89b-12d3-a456-426614174003",
                "start_time": "2025-01-15T10:00:00+08:00",
                "end_time": "2025-01-15T11:00:00+08:00",
                "status": "confirmed"
            }
        }
    }