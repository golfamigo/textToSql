#!/usr/bin/env python
"""
簡單的 API 測試演示
這個示例展示如何編寫 API 測試，而不需要完整的應用程序依賴
"""
import unittest
from unittest.mock import MagicMock, patch
import json
import sys
import os


# 創建模擬模塊
class MockResponse:
    def __init__(self, json_data, status_code):
        self.json_data = json_data
        self.status_code = status_code
        
    def json(self):
        return self.json_data


# 模擬 FastAPI 的 TestClient
class MockTestClient:
    def __init__(self, app):
        self.app = app
        
    def get(self, url):
        if url == "/health":
            return MockResponse(
                {
                    "status": "ok",
                    "database": "connected",
                    "models": {
                        "default": "dummy-model",
                        "available": 2,
                        "names": ["dummy-model", "test-model"]
                    }
                },
                200
            )
        elif url == "/api/tables":
            return MockResponse(
                {
                    "tables": ["users", "services", "bookings"]
                },
                200
            )
        return MockResponse({"error": "Not found"}, 404)
    
    def post(self, url, json=None):
        if url == "/api/text-to-sql":
            return MockResponse(
                {
                    "sql": "SELECT * FROM users WHERE email = :email",
                    "explanation": "這個查詢從用戶表中選擇符合條件的用戶",
                    "parameters": {"email": "test@example.com"},
                    "query_id": "test-id"
                },
                200
            )
        return MockResponse({"error": "Not found"}, 404)


# 模擬 app 模塊
sys.modules['app'] = MagicMock()
sys.modules['app.api'] = MagicMock()
sys.modules['app.api'].app = MagicMock()


class TestAPISimple(unittest.TestCase):
    """簡單的 API 測試示例"""
    
    def setUp(self):
        """測試設置"""
        # 創建測試客戶端
        self.client = MockTestClient(sys.modules['app.api'].app)
    
    def test_health_check(self):
        """測試健康檢查端點"""
        response = self.client.get("/health")
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "ok")
        self.assertEqual(data["database"], "connected")
        self.assertEqual(data["models"]["default"], "dummy-model")
    
    def test_get_tables(self):
        """測試獲取所有表名"""
        response = self.client.get("/api/tables")
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data["tables"]), 3)
        self.assertIn("users", data["tables"])
    
    def test_convert_text_to_sql(self):
        """測試文本到SQL轉換端點"""
        request_data = {
            "query": "找到email是test@example.com的用戶",
            "execute": True,
            "model": "test-model",
            "find_similar": True
        }
        response = self.client.post("/api/text-to-sql", json=request_data)
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["sql"], "SELECT * FROM users WHERE email = :email")
        self.assertEqual(data["parameters"]["email"], "test@example.com")


def run_tests():
    """運行測試"""
    print("運行 API 測試示例")
    suite = unittest.TestLoader().loadTestsFromTestCase(TestAPISimple)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    return len(result.errors) + len(result.failures)


if __name__ == "__main__":
    sys.exit(run_tests())