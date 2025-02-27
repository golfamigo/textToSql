import unittest
from uuid import UUID, uuid4
from datetime import datetime, timedelta, date, time
from pydantic import ValidationError, BaseModel, Field
import sys
import os
import json
from typing import List, Dict, Optional

# Add the app directory to the path to import the models
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from textToSql.app.models.users import UserModel, UserRole
from textToSql.app.models.bookings import BookingModel, BookingStatus
from textToSql.app.models.services import ServiceModel
from textToSql.app.models.time_periods import TimePeriodModel, WeekDay
from textToSql.app.models.query_history import QueryHistoryModel


class CustomTestModel(BaseModel):
    """用於測試的自定義模型"""
    name: str
    value: int


class TestNestedModels(unittest.TestCase):
    """測試嵌套模型驗證"""

    def setUp(self):
        """設置測試數據"""
        self.valid_user_data = {
            "id": uuid4(),
            "business_id": uuid4(),
            "email": "test@example.com",
            "name": "測試使用者",
            "phone": "0912345678",
            "role": "staff",
            "is_active": True,
            "profile_data": {
                "address": "臺北市測試路123號",
                "preferences": {
                    "language": "zh-TW",
                    "theme": "dark",
                    "notifications": True
                },
                "skills": ["hair", "nails", "makeup"]
            },
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        }

    def test_nested_json_data(self):
        """測試嵌套的JSON數據"""
        user = UserModel(**self.valid_user_data)
        self.assertEqual(user.profile_data["preferences"]["language"], "zh-TW")
        self.assertEqual(user.profile_data["skills"][0], "hair")

    def test_modify_nested_data(self):
        """測試修改嵌套數據後的驗證"""
        user = UserModel(**self.valid_user_data)
        
        # 修改嵌套數據
        user_dict = user.model_dump()
        user_dict["profile_data"]["preferences"]["language"] = "en-US"
        
        updated_user = UserModel(**user_dict)
        self.assertEqual(updated_user.profile_data["preferences"]["language"], "en-US")


class TestComplexValidators(unittest.TestCase):
    """測試複雜的驗證邏輯"""

    def setUp(self):
        """設置測試數據"""
        self.business_id = uuid4()
        self.service_id = uuid4()
        self.period_id = uuid4()
        self.start_time = datetime.now().replace(microsecond=0)
        self.end_time = self.start_time + timedelta(hours=1)
        
        self.valid_booking_data = {
            "id": uuid4(),
            "business_id": self.business_id,
            "customer_id": uuid4(),
            "service_id": self.service_id,
            "staff_id": uuid4(),
            "period_id": self.period_id,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "status": "confirmed",
            "customer_notes": "測試備註",
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        }

    def test_booking_time_range(self):
        """測試預約時間範圍驗證"""
        booking = BookingModel(**self.valid_booking_data)
        self.assertEqual(booking.start_time, self.start_time)
        self.assertEqual(booking.end_time, self.end_time)
        
        # 計算預約持續時間
        duration = (booking.end_time - booking.start_time).total_seconds() / 60
        self.assertEqual(duration, 60)  # 應為60分鐘

    def test_booking_status_transition(self):
        """測試預約狀態轉換邏輯"""
        # 創建一個待確認的預約
        pending_data = self.valid_booking_data.copy()
        pending_data["status"] = "pending"
        pending_booking = BookingModel(**pending_data)
        
        # 確認預約
        confirmed_data = pending_booking.model_dump()
        confirmed_data["status"] = "confirmed"
        confirmed_booking = BookingModel(**confirmed_data)
        self.assertEqual(confirmed_booking.status, BookingStatus.CONFIRMED)
        
        # 完成預約
        completed_data = confirmed_booking.model_dump()
        completed_data["status"] = "completed"
        completed_booking = BookingModel(**completed_data)
        self.assertEqual(completed_booking.status, BookingStatus.COMPLETED)
        
        # 取消預約
        cancelled_data = pending_booking.model_dump()
        cancelled_data["status"] = "cancelled"
        cancelled_booking = BookingModel(**cancelled_data)
        self.assertEqual(cancelled_booking.status, BookingStatus.CANCELLED)


class TestEdgeCases(unittest.TestCase):
    """測試邊界情況"""

    def test_empty_optional_fields(self):
        """測試可選欄位為空的情況"""
        user_data = {
            "id": uuid4(),
            "business_id": uuid4(),
            "email": "test@example.com",
            "name": "測試使用者",
            "role": "staff",
            "is_active": True
        }
        
        # 沒有提供可選欄位
        user = UserModel(**user_data)
        self.assertIsNone(user.phone)
        self.assertIsNone(user.profile_data)
        self.assertIsNone(user.last_login)

    def test_minimum_required_fields(self):
        """測試只提供必填欄位的情況"""
        service_data = {
            "id": uuid4(),
            "business_id": uuid4(),
            "name": "測試服務",
            "duration": timedelta(minutes=60),  # 必填欄位
            "price": 1000.0  # 必填欄位
        }
        
        # 提供所有必填欄位
        service = ServiceModel(**service_data)
        self.assertEqual(service.name, "測試服務")
        self.assertIsNone(service.description)
        # 檢查默認值
        self.assertTrue(service.is_active)

    def test_null_values(self):
        """測試NULL值的處理"""
        booking_data = {
            "id": uuid4(),
            "business_id": uuid4(),
            "customer_id": uuid4(),
            "service_id": uuid4(),
            "staff_id": None,  # 明確設置為NULL
            "period_id": uuid4(),
            "start_time": datetime.now(),
            "end_time": datetime.now() + timedelta(hours=1),
            "status": "confirmed",
            "customer_notes": None,  # 明確設置為NULL
            "staff_notes": None      # 明確設置為NULL
        }
        
        booking = BookingModel(**booking_data)
        self.assertIsNone(booking.staff_id)
        self.assertIsNone(booking.customer_notes)
        self.assertIsNone(booking.staff_notes)


class TestQueryHistoryModel(unittest.TestCase):
    """查詢歷史模型測試"""

    def setUp(self):
        """設置測試數據"""
        self.valid_query_data = {
            "id": uuid4(),
            "user_query": "顯示所有下週的預約",
            "generated_sql": "SELECT * FROM bookings WHERE start_time BETWEEN '2025-03-03' AND '2025-03-09'",
            "explanation": "此查詢列出下週（2025年3月3日至9日）之間的所有預約記錄。",
            "executed": True,
            "execution_time": 250.5,
            "created_at": datetime.now(),
            "conversation_id": "conv-" + str(uuid4())[:8],
            "parameters": {
                "start_date": "2025-03-03",
                "end_date": "2025-03-09"
            },
            "is_favorite": False,
            "is_template": False
        }

    def test_valid_query_history(self):
        """測試有效的查詢歷史數據"""
        query_history = QueryHistoryModel(**self.valid_query_data)
        self.assertEqual(query_history.user_query, self.valid_query_data["user_query"])
        self.assertEqual(query_history.generated_sql, self.valid_query_data["generated_sql"])
        self.assertEqual(query_history.explanation, self.valid_query_data["explanation"])
        self.assertTrue(query_history.executed)
        self.assertEqual(query_history.execution_time, 250.5)

    def test_query_template_fields(self):
        """測試查詢模板相關欄位"""
        template_data = self.valid_query_data.copy()
        template_data["is_template"] = True
        template_data["template_name"] = "週預約查詢範本"
        template_data["template_description"] = "用於查詢特定週的所有預約"
        template_data["template_tags"] = ["預約", "時間查詢", "週查詢"]
        
        query_history = QueryHistoryModel(**template_data)
        self.assertTrue(query_history.is_template)
        self.assertEqual(query_history.template_name, "週預約查詢範本")
        self.assertEqual(query_history.template_tags, ["預約", "時間查詢", "週查詢"])
        
    def test_serialization(self):
        """測試序列化和反序列化"""
        query_history = QueryHistoryModel(**self.valid_query_data)
        
        # 序列化為JSON
        json_data = query_history.model_dump_json()
        data_dict = json.loads(json_data)
        
        # 驗證序列化後的數據
        self.assertEqual(data_dict["user_query"], self.valid_query_data["user_query"])
        self.assertEqual(data_dict["generated_sql"], self.valid_query_data["generated_sql"])
        
        # 測試默認值是否正確序列化
        self.assertFalse(data_dict["is_favorite"])
        self.assertFalse(data_dict["is_template"])
        self.assertEqual(data_dict["entity_references"], {})
        self.assertEqual(data_dict["template_tags"], [])
        

if __name__ == "__main__":
    unittest.main()