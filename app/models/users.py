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
    """使用者模型"""
    
    business_id: UUID = Field(description="所屬商家ID")
    email: str = Field(description="使用者信箱")
    name: str = Field(description="使用者名稱")
    phone: Optional[str] = Field(default=None, description="電話號碼")
    role: UserRole = Field(description="使用者角色")
    is_active: bool = Field(default=True, description="是否啟用")
    password_hash: Optional[str] = Field(default=None, description="密碼雜湊")
    profile_data: Optional[Dict[str, Any]] = Field(default=None, description="個人資料")
    last_login: Optional[datetime] = Field(default=None, description="最後登入時間")
    email_verified: bool = Field(default=False, description="電子郵件是否已驗證")
    line_user_id: Optional[str] = Field(default=None, description="Line 使用者 ID")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174001",
                "business_id": "123e4567-e89b-12d3-a456-426614174000",
                "email": "user@example.com",
                "name": "張小明",
                "phone": "0912345678",
                "role": "staff",
                "is_active": True
            }
        }
    }