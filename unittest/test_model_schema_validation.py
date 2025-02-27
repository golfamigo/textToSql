import unittest
from uuid import UUID, uuid4
from datetime import datetime, timedelta, date
from pydantic import ValidationError
import sys
import os
import json
from typing import List, Dict, Any, Optional

# Add the app directory to the path to import the models
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from textToSql.app.models.users import UserModel, UserRole
from textToSql.app.models.bookings import BookingModel, BookingStatus
from textToSql.app.models.services import ServiceModel
from textToSql.app.models.businesses import BusinessModel


class TestModelSerialization(unittest.TestCase):
    """測試模型序列化和反序列化"""

    def setUp(self):
        """設置測試數據"""
        self.user_id = uuid4()
        self.business_id = uuid4()
        self.valid_user_data = {
            "id": self.user_id,
            "business_id": self.business_id,
            "email": "test@example.com",
            "name": "測試使用者",
            "phone": "0912345678",
            "role": "staff",
            "is_active": True,
            "created_at": datetime.now().replace(microsecond=0),
            "updated_at": datetime.now().replace(microsecond=0)
        }

    def test_model_to_dict(self):
        """測試模型轉換為字典"""
        user = UserModel(**self.valid_user_data)
        user_dict = user.model_dump()
        
        self.assertEqual(str(user_dict["id"]), str(self.user_id))
        self.assertEqual(user_dict["email"], "test@example.com")
        self.assertEqual(user_dict["role"], "staff")

    def test_model_to_json(self):
        """測試模型轉換為JSON"""
        user = UserModel(**self.valid_user_data)
        user_json = user.model_dump_json()
        
        # 解析JSON
        user_dict = json.loads(user_json)
        
        self.assertEqual(user_dict["email"], "test@example.com")
        self.assertEqual(user_dict["name"], "測試使用者")
        self.assertEqual(user_dict["role"], "staff")

    def test_json_to_model(self):
        """測試JSON轉換為模型"""
        user = UserModel(**self.valid_user_data)
        user_json = user.model_dump_json()
        
        # 將JSON轉換回模型
        new_user = UserModel.model_validate_json(user_json)
        
        self.assertEqual(str(new_user.id), str(self.user_id))
        self.assertEqual(new_user.email, "test@example.com")
        self.assertEqual(new_user.role, UserRole.STAFF)


class TestSchemaValidation(unittest.TestCase):
    """測試模型的JSON架構驗證"""

    def test_user_model_schema(self):
        """測試UserModel的JSON架構"""
        schema = UserModel.model_json_schema()
        
        # 檢查必要屬性
        self.assertIn("properties", schema)
        self.assertIn("id", schema["properties"])
        self.assertIn("email", schema["properties"])
        self.assertIn("name", schema["properties"])
        self.assertIn("role", schema["properties"])
        
        # 檢查屬性類型
        self.assertEqual(schema["properties"]["email"]["type"], "string")
        self.assertEqual(schema["properties"]["is_active"]["type"], "boolean")
        
        # 檢查必填欄位
        self.assertIn("required", schema)
        self.assertIn("id", schema["required"])
        self.assertIn("business_id", schema["required"])
        self.assertIn("email", schema["required"])
        self.assertIn("name", schema["required"])
        self.assertIn("role", schema["required"])

    def test_booking_model_schema(self):
        """測試BookingModel的JSON架構"""
        schema = BookingModel.model_json_schema()
        
        # 檢查必要屬性
        self.assertIn("properties", schema)
        self.assertIn("start_time", schema["properties"])
        self.assertIn("end_time", schema["properties"])
        self.assertIn("status", schema["properties"])
        
        # 檢查必填欄位
        self.assertIn("required", schema)
        self.assertIn("business_id", schema["required"])
        self.assertIn("customer_id", schema["required"])
        self.assertIn("service_id", schema["required"])
        self.assertIn("period_id", schema["required"])
        self.assertIn("start_time", schema["required"])
        self.assertIn("end_time", schema["required"])


class TestModelExamples(unittest.TestCase):
    """測試模型示例數據"""

    def test_business_model_example(self):
        """測試BusinessModel的示例數據"""
        schema = BusinessModel.model_json_schema()
        
        # Pydantic v2的架構可能與之前版本不同
        # 檢查schema是否包含基本信息
        self.assertIn("properties", schema)
        self.assertIn("title", schema)
        self.assertEqual(schema["title"], "BusinessModel")
        
        # 檢查是否有必要的屬性
        properties = schema["properties"]
        self.assertIn("name", properties)
        self.assertIn("timezone", properties)
        
        # 檢查屬性說明
        self.assertEqual(properties["name"]["description"], "商家名稱")
        self.assertEqual(properties["timezone"]["description"], "時區")

    def test_service_model_example(self):
        """測試ServiceModel的示例數據"""
        schema = ServiceModel.model_json_schema()
        
        # 檢查schema是否包含基本信息
        self.assertIn("properties", schema)
        self.assertIn("title", schema)
        self.assertEqual(schema["title"], "ServiceModel")
        
        # 檢查是否有必要的屬性
        properties = schema["properties"]
        self.assertIn("name", properties)
        self.assertIn("duration", properties)
        self.assertIn("price", properties)
        
        # 檢查屬性說明
        self.assertEqual(properties["name"]["description"], "服務名稱")
        self.assertEqual(properties["duration"]["description"], "服務時長")


class TestDataTypeValidation(unittest.TestCase):
    """測試數據類型驗證"""

    def test_uuid_validation(self):
        """測試UUID欄位驗證"""
        valid_data = {
            "id": uuid4(),
            "business_id": uuid4(),
            "email": "test@example.com",
            "name": "測試使用者",
            "role": "staff"
        }
        
        # 有效的UUID
        user = UserModel(**valid_data)
        self.assertTrue(isinstance(user.id, UUID))
        
        # 無效的UUID格式
        invalid_data = valid_data.copy()
        invalid_data["id"] = "not-a-uuid"
        
        with self.assertRaises(ValidationError):
            UserModel(**invalid_data)
        
        # 使用UUID字符串
        valid_uuid_str = str(uuid4())
        string_data = valid_data.copy()
        string_data["id"] = valid_uuid_str
        
        user = UserModel(**string_data)
        self.assertTrue(isinstance(user.id, UUID))
        self.assertEqual(str(user.id), valid_uuid_str)

    def test_date_time_validation(self):
        """測試日期時間欄位驗證"""
        now = datetime.now().replace(microsecond=0)
        
        booking_data = {
            "id": uuid4(),
            "business_id": uuid4(),
            "customer_id": uuid4(),
            "service_id": uuid4(),
            "period_id": uuid4(),
            "start_time": now,
            "end_time": now + timedelta(hours=1),
            "status": "confirmed"
        }
        
        # 有效的日期時間
        booking = BookingModel(**booking_data)
        self.assertTrue(isinstance(booking.start_time, datetime))
        
        # 使用ISO格式字符串
        string_data = booking_data.copy()
        string_data["start_time"] = now.isoformat()
        string_data["end_time"] = (now + timedelta(hours=1)).isoformat()
        
        booking = BookingModel(**string_data)
        self.assertTrue(isinstance(booking.start_time, datetime))
        
        # 測試日期時間格式
        booking_str = booking.model_dump_json()
        parsed_data = json.loads(booking_str)
        # 檢查序列化後的時間格式是否為ISO格式
        self.assertTrue(isinstance(parsed_data["start_time"], str))
        # ISO格式的字符串應該包含 T
        self.assertIn("T", parsed_data["start_time"])

    def test_enum_validation(self):
        """測試枚舉欄位驗證"""
        user_data = {
            "id": uuid4(),
            "business_id": uuid4(),
            "email": "test@example.com",
            "name": "測試使用者",
            "role": "staff"
        }
        
        # 有效的枚舉值
        user = UserModel(**user_data)
        self.assertEqual(user.role, UserRole.STAFF)
        
        # 無效的枚舉值
        invalid_data = user_data.copy()
        invalid_data["role"] = "invalid_role"
        
        with self.assertRaises(ValidationError):
            UserModel(**invalid_data)


if __name__ == "__main__":
    unittest.main()