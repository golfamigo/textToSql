from pydantic import Field, field_validator
from typing import Optional, Literal
from datetime import datetime, date, time
from uuid import UUID
from enum import Enum
from .base import BaseDBModel


class AvailabilityType(str, Enum):
    """可用性類型枚舉"""
    AVAILABLE = "available"
    UNAVAILABLE = "unavailable"


class StaffAvailabilityModel(BaseDBModel):
    """員工可用時間模型 - 對應 n8n_booking_staff_availability 表"""
    
    staff_id: UUID = Field(description="員工ID")
    business_id: UUID = Field(description="商家ID")
    day_of_week: Optional[int] = Field(default=None, description="星期幾 (0=星期日, 1=星期一, ..., 6=星期六)")
    specific_date: Optional[date] = Field(default=None, description="特定日期")
    start_time: time = Field(description="開始時間")
    end_time: time = Field(description="結束時間")
    is_recurring: bool = Field(default=True, description="是否週期性")
    availability_type: AvailabilityType = Field(default=AvailabilityType.AVAILABLE, description="可用性類型")
    notes: Optional[str] = Field(default=None, description="備註")
    created_at: Optional[datetime] = Field(default=None, description="創建時間")
    updated_at: Optional[datetime] = Field(default=None, description="更新時間")
    
    @field_validator('end_time')
    def end_time_must_be_after_start_time(cls, v, values):
        """確保結束時間在開始時間之後"""
        if v and 'start_time' in values.data and values.data['start_time'] and v <= values.data['start_time']:
            raise ValueError('結束時間必須晚於開始時間')
        return v
    
    @field_validator('day_of_week', 'specific_date')
    def validate_date_settings(cls, v, values, **kwargs):
        """確保至少指定了星期幾或特定日期之一"""
        field = kwargs.get('field')
        if field.name == 'specific_date' and v is not None:
            return v
            
        if field.name == 'day_of_week' and v is not None:
            if v < 0 or v > 6:
                raise ValueError('星期幾必須在 0-6 範圍內 (0=星期日, 6=星期六)')
            return v
            
        # 確保兩個欄位其中一個有值
        other_field = 'specific_date' if field.name == 'day_of_week' else 'day_of_week'
        if other_field not in values.data or values.data[other_field] is None:
            if v is None:
                raise ValueError('必須指定 day_of_week 或 specific_date')
                
        return v
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174200",
                "staff_id": "123e4567-e89b-12d3-a456-426614174001",
                "business_id": "123e4567-e89b-12d3-a456-426614174000",
                "day_of_week": 1,
                "start_time": "09:00:00",
                "end_time": "17:00:00",
                "is_recurring": True,
                "availability_type": "available",
                "notes": "每週一正常工作時間"
            }
        }
    }