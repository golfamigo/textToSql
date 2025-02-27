from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict, Any, Literal
from datetime import datetime, date
from uuid import UUID
from enum import Enum
from .base import BaseDBModel


class UserRole(str, Enum):
    """使用者角色枚舉"""
    ADMIN = "admin"
    STAFF = "staff"
    CUSTOMER = "customer"


class UserModel(BaseDBModel):
    """使用者模型 - 對應 n8n_booking_users 表"""
    
    name: str = Field(description="使用者名稱")
    email: Optional[str] = Field(default=None, description="使用者信箱")
    phone: Optional[str] = Field(default=None, description="電話號碼")
    line_user_id: Optional[str] = Field(default=None, description="Line 使用者 ID")
    role: UserRole = Field(description="使用者角色")
    password_hash: Optional[str] = Field(default=None, description="密碼雜湊")
    business_id: Optional[UUID] = Field(default=None, description="所屬商家ID")
    is_active: bool = Field(default=True, description="是否啟用")
    notes: Optional[str] = Field(default=None, description="備註")
    settings: Optional[Dict[str, Any]] = Field(default=None, description="使用者設定")
    created_at: Optional[datetime] = Field(default=None, description="創建時間")
    updated_at: Optional[datetime] = Field(default=None, description="更新時間")
    last_login: Optional[datetime] = Field(default=None, description="最後登入時間")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174001",
                "name": "張小明",
                "email": "user@example.com",
                "phone": "0912345678",
                "role": "staff",
                "business_id": "123e4567-e89b-12d3-a456-426614174000",
                "is_active": True,
                "line_user_id": "U1234567890abcdef1234567890abcdef",
                "notes": "資深造型師",
                "settings": {"notifications": {"email": true, "sms": false}}
            }
        }
    }