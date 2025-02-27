import unittest
from unittest.mock import patch, MagicMock
import json
import os
import sys
import tempfile
import shutil
from fastapi.testclient import TestClient
from datetime import datetime, timedelta

# 添加模擬設置來繞過配置問題
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)
import mock_settings

# 在導入其他模塊前先模擬設置
sys.modules['app.utils.config'] = mock_settings

# 導入 API 和相關服務
from app.api import app
from app.services.text_to_sql import SQLResult
from app.models import QueryHistoryModel


class TestAPIIntegration(unittest.TestCase):
    """API 整合測試"""
    
    def setUp(self):
        """測試設置"""
        # 創建測試客戶端
        self.client = TestClient(app)
        
        # 建立臨時目錄用於測試
        self.test_dir = tempfile.mkdtemp()
        mock_settings.settings.vector_store_directory = os.path.join(self.test_dir, "vector_store")
        mock_settings.settings.history_file = os.path.join(self.test_dir, "history.json")
        
        # 模擬服務
        self.setup_mocks()
    
    def tearDown(self):
        """測試清理"""
        # 停止所有 patch
        for patcher in self.patchers:
            patcher.stop()
        
        # 清理臨時目錄
        shutil.rmtree(self.test_dir)
    
    def setup_mocks(self):
        """設置所有需要的模擬"""
        self.patchers = []
        
        # 模擬 TextToSQLService
        self.text_to_sql_patcher = patch('app.api.text_to_sql_service')
        self.mock_text_to_sql = self.text_to_sql_patcher.start()
        self.patchers.append(self.text_to_sql_patcher)
        
        # 模擬 DatabaseService
        self.db_service_patcher = patch('app.api.db_service')
        self.mock_db_service = self.db_service_patcher.start()
        self.patchers.append(self.db_service_patcher)
        
        # 模擬 VectorStore
        self.vector_store_patcher = patch('app.api.vector_store')
        self.mock_vector_store = self.vector_store_patcher.start()
        self.patchers.append(self.vector_store_patcher)
        
        # 模擬 LLMService
        self.llm_service_patcher = patch('app.api.llm_service')
        self.mock_llm_service = self.llm_service_patcher.start()
        self.patchers.append(self.llm_service_patcher)
        
        # 基本配置
        self.mock_db_service.is_connected.return_value = True
        self.mock_llm_service.get_available_models.return_value = ["dummy-model", "test-model"]
    
    def test_health_check(self):
        """測試健康檢查端點"""
        response = self.client.get("/health")
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "ok")
        self.assertEqual(data["database"], "connected")
        self.assertEqual(data["models"]["default"], "dummy-model")
        self.assertEqual(data["models"]["available"], 2)
        
        # 驗證調用
        self.mock_db_service.is_connected.assert_called_once()
        self.mock_llm_service.get_available_models.assert_called_once()
    
    def test_convert_text_to_sql(self):
        """測試文本到SQL轉換端點"""
        # 準備模擬返回值
        mock_result = SQLResult(
            sql="SELECT * FROM n8n_booking_users WHERE email = :email",
            explanation="這個查詢從用戶表中查找符合指定電子郵件的用戶。",
            parameters={"email": "test@example.com"},
            query_id="test-query-id"
        )
        self.mock_text_to_sql.text_to_sql.return_value = mock_result
        
        # 發送請求
        request_data = {
            "query": "找到email是test@example.com的用戶",
            "execute": True,
            "model": "test-model",
            "find_similar": True
        }
        response = self.client.post("/api/text-to-sql", json=request_data)
        
        # 驗證結果
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["sql"], "SELECT * FROM n8n_booking_users WHERE email = :email")
        self.assertEqual(data["parameters"], {"email": "test@example.com"})
        
        # 驗證調用
        self.mock_text_to_sql.text_to_sql.assert_called_once_with(
            query="找到email是test@example.com的用戶",
            execute=True,
            find_similar=True
        )
    
    def test_convert_text_to_sql_error(self):
        """測試文本到SQL轉換錯誤處理"""
        # 模擬拋出異常
        self.mock_text_to_sql.text_to_sql.side_effect = Exception("測試錯誤")
        
        # 發送請求
        request_data = {
            "query": "無效查詢",
            "execute": False
        }
        response = self.client.post("/api/text-to-sql", json=request_data)
        
        # 驗證結果
        self.assertEqual(response.status_code, 500)
        data = response.json()
        self.assertIn("detail", data)
        self.assertIn("測試錯誤", data["detail"])
    
    def test_convert_text_to_sql_invalid_model(self):
        """測試使用無效模型"""
        # 發送請求
        request_data = {
            "query": "測試查詢",
            "model": "不存在的模型"
        }
        response = self.client.post("/api/text-to-sql", json=request_data)
        
        # 驗證結果
        self.assertEqual(response.status_code, 422)
        data = response.json()
        self.assertIn("不存在的模型", str(data))
    
    def test_get_query_history(self):
        """測試獲取查詢歷史"""
        # 準備模擬返回值
        mock_history = [
            QueryHistoryModel(
                id="hist-1",
                user_query="找到所有用戶",
                generated_sql="SELECT * FROM n8n_booking_users",
                explanation="查詢所有用戶",
                executed=True,
                created_at=datetime.now() - timedelta(days=1)
            ),
            QueryHistoryModel(
                id="hist-2",
                user_query="找到特定email的用戶",
                generated_sql="SELECT * FROM n8n_booking_users WHERE email = :email",
                explanation="查詢特定郵箱的用戶",
                executed=False,
                created_at=datetime.now()
            )
        ]
        self.mock_text_to_sql.get_history.return_value = mock_history
        
        # 發送請求
        response = self.client.get("/api/history?limit=10&offset=0")
        
        # 驗證結果
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data), 2)
        self.assertEqual(data[0]["id"], "hist-1")
        self.assertEqual(data[1]["id"], "hist-2")
        
        # 驗證調用
        self.mock_text_to_sql.get_history.assert_called_once_with(10, 0)
    
    def test_get_query_history_error(self):
        """測試獲取查詢歷史錯誤處理"""
        # 模擬拋出異常
        self.mock_text_to_sql.get_history.side_effect = Exception("歷史記錄錯誤")
        
        # 發送請求
        response = self.client.get("/api/history")
        
        # 驗證結果
        self.assertEqual(response.status_code, 500)
        data = response.json()
        self.assertIn("detail", data)
        self.assertIn("歷史記錄錯誤", data["detail"])
    
    def test_execute_sql(self):
        """測試直接執行SQL"""
        # 準備模擬返回值
        mock_result = MagicMock()
        mock_result.error = None
        mock_result.to_dict.return_value = {
            "columns": ["id", "name", "email"],
            "rows": [[1, "測試用戶", "test@example.com"]],
            "execution_time": 0.1
        }
        self.mock_text_to_sql.execute_sql.return_value = mock_result
        
        # 模擬SQL安全性檢查
        self.mock_db_service.is_safe_query.return_value = (True, "")
        
        # 發送請求
        sql_query = "SELECT * FROM n8n_booking_users WHERE id = 1"
        response = self.client.post(f"/api/execute-sql?sql={sql_query}")
        
        # 驗證結果
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["columns"], ["id", "name", "email"])
        self.assertEqual(len(data["rows"]), 1)
        
        # 驗證調用
        self.mock_db_service.is_safe_query.assert_called_once_with(sql_query)
        self.mock_text_to_sql.execute_sql.assert_called_once_with(sql_query)
    
    def test_execute_sql_unsafe(self):
        """測試執行不安全的SQL"""
        # 模擬SQL安全性檢查
        self.mock_db_service.is_safe_query.return_value = (False, "不允許修改數據")
        
        # 發送請求
        sql_query = "DELETE FROM n8n_booking_users"
        response = self.client.post(f"/api/execute-sql?sql={sql_query}")
        
        # 驗證結果
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertIn("detail", data)
        self.assertEqual(data["detail"], "不允許修改數據")
        
        # 驗證未執行SQL
        self.mock_text_to_sql.execute_sql.assert_not_called()
    
    def test_execute_sql_error(self):
        """測試執行SQL時發生錯誤"""
        # 模擬SQL安全性檢查
        self.mock_db_service.is_safe_query.return_value = (True, "")
        
        # 準備模擬返回值
        mock_result = MagicMock()
        mock_result.error = "SQL語法錯誤"
        self.mock_text_to_sql.execute_sql.return_value = mock_result
        
        # 發送請求
        sql_query = "SELECT * FROM 不存在的表"
        response = self.client.post(f"/api/execute-sql?sql={sql_query}")
        
        # 驗證結果
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertIn("error", data)
        self.assertEqual(data["error"], "SQL語法錯誤")
    
    def test_get_tables(self):
        """測試獲取所有表名"""
        # 準備模擬返回值
        self.mock_db_service.get_tables.return_value = [
            "n8n_booking_users",
            "n8n_booking_services",
            "n8n_booking_bookings"
        ]
        
        # 發送請求
        response = self.client.get("/api/tables")
        
        # 驗證結果
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data["tables"]), 3)
        self.assertIn("n8n_booking_users", data["tables"])
        
        # 驗證調用
        self.mock_db_service.get_tables.assert_called_once()
    
    def test_get_table_schema(self):
        """測試獲取表結構"""
        # 準備模擬返回值
        mock_schema = {
            "table_name": "n8n_booking_users",
            "columns": [
                {"name": "id", "type": "INTEGER", "nullable": False},
                {"name": "name", "type": "VARCHAR", "nullable": False},
                {"name": "email", "type": "VARCHAR", "nullable": True}
            ],
            "primary_keys": ["id"],
            "foreign_keys": []
        }
        self.mock_db_service.get_table_schema.return_value = mock_schema
        
        # 發送請求
        response = self.client.get("/api/table/n8n_booking_users/schema")
        
        # 驗證結果
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["table_name"], "n8n_booking_users")
        self.assertEqual(len(data["columns"]), 3)
        
        # 驗證調用
        self.mock_db_service.get_table_schema.assert_called_once_with("n8n_booking_users")
    
    def test_get_table_schema_error(self):
        """測試獲取不存在的表結構"""
        # 準備模擬返回值
        self.mock_db_service.get_table_schema.return_value = {"error": "表不存在"}
        
        # 發送請求
        response = self.client.get("/api/table/不存在的表/schema")
        
        # 驗證結果
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertIn("detail", data)
        self.assertEqual(data["detail"], "表不存在")
    
    def test_get_available_models(self):
        """測試獲取可用模型"""
        # 發送請求
        response = self.client.get("/api/models")
        
        # 驗證結果
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["default"], "dummy-model")
        self.assertEqual(len(data["models"]), 2)
        self.assertIn("dummy-model", data["models"])
        self.assertIn("test-model", data["models"])
    
    def test_rate_model(self):
        """測試模型評分"""
        # 發送請求
        request_data = {
            "request_id": "test-request-id",
            "score": 4.5,
            "reason": "結果很準確"
        }
        response = self.client.post("/api/rate-model", json=request_data)
        
        # 驗證結果
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["message"], "評分已接收")
        
        # 驗證調用
        self.mock_llm_service.rate_response.assert_called_once()
    
    def test_rate_model_invalid_score(self):
        """測試無效的評分"""
        # 發送請求
        request_data = {
            "request_id": "test-request-id",
            "score": 6.0,  # 超出範圍（1-5）
            "reason": "結果很準確"
        }
        response = self.client.post("/api/rate-model", json=request_data)
        
        # 驗證結果
        self.assertEqual(response.status_code, 422)
        data = response.json()
        self.assertIn("評分必須在 1-5 之間", str(data))
    
    def test_vector_store_stats(self):
        """測試獲取向量存儲統計"""
        # 準備模擬返回值
        self.mock_vector_store.get_count.return_value = 15
        
        # 發送請求
        response = self.client.get("/api/vector-store/stats")
        
        # 驗證結果
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["count"], 15)
        self.assertEqual(data["status"], "active")
        
        # 驗證調用
        self.mock_vector_store.get_count.assert_called_once()
    
    def test_vector_store_stats_empty(self):
        """測試向量存儲為空時的統計"""
        # 準備模擬返回值
        self.mock_vector_store.get_count.return_value = 0
        
        # 發送請求
        response = self.client.get("/api/vector-store/stats")
        
        # 驗證結果
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["count"], 0)
        self.assertEqual(data["status"], "empty")
    
    def test_search_similar_queries(self):
        """測試搜索相似查詢"""
        # 準備模擬返回值
        mock_results = [
            {
                "id": "query-1",
                "query": "查詢所有用戶",
                "sql": "SELECT * FROM n8n_booking_users",
                "similarity": 0.85,
                "timestamp": datetime.now().isoformat()
            },
            {
                "id": "query-2",
                "query": "查詢活躍用戶",
                "sql": "SELECT * FROM n8n_booking_users WHERE is_active = true",
                "similarity": 0.75,
                "timestamp": datetime.now().isoformat()
            }
        ]
        self.mock_vector_store.search_similar.return_value = mock_results
        
        # 發送請求
        response = self.client.get("/api/vector-store/search?query=查詢用戶&limit=5")
        
        # 驗證結果
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data), 2)
        self.assertEqual(data[0]["id"], "query-1")
        self.assertEqual(data[1]["id"], "query-2")
        
        # 驗證調用
        self.mock_vector_store.search_similar.assert_called_once_with("查詢用戶", k=5)
    
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
        
        # 驗證調用
        self.mock_vector_store.clear.assert_called_once()
    
    def test_add_query_to_vector_store(self):
        """測試添加查詢到向量存儲"""
        # 配置模擬返回值
        self.mock_vector_store.add_query.return_value = "new-query-id"
        
        # 請求數據
        request_data = {
            "query": "測試查詢",
            "sql": "SELECT * FROM test_table",
            "metadata": {"test": True}
        }
        
        # 發送請求
        response = self.client.post("/api/vector-store/add", json=request_data)
        
        # 驗證結果
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["id"], "new-query-id")
        
        # 驗證調用
        self.mock_vector_store.add_query.assert_called_once_with(
            "測試查詢", 
            "SELECT * FROM test_table",
            {"test": True}
        )
    
    def test_search_vector_store_with_error(self):
        """測試搜索向量存儲時出錯"""
        # 配置模擬拋出異常
        self.mock_vector_store.search_similar.side_effect = Exception("搜索錯誤")
        
        # 發送請求
        response = self.client.get("/api/vector-store/search?query=錯誤查詢")
        
        # 驗證結果
        self.assertEqual(response.status_code, 500)
        data = response.json()
        self.assertIn("detail", data)
        self.assertIn("搜索錯誤", data["detail"])
    
    def test_model_performance(self):
        """測試獲取模型性能統計"""
        # 準備模擬返回值
        mock_performance = {
            "dummy-model": {
                "total_requests": 100,
                "average_rating": 4.5,
                "latency": {
                    "p50": 1.2,
                    "p95": 2.3,
                    "p99": 3.1
                }
            }
        }
        self.mock_llm_service.get_model_performance.return_value = mock_performance
        
        # 發送請求
        response = self.client.get("/api/model-performance?model_name=dummy-model")
        
        # 驗證結果
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["dummy-model"]["total_requests"], 100)
        self.assertEqual(data["dummy-model"]["average_rating"], 4.5)
        
        # 驗證調用
        self.mock_llm_service.get_model_performance.assert_called_once_with("dummy-model")
    
    def test_model_performance_all(self):
        """測試獲取所有模型性能統計"""
        # 準備模擬返回值
        mock_performance = {
            "dummy-model": {"total_requests": 100, "average_rating": 4.5},
            "test-model": {"total_requests": 50, "average_rating": 4.2}
        }
        self.mock_llm_service.get_model_performance.return_value = mock_performance
        
        # 發送請求
        response = self.client.get("/api/model-performance")
        
        # 驗證結果
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data), 2)
        self.assertIn("dummy-model", data)
        self.assertIn("test-model", data)


if __name__ == '__main__':
    unittest.main()