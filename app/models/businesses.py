from pydantic import BaseModel, Field, field_validator
from typing import Optional, Dict, Any
from datetime import datetime, date, timedelta
from uuid import UUID
from .base import BaseDBModel


class BusinessModel(BaseDBModel):
    """商家資訊模型"""
    
    name: str = Field(description="商家名稱")
    description: Optional[str] = Field(default=None, description="商家描述")
    address: Optional[str] = Field(default=None, description="地址")
    contact_email: Optional[str] = Field(default=None, description="聯絡信箱")
    contact_phone: Optional[str] = Field(default=None, description="聯絡電話")
    business_hours: Optional[Dict[str, Any]] = Field(default=None, description="營業時間")
    timezone: str = Field(default="Asia/Taipei", description="時區")
    min_booking_lead_time: Optional[timedelta] = Field(default=None, description="最小預約提前時間")
    owner_id: Optional[UUID] = Field(default=None, description="擁有者ID")
    settings: Optional[Dict[str, Any]] = Field(default=None, description="商家設定")
    subscription_status: Optional[str] = Field(default=None, description="訂閱狀態")
    subscription_end_date: Optional[date] = Field(default=None, description="訂閱截止日期")
    linebot_destination: Optional[str] = Field(default=None, description="Line 機器人目的地")
    
    @field_validator('business_hours', mode='before')
    def validate_business_hours(cls, v):
        """驗證營業時間格式"""
        if v is None:
            return None
        return v
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "name": "美容沙龍示範",
                "description": "專業美容服務",
                "address": "台北市信義區101號",
                "contact_email": "contact@salon.example.com",
                "contact_phone": "02-1234-5678",
                "timezone": "Asia/Taipei"
            }
        }
    }