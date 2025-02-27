import unittest
import json
import os
import sys
import tempfile
import shutil
from fastapi.testclient import TestClient
from datetime import datetime
import pytest

# 添加模擬設置來繞過配置問題
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)
import mock_settings

# 在導入其他模塊前先模擬設置
sys.modules['app.utils.config'] = mock_settings

# 導入 API 和相關服務
from app.api import app
from app.services.text_to_sql import SQLResult, TextToSQLService
from app.services.database_service import DatabaseService
from app.services.llm_service import LLMService
from app.services.vector_store import VectorStore
from app.models import QueryHistoryModel

# 標記整個測試類為集成測試
@pytest.mark.integration
class TestAPIE2E(unittest.TestCase):
    """API 端到端測試，使用實際服務實例而非模擬"""
    
    @classmethod
    def setUpClass(cls):
        """測試類設置，只執行一次"""
        # 創建臨時目錄用於測試
        cls.test_dir = tempfile.mkdtemp()
        mock_settings.settings.vector_store_directory = os.path.join(cls.test_dir, "vector_store")
        mock_settings.settings.history_file = os.path.join(cls.test_dir, "history.json")
        
        # 創建測試客戶端
        cls.client = TestClient(app)
        
        # 創建實際的服務實例（非模擬）- 如果需要的話
        # 注意：這裡不創建真實的服務連接，依然使用API中預設的服務實例
    
    @classmethod
    def tearDownClass(cls):
        """測試類清理，只執行一次"""
        # 清理臨時目錄
        shutil.rmtree(cls.test_dir)
    
    def setUp(self):
        """每個測試方法開始前執行"""
        # 這裡可以添加特定測試需要的設置
        pass
    
    def tearDown(self):
        """每個測試方法結束後執行"""
        # 這裡可以添加特定測試需要的清理
        pass
    
    # 注意：以下測試依賴於應用程序中的實際服務實現
    # 由於無法在測試中連接真實資料庫，這些測試可能會失敗
    # 這些測試主要用於展示如何實現端到端測試
    
    @pytest.mark.skip(reason="需要真實服務連接")
    def test_health_check_e2e(self):
        """測試健康檢查端點（端到端）"""
        response = self.client.get("/health")
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "ok")
        # 注意：以下斷言取決於實際的資料庫連接和服務配置
        # self.assertEqual(data["database"], "connected")
        # self.assertGreaterEqual(len(data["models"]["names"]), 1)
    
    @pytest.mark.skip(reason="需要真實服務連接")
    def test_get_tables_e2e(self):
        """測試獲取所有表名（端到端）"""
        response = self.client.get("/api/tables")
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        # 注意：以下斷言取決於實際的資料庫內容
        # self.assertIsInstance(data["tables"], list)
        # self.assertGreater(len(data["tables"]), 0)
    
    @pytest.mark.skip(reason="需要真實服務連接")
    def test_get_models_e2e(self):
        """測試獲取可用模型（端到端）"""
        response = self.client.get("/api/models")
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("models", data)
        self.assertIn("default", data)
        self.assertGreaterEqual(len(data["models"]), 1)
    
    @pytest.mark.skip(reason="需要真實服務連接")
    def test_convert_text_to_sql_e2e(self):
        """測試文本到SQL轉換（端到端）"""
        # 請求數據
        request_data = {
            "query": "查詢所有用戶",
            "execute": False,
            "find_similar": False
        }
        
        response = self.client.post("/api/text-to-sql", json=request_data)
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("sql", data)
        self.assertIn("explanation", data)
        self.assertIsNotNone(data["query_id"])
    
    @pytest.mark.skip(reason="需要真實服務連接")
    def test_vector_store_workflow_e2e(self):
        """測試向量存儲工作流程（端到端）"""
        # 1. 首先清除向量存儲
        clear_response = self.client.post("/api/vector-store/clear")
        self.assertEqual(clear_response.status_code, 200)
        
        # 2. 獲取統計信息（應該為空）
        stats_response = self.client.get("/api/vector-store/stats")
        self.assertEqual(stats_response.status_code, 200)
        self.assertEqual(stats_response.json()["count"], 0)
        
        # 3. 添加查詢
        add_data = {
            "query": "查詢所有用戶",
            "sql": "SELECT * FROM n8n_booking_users",
            "metadata": {"test": True}
        }
        add_response = self.client.post("/api/vector-store/add", json=add_data)
        self.assertEqual(add_response.status_code, 200)
        query_id = add_response.json()["id"]
        self.assertIsNotNone(query_id)
        
        # 4. 再次獲取統計信息（應該有1個項目）
        stats_response = self.client.get("/api/vector-store/stats")
        self.assertEqual(stats_response.status_code, 200)
        self.assertEqual(stats_response.json()["count"], 1)
        
        # 5. 搜索相似查詢
        search_response = self.client.get("/api/vector-store/search?query=查詢用戶&limit=5")
        self.assertEqual(search_response.status_code, 200)
        results = search_response.json()
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["query"], "查詢所有用戶")
        
        # 6. 最後再次清除向量存儲
        clear_response = self.client.post("/api/vector-store/clear")
        self.assertEqual(clear_response.status_code, 200)


# 如果需要單獨運行這些測試
if __name__ == '__main__':
    unittest.main()