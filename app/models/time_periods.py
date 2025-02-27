from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from datetime import datetime, date, time
from uuid import UUID
from enum import Enum
from .base import BaseDBModel


class WeekDay(int, Enum):
    """星期幾枚舉"""
    MONDAY = 1
    TUESDAY = 2
    WEDNESDAY = 3
    THURSDAY = 4
    FRIDAY = 5
    SATURDAY = 6
    SUNDAY = 7


class TimePeriodModel(BaseDBModel):
    """預約時段模型 - 對應 n8n_booking_time_periods 表"""
    
    business_id: UUID = Field(description="所屬商家ID")
    name: str = Field(description="時段名稱")
    start_time: Optional[time] = Field(default=None, description="開始時間")
    end_time: Optional[time] = Field(default=None, description="結束時間")
    start_minutes: Optional[int] = Field(default=None, description="開始分鐘數")
    end_minutes: Optional[int] = Field(default=None, description="結束分鐘數")
    max_capacity: Optional[int] = Field(default=None, description="最大容量")
    is_active: bool = Field(default=True, description="是否啟用")
    
    @field_validator('end_time')
    def end_time_must_be_after_start_time(cls, v, values):
        """確保結束時間在開始時間之後"""
        if v and 'start_time' in values.data and values.data['start_time'] and v <= values.data['start_time']:
            raise ValueError('結束時間必須晚於開始時間')
        return v
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174003",
                "business_id": "123e4567-e89b-12d3-a456-426614174000",
                "name": "上午",
                "start_time": "09:00:00",
                "end_time": "12:00:00",
                "start_minutes": 540,  # 9小時 = 540分鐘
                "end_minutes": 720,    # 12小時 = 720分鐘
                "max_capacity": 8,
                "is_active": True
            }
        }
    }