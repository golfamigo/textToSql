"""
模擬TextToSQL功能測試
這個測試不依賴實際的TextToSQL模組，而是模擬其行為
"""
import unittest
from unittest.mock import MagicMock
import json


class MockTextToSQL:
    """模擬TextToSQL服務"""
    
    def __init__(self):
        """初始化"""
        self.llm_service = MagicMock()
        self.history_service = MagicMock()
        self.db_service = MagicMock()
    
    def generate_sql(self, query):
        """模擬生成SQL的功能"""
        if "商家" in query:
            return "SELECT * FROM businesses WHERE name LIKE '%商家%'"
        elif "預約" in query:
            return "SELECT * FROM bookings WHERE customer_id = :customer_id"
        elif "服務" in query:
            return "SELECT * FROM services WHERE is_active = true"
        else:
            return "SELECT 1"  # 默認查詢
    
    def execute_query(self, sql, params=None):
        """模擬執行查詢的功能"""
        if "businesses" in sql:
            return {"columns": ["id", "name"], "rows": [[1, "測試商家"], [2, "示例店鋪"]]}
        elif "bookings" in sql:
            return {"columns": ["id", "date"], "rows": [[101, "2025-01-15"], [102, "2025-01-16"]]}
        elif "services" in sql:
            return {"columns": ["id", "name", "price"], "rows": [[1, "基礎服務", 100], [2, "高級服務", 200]]}
        else:
            return {"columns": ["result"], "rows": [[1]]}


class TestMockTextToSQL(unittest.TestCase):
    """測試模擬的TextToSQL功能"""
    
    def setUp(self):
        """設置測試環境"""
        self.text_to_sql = MockTextToSQL()
    
    def test_generate_sql(self):
        """測試生成SQL功能"""
        # 測試不同類型的查詢
        business_sql = self.text_to_sql.generate_sql("列出所有商家")
        self.assertTrue("businesses" in business_sql)
        
        booking_sql = self.text_to_sql.generate_sql("查詢用戶的預約記錄")
        self.assertTrue("bookings" in booking_sql)
        
        service_sql = self.text_to_sql.generate_sql("查詢可用的服務")
        self.assertTrue("services" in service_sql)
        
        default_sql = self.text_to_sql.generate_sql("隨機查詢")
        self.assertEqual(default_sql, "SELECT 1")
    
    def test_execute_query(self):
        """測試執行查詢功能"""
        # 測試商家查詢
        business_result = self.text_to_sql.execute_query("SELECT * FROM businesses")
        self.assertEqual(business_result["columns"], ["id", "name"])
        self.assertEqual(len(business_result["rows"]), 2)
        
        # 測試預約查詢
        booking_result = self.text_to_sql.execute_query("SELECT * FROM bookings")
        self.assertEqual(booking_result["columns"], ["id", "date"])
        self.assertEqual(len(booking_result["rows"]), 2)
        
        # 測試服務查詢
        service_result = self.text_to_sql.execute_query("SELECT * FROM services")
        self.assertEqual(service_result["columns"], ["id", "name", "price"])
        self.assertEqual(len(service_result["rows"]), 2)
    
    def test_end_to_end(self):
        """測試端到端流程"""
        # 用戶輸入 -> 生成SQL -> 執行查詢 -> 返回結果
        user_query = "查詢所有商家信息"
        
        # 生成SQL
        generated_sql = self.text_to_sql.generate_sql(user_query)
        self.assertTrue("businesses" in generated_sql)
        
        # 執行查詢
        result = self.text_to_sql.execute_query(generated_sql)
        
        # 驗證結果
        self.assertIsNotNone(result)
        self.assertEqual(result["columns"], ["id", "name"])
        self.assertEqual(len(result["rows"]), 2)
        
        # 檢查結果中是否包含預期的商家
        has_test_business = False
        for row in result["rows"]:
            if "測試商家" in row:
                has_test_business = True
                break
                
        self.assertTrue(has_test_business, "結果中應該包含'測試商家'")


if __name__ == '__main__':
    unittest.main()