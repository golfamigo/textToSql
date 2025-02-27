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
    """預約模型 - 對應 n8n_booking_bookings 表"""
    
    booking_created_at: Optional[datetime] = Field(default=None, description="預約創建時間")
    booking_date: date = Field(description="預約日期")
    booking_duration: Optional[str] = Field(default=None, description="預約時長 (interval 格式，如 '1 hour', '30 minutes')")
    booking_start_time: time = Field(description="預約開始時間")
    business_id: UUID = Field(description="所屬商家ID")
    customer_email: str = Field(description="客戶電子郵件")
    customer_name: str = Field(description="客戶名稱")
    customer_notes: Optional[str] = Field(default=None, description="客戶備註")
    customer_phone: Optional[str] = Field(default=None, description="客戶電話")
    line_user_id: Optional[str] = Field(default=None, description="Line用戶ID")
    notes: Optional[str] = Field(default=None, description="備註")
    notification_status: Optional[Dict[str, Any]] = Field(default=None, description="通知狀態")
    number_of_people: Optional[int] = Field(default=1, description="預約人數")
    period_id: Optional[UUID] = Field(default=None, description="預約時段ID")
    service_id: UUID = Field(description="服務項目ID")
    staff_id: Optional[UUID] = Field(default=None, description="服務人員ID")
    status: str = Field(default="confirmed", description="預約狀態")
    updated_at: Optional[datetime] = Field(default=None, description="更新時間")
    user_id: Optional[UUID] = Field(default=None, description="用戶ID")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174004",
                "business_id": "123e4567-e89b-12d3-a456-426614174000",
                "booking_date": "2025-01-15",
                "booking_start_time": "10:00:00",
                "booking_duration": "1 hour",
                "service_id": "123e4567-e89b-12d3-a456-426614174002",
                "staff_id": "123e4567-e89b-12d3-a456-426614174005",
                "period_id": "123e4567-e89b-12d3-a456-426614174003",
                "customer_name": "王小明",
                "customer_email": "example@email.com",
                "customer_phone": "0912345678",
                "status": "confirmed",
                "number_of_people": 1
            }
        }
    }


class BookingHistoryModel(BaseDBModel):
    """預約狀態歷史記錄模型 - 對應 n8n_booking_history 表"""
    
    booking_id: UUID = Field(description="預約ID")
    previous_status: Optional[str] = Field(description="之前的狀態")
    new_status: str = Field(description="新狀態")
    changed_by: Optional[UUID] = Field(default=None, description="變更者ID")
    reason: Optional[str] = Field(default=None, description="變更原因")
    created_at: Optional[datetime] = Field(default=None, description="創建時間")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174099",
                "booking_id": "123e4567-e89b-12d3-a456-426614174004",
                "previous_status": "pending",
                "new_status": "confirmed",
                "changed_by": "123e4567-e89b-12d3-a456-426614174005",
                "reason": "客戶已確認預約",
                "created_at": "2025-01-15T10:30:00+08:00"
            }
        }
    }