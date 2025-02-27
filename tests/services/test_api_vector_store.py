import unittest
from unittest.mock import patch, MagicMock
import json
from fastapi.testclient import TestClient
from fastapi import FastAPI
import sys
import os

# 添加專用的 mock_settings 來繞過配置問題
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)
import mock_settings

# 在導入其他模塊前先模擬設置
sys.modules['app.utils.config'] = mock_settings

# 假設 API 在 app.api 中
from app.api import app
from app.services.vector_store import VectorStore


class TestVectorStoreAPI(unittest.TestCase):
    def setUp(self):
        # 創建測試客戶端
        self.client = TestClient(app)
        
        # 模擬向量存儲
        self.vector_store_patcher = patch('app.api.vector_store')
        self.mock_vector_store = self.vector_store_patcher.start()
    
    def tearDown(self):
        # 停止所有模擬
        self.vector_store_patcher.stop()
    
    def test_get_vector_store_stats(self):
        """測試獲取向量存儲統計信息"""
        # 配置模擬返回值
        self.mock_vector_store.get_count.return_value = 10
        
        # 發送請求
        response = self.client.get("/api/vector-store/stats")
        
        # 驗證結果
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["count"], 10)
    
    def test_search_vector_store(self):
        """測試搜索向量存儲"""
        # 配置模擬返回值
        mock_results = [
            {
                "id": "test-id-1",
                "query": "列出所有用戶",
                "sql": "SELECT * FROM n8n_booking_users",
                "timestamp": "2023-01-01T12:00:00",
                "similarity": 0.85,
                "metadata": {}
            },
            {
                "id": "test-id-2",
                "query": "查詢用戶資料",
                "sql": "SELECT * FROM n8n_booking_users WHERE id = :id",
                "timestamp": "2023-01-02T12:00:00",
                "similarity": 0.75,
                "metadata": {"executed": True}
            }
        ]
        self.mock_vector_store.search_similar.return_value = mock_results
        
        # 發送請求
        response = self.client.get("/api/vector-store/search?query=用戶資料&limit=5")
        
        # 驗證結果
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data), 2)
        self.assertEqual(data[0]["query"], "列出所有用戶")
        self.assertEqual(data[1]["query"], "查詢用戶資料")
        
        # 驗證調用參數
        self.mock_vector_store.search_similar.assert_called_once_with("用戶資料", k=5)
    
    def test_clear_vector_store(self):
        """測試清除向量存儲"""
        # 配置模擬
        self.mock_vector_store.clear.return_value = None
        
        # 發送請求
        response = self.client.post("/api/vector-store/clear")
        
        # 驗證結果
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["message"], "向量存儲已清除")
        
        # 驗證方法調用
        self.mock_vector_store.clear.assert_called_once()
    
    def test_add_query_to_vector_store(self):
        """測試添加查詢到向量存儲"""
        # 配置模擬返回值
        self.mock_vector_store.add_query.return_value = "test-id-3"
        
        # 請求數據
        request_data = {
            "query": "測試添加查詢",
            "sql": "SELECT * FROM test_table",
            "metadata": {"test": True}
        }
        
        # 發送請求
        response = self.client.post(
            "/api/vector-store/add",
            json=request_data
        )
        
        # 驗證結果
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["id"], "test-id-3")
        
        # 驗證調用參數
        self.mock_vector_store.add_query.assert_called_once_with(
            "測試添加查詢", 
            "SELECT * FROM test_table",
            {"test": True}
        )
    
    def test_search_with_error(self):
        """測試搜索時出錯的情況"""
        # 配置模擬拋出異常
        self.mock_vector_store.search_similar.side_effect = Exception("測試錯誤")
        
        # 發送請求
        response = self.client.get("/api/vector-store/search?query=錯誤查詢")
        
        # 驗證結果
        self.assertEqual(response.status_code, 500)
        data = response.json()
        self.assertIn("error", data)
        self.assertIn("測試錯誤", data["error"])
    
    def test_clear_with_error(self):
        """測試清除時出錯的情況"""
        # 配置模擬拋出異常
        self.mock_vector_store.clear.side_effect = Exception("清除錯誤")
        
        # 發送請求
        response = self.client.post("/api/vector-store/clear")
        
        # 驗證結果
        self.assertEqual(response.status_code, 500)
        data = response.json()
        self.assertIn("error", data)
    
    def test_search_with_invalid_params(self):
        """測試無效的搜索參數"""
        # 發送無查詢參數的請求
        response = self.client.get("/api/vector-store/search")
        
        # 驗證結果
        self.assertEqual(response.status_code, 422)
    
    def test_add_with_missing_fields(self):
        """測試缺少必要欄位的添加請求"""
        # 缺少 SQL 的請求數據
        request_data = {
            "query": "測試添加查詢"
        }
        
        # 發送請求
        response = self.client.post(
            "/api/vector-store/add",
            json=request_data
        )
        
        # 驗證結果
        self.assertEqual(response.status_code, 422)
    
    def test_add_with_error(self):
        """測試添加時出錯的情況"""
        # 配置模擬拋出異常
        self.mock_vector_store.add_query.side_effect = Exception("添加錯誤")
        
        # 請求數據
        request_data = {
            "query": "測試添加查詢",
            "sql": "SELECT * FROM test_table"
        }
        
        # 發送請求
        response = self.client.post(
            "/api/vector-store/add",
            json=request_data
        )
        
        # 驗證結果
        self.assertEqual(response.status_code, 500)
        data = response.json()
        self.assertIn("error", data)


if __name__ == '__main__':
    unittest.main()