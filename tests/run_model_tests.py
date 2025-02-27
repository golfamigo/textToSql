"""
簡易模型測試執行器
不依賴完整的應用程式配置
"""
import sys
import os
import unittest
import uuid
import re
from datetime import datetime, time, date, timedelta

# 添加父目錄到 Python 路徑
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# 自定義驗證器
from pydantic import BaseModel, Field, field_validator, EmailStr
from typing import Optional, List, Dict, Any, Literal
from enum import Enum

# 使用現有的枚舉定義
from app.models.users import UserRole
from app.models.bookings import BookingStatus
from app.models.time_periods import WeekDay

# 自定義測試模型 (包含必要的驗證器)
class TestUserModel(BaseModel):
    """測試用戶模型"""
    id: uuid.UUID = Field(description="唯一識別碼")
    business_id: uuid.UUID = Field(description="所屬商家ID")
    email: EmailStr = Field(description="使用者信箱")
    name: str = Field(description="使用者名稱")
    phone: Optional[str] = Field(default=None, description="電話號碼")
    role: UserRole = Field(description="使用者角色")
    is_active: bool = Field(default=True, description="是否啟用")
    
    @field_validator('name')
    def name_must_not_be_empty(cls, v):
        if v == "":
            raise ValueError('名稱不能為空')
        return v

class TestBookingModel(BaseModel):
    """測試預約模型"""
    id: uuid.UUID = Field(description="唯一識別碼")
    business_id: uuid.UUID = Field(description="所屬商家ID")
    customer_id: uuid.UUID = Field(description="客戶ID")
    service_id: uuid.UUID = Field(description="服務項目ID")
    period_id: uuid.UUID = Field(description="預約時段ID")
    start_time: datetime = Field(description="預約開始時間")
    end_time: datetime = Field(description="預約結束時間")
    status: BookingStatus = Field(default=BookingStatus.PENDING, description="預約狀態")
    
    @field_validator('end_time')
    def end_time_must_be_after_start_time(cls, v, values):
        """確保結束時間在開始時間之後"""
        if 'start_time' in values.data and v <= values.data['start_time']:
            raise ValueError('結束時間必須晚於開始時間')
        return v

class TestServiceModel(BaseModel):
    """測試服務項目模型"""
    id: uuid.UUID = Field(description="唯一識別碼")
    business_id: uuid.UUID = Field(description="所屬商家ID")
    name: str = Field(description="服務名稱")
    duration: timedelta = Field(description="服務時長")
    price: float = Field(description="服務價格")
    
    @field_validator('price')
    def price_must_be_positive(cls, v):
        """確保價格為正數"""
        if v < 0:
            raise ValueError('價格必須為正數')
        return v
    
    @field_validator('duration')
    def duration_must_be_positive(cls, v):
        """確保時長為正數"""
        if v.total_seconds() <= 0:
            raise ValueError('時長必須大於零')
        return v

class TestTimePeriodModel(BaseModel):
    """測試預約時段模型"""
    id: uuid.UUID = Field(description="唯一識別碼")
    business_id: uuid.UUID = Field(description="所屬商家ID")
    start_time: time = Field(description="開始時間")
    end_time: time = Field(description="結束時間")
    day_of_week: Optional[WeekDay] = Field(default=None, description="星期幾 (1-7，週一至週日)")
    specific_date: Optional[date] = Field(default=None, description="特定日期 (優先於 day_of_week)")
    
    # 使用模型方法進行額外驗證
    def model_post_init(self, __context):
        """模型初始化後進行驗證"""
        # 驗證時間順序
        if self.end_time <= self.start_time:
            raise ValueError('結束時間必須晚於開始時間')
        
        # 驗證日期設定
        if self.specific_date is None and self.day_of_week is None:
            raise ValueError('必須指定 day_of_week 或 specific_date')


class TestUserModelValidation(unittest.TestCase):
    """測試 UserModel 驗證"""

    def test_invalid_email_format(self):
        """測試無效的電子郵件格式"""
        # 準備測試數據
        test_id = uuid.uuid4()
        business_id = uuid.uuid4()
        invalid_email = "invalid-email"  # 無效的電子郵件格式

        # 確認建立實例時會引發錯誤
        with self.assertRaises(Exception) as context:
            TestUserModel(
                id=test_id,
                business_id=business_id,
                email=invalid_email,
                name="測試用戶",
                role=UserRole.STAFF
            )
        
        # 檢查錯誤訊息
        self.assertTrue("email" in str(context.exception).lower())

    def test_invalid_role(self):
        """測試無效的角色值"""
        # 準備測試數據
        test_id = uuid.uuid4()
        business_id = uuid.uuid4()
        
        # 確認建立實例時會引發錯誤
        with self.assertRaises(Exception) as context:
            TestUserModel(
                id=test_id,
                business_id=business_id,
                email="test@example.com",
                name="測試用戶",
                role="invalid_role"  # 無效的角色值
            )
        
        # 檢查錯誤訊息
        self.assertTrue("role" in str(context.exception).lower())


class TestBookingModelValidation(unittest.TestCase):
    """測試 BookingModel 驗證"""

    def test_end_time_before_start_time(self):
        """測試結束時間在開始時間之前的錯誤"""
        # 準備測試數據
        test_id = uuid.uuid4()
        business_id = uuid.uuid4()
        customer_id = uuid.uuid4()
        service_id = uuid.uuid4()
        period_id = uuid.uuid4()
        start_time = datetime(2025, 2, 15, 10, 0)
        end_time = datetime(2025, 2, 15, 9, 0)  # 結束時間在開始時間之前
        
        # 確認建立實例時會引發錯誤
        with self.assertRaises(Exception) as context:
            TestBookingModel(
                id=test_id,
                business_id=business_id,
                customer_id=customer_id,
                service_id=service_id,
                period_id=period_id,
                start_time=start_time,
                end_time=end_time,
                status=BookingStatus.PENDING
            )
        
        # 檢查錯誤訊息
        self.assertTrue("結束時間必須晚於開始時間" in str(context.exception))


class TestServiceModelValidation(unittest.TestCase):
    """測試 ServiceModel 驗證"""

    def test_negative_price(self):
        """測試負數價格"""
        # 準備測試數據
        test_id = uuid.uuid4()
        business_id = uuid.uuid4()
        
        # 確認建立實例時會引發錯誤
        with self.assertRaises(Exception) as context:
            TestServiceModel(
                id=test_id,
                business_id=business_id,
                name="測試服務",
                duration=timedelta(hours=1),
                price=-100  # 負數價格
            )
        
        # 檢查錯誤訊息
        self.assertTrue("價格必須為正數" in str(context.exception))

    def test_zero_duration(self):
        """測試零時長"""
        # 準備測試數據
        test_id = uuid.uuid4()
        business_id = uuid.uuid4()
        
        # 確認建立實例時會引發錯誤
        with self.assertRaises(Exception) as context:
            TestServiceModel(
                id=test_id,
                business_id=business_id,
                name="測試服務",
                duration=timedelta(seconds=0),  # 零時長
                price=100
            )
        
        # 檢查錯誤訊息
        self.assertTrue("時長必須大於零" in str(context.exception))


class TestTimePeriodModelValidation(unittest.TestCase):
    """測試 TimePeriodModel 驗證"""

    def test_missing_date_specification(self):
        """測試缺少日期指定（星期幾或特定日期）"""
        # 準備測試數據
        test_id = uuid.uuid4()
        business_id = uuid.uuid4()
        
        # 確認建立實例時會引發錯誤
        with self.assertRaises(Exception) as context:
            TestTimePeriodModel(
                id=test_id,
                business_id=business_id,
                start_time=time(9, 0),
                end_time=time(17, 0),
                # 未指定 day_of_week 或 specific_date
            )
        
        # 檢查錯誤訊息
        self.assertTrue("必須指定 day_of_week 或 specific_date" in str(context.exception))
        
    def test_end_time_before_start_time(self):
        """測試結束時間在開始時間之前的錯誤"""
        # 準備測試數據
        test_id = uuid.uuid4()
        business_id = uuid.uuid4()
        
        # 確認建立實例時會引發錯誤
        with self.assertRaises(Exception) as context:
            TestTimePeriodModel(
                id=test_id,
                business_id=business_id,
                start_time=time(10, 0),
                end_time=time(9, 0),  # 結束時間在開始時間之前
                day_of_week=WeekDay.MONDAY
            )
        
        # 檢查錯誤訊息
        self.assertTrue("結束時間必須晚於開始時間" in str(context.exception))


if __name__ == '__main__':
    unittest.main()