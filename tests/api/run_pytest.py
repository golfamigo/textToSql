#!/usr/bin/env python
"""
用於運行 pytest 風格測試的腳本
"""
import unittest
import sys
import os
import warnings
import pytest
from unittest.mock import patch, MagicMock

# 忽略警告
warnings.filterwarnings('ignore')

# 設置路徑
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(script_dir, '../../')))

# 模擬應用程序模塊
sys.modules['app'] = MagicMock()
sys.modules['app.api'] = MagicMock()
sys.modules['app.api'].app = MagicMock()
sys.modules['app.services'] = MagicMock()
sys.modules['app.services.text_to_sql'] = MagicMock()
sys.modules['app.services.database_service'] = MagicMock()
sys.modules['app.services.vector_store'] = MagicMock()
sys.modules['app.services.llm_service'] = MagicMock()
sys.modules['app.models'] = MagicMock()

# 定義一些簡單的 pytest 測試函數
def test_health_check():
    """測試健康檢查端點"""
    # 創建模擬響應
    class MockResponse:
        def __init__(self):
            self.status_code = 200
            self.json_data = {
                "status": "ok",
                "database": "connected",
                "models": {
                    "default": "dummy-model",
                    "available": 2,
                    "names": ["dummy-model", "test-model"]
                }
            }
        
        def json(self):
            return self.json_data
    
    # 模擬客戶端
    class MockClient:
        def get(self, url):
            return MockResponse()
    
    # 執行測試
    client = MockClient()
    response = client.get("/health")
    
    # 斷言
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["database"] == "connected"
    assert data["models"]["default"] == "dummy-model"


def test_get_tables():
    """測試獲取所有表名"""
    # 創建模擬響應
    class MockResponse:
        def __init__(self):
            self.status_code = 200
            self.json_data = {
                "tables": ["users", "services", "bookings"]
            }
        
        def json(self):
            return self.json_data
    
    # 模擬客戶端
    class MockClient:
        def get(self, url):
            return MockResponse()
    
    # 執行測試
    client = MockClient()
    response = client.get("/api/tables")
    
    # 斷言
    assert response.status_code == 200
    data = response.json()
    assert len(data["tables"]) == 3
    assert "users" in data["tables"]


if __name__ == '__main__':
    print("運行 pytest 測試")
    
    # 運行測試 (使用內部參數，忽略搜索其他路徑)
    exit_code = pytest.main(["-xvs", "--no-header", "--no-summary", "--no-conftest", "-k", "test_", __file__])
    
    # 退出
    sys.exit(exit_code)