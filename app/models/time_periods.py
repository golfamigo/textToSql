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
    """預約時段模型"""
    
    business_id: UUID = Field(description="所屬商家ID")
    start_time: time = Field(description="開始時間")
    end_time: time = Field(description="結束時間")
    day_of_week: Optional[WeekDay] = Field(default=None, description="星期幾 (1-7，週一至週日)")
    specific_date: Optional[date] = Field(default=None, description="特定日期 (優先於 day_of_week)")
    is_active: bool = Field(default=True, description="是否啟用")
    slot_interval_minutes: int = Field(default=30, description="時段間隔（分鐘）")
    
    @field_validator('end_time')
    def end_time_must_be_after_start_time(cls, v, values):
        """確保結束時間在開始時間之後"""
        if 'start_time' in values.data and v <= values.data['start_time']:
            raise ValueError('結束時間必須晚於開始時間')
        return v
    
    @field_validator('day_of_week', 'specific_date')
    def validate_day_settings(cls, v, values, **kwargs):
        """驗證日期設定"""
        field = kwargs.get('field')
        if field.name == 'specific_date' and v is not None:
            return v
        if field.name == 'day_of_week' and 'specific_date' not in values.data:
            if v is None:
                raise ValueError('必須指定 day_of_week 或 specific_date')
        return v
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174003",
                "business_id": "123e4567-e89b-12d3-a456-426614174000",
                "start_time": "09:00:00",
                "end_time": "17:00:00",
                "day_of_week": 1,  # 週一
                "is_active": True,
                "slot_interval_minutes": 30
            }
        }
    }