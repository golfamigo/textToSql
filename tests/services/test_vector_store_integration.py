import unittest
import os
import tempfile
import shutil
from unittest.mock import patch, MagicMock
import json
import numpy as np
from datetime import datetime
import sys

# 添加專用的 mock_settings 來繞過配置問題
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)
import mock_settings

# 在導入其他模塊前先模擬設置
sys.modules['app.utils.config'] = mock_settings

from app.services.vector_store import VectorStore
from app.services.text_to_sql import TextToSQLService, SQLResult, SimilarQuery


class TestVectorStoreIntegration(unittest.TestCase):
    def setUp(self):
        # 創建臨時目錄用於測試
        self.temp_dir = tempfile.mkdtemp()
        
        # 修改常量以使用臨時目錄
        self.index_path = os.path.join(self.temp_dir, "test_index.faiss")
        self.metadata_path = os.path.join(self.temp_dir, "test_metadata.joblib")
        
        # 模擬 SentenceTransformer
        self.embedding_model_patcher = patch('app.services.vector_store.SentenceTransformer')
        self.mock_embedding_model = self.embedding_model_patcher.start()
        
        # 設置模擬模型返回固定的向量
        self.mock_model = MagicMock()
        self.mock_model.encode.return_value = np.ones(384, dtype=np.float32)
        self.mock_embedding_model.return_value = self.mock_model
        
        # 模擬路徑常量
        self.index_file_patcher = patch('app.services.vector_store.INDEX_FILE', self.index_path)
        self.metadata_file_patcher = patch('app.services.vector_store.METADATA_FILE', self.metadata_path)
        
        self.index_file_patcher.start()
        self.metadata_file_patcher.start()
        
        # 創建向量存儲實例
        self.vector_store = VectorStore()
        
        # 初始化 LLM 服務的模擬
        self.llm_service_patcher = patch('app.services.text_to_sql.llm_service')
        self.mock_llm_service = self.llm_service_patcher.start()
        
        # 配置 LLM 服務返回
        self.configure_llm_service_mock()
        
        # 模擬 vector_store 全局變量
        self.vector_store_patcher = patch('app.services.text_to_sql.vector_store', self.vector_store)
        self.vector_store_patcher.start()
        
        # 模擬歷史服務
        self.history_service_patcher = patch('app.services.history_service.HistoryService')
        self.mock_history_service = self.history_service_patcher.start()
        
        # 模擬對話管理器
        self.conversation_manager_patcher = patch('app.services.text_to_sql.conversation_manager')
        self.mock_conversation_manager = self.conversation_manager_patcher.start()
        
        # 模擬資料庫服務
        self.db_service_patcher = patch('app.services.database_service.DatabaseService')
        self.mock_db_service = self.db_service_patcher.start()
        
        # 模擬 schema 描述
        self.schema_patcher = patch('app.services.text_to_sql.get_table_schema_description', return_value="模擬資料庫結構")
        self.schema_patcher.start()
        
        # 創建 TextToSQLService 實例
        self.text_to_sql_service = TextToSQLService()
    
    def tearDown(self):
        # 停止所有模擬
        self.embedding_model_patcher.stop()
        self.index_file_patcher.stop()
        self.metadata_file_patcher.stop()
        self.llm_service_patcher.stop()
        self.vector_store_patcher.stop()
        self.history_service_patcher.stop()
        self.conversation_manager_patcher.stop()
        self.db_service_patcher.stop()
        self.schema_patcher.stop()
        
        # 刪除臨時目錄
        shutil.rmtree(self.temp_dir)
    
    def configure_llm_service_mock(self):
        """配置 LLM 服務模擬返回值"""
        llm_response = MagicMock()
        llm_response.is_error.return_value = False
        llm_response.get_parsed_json.return_value = {
            "sql": "SELECT * FROM test_table",
            "explanation": "這是一個測試查詢",
            "parameters": {}
        }
        self.mock_llm_service.generate.return_value = llm_response
    
    def test_similar_query_search_and_storage(self):
        """測試相似查詢搜索和存儲功能整合"""
        # 初始化一些查詢數據到向量存儲
        queries = [
            ("列出所有用戶", "SELECT * FROM n8n_booking_users"),
            ("找出價格超過100的服務", "SELECT * FROM n8n_booking_services WHERE price > :price"),
            ("查看明天的可用時段", "SELECT * FROM get_period_availability_by_date(:date)")
        ]
        
        for query, sql in queries:
            self.vector_store.add_query(query, sql)
        
        # 執行一個新的查詢，確認能夠找到相似查詢
        new_query = "顯示所有用戶"
        
        # 設置模擬以返回固定的相似度
        similarity_mock = MagicMock()
        similarity_mock.side_effect = lambda x, k: (np.array([[0.5]]), np.array([[0]]))
        self.vector_store.index.search = similarity_mock
        
        # 執行文本到 SQL 轉換
        result = self.text_to_sql_service.text_to_sql(new_query, find_similar=True)
        
        # 確認結果中包含相似查詢
        self.assertIsNotNone(result.similar_queries)
        
        # 驗證相似查詢是否添加到向量存儲
        self.assertEqual(self.vector_store.get_count(), 4)  # 原有3個 + 新增1個
        self.assertEqual(len(self.vector_store.metadata), 4)
        self.assertEqual(self.vector_store.metadata[3]["query"], new_query)
    
    def test_vector_store_error_handling(self):
        """測試向量存儲錯誤處理"""
        # 模擬向量存儲搜索時出錯
        self.vector_store.search_similar = MagicMock(side_effect=Exception("向量搜索錯誤"))
        
        # 執行文本到 SQL 轉換，應該能夠正常處理錯誤並繼續工作
        result = self.text_to_sql_service.text_to_sql("測試查詢", find_similar=True)
        
        # 應該成功生成 SQL，即使向量存儲搜索失敗
        self.assertEqual(result.sql, "SELECT * FROM test_table")
        self.assertIsNone(result.similar_queries)  # 沒有相似查詢結果
    
    def test_add_query_to_vector_store_error_handling(self):
        """測試添加查詢到向量存儲時的錯誤處理"""
        # 模擬添加查詢到向量存儲時出錯
        self.vector_store.add_query = MagicMock(side_effect=Exception("添加查詢錯誤"))
        
        # 執行文本到 SQL 轉換，應該能夠正常處理錯誤並繼續工作
        result = self.text_to_sql_service.text_to_sql("測試查詢")
        
        # 應該成功生成 SQL，即使添加到向量存儲失敗
        self.assertEqual(result.sql, "SELECT * FROM test_table")
    
    def test_no_similar_query_found(self):
        """測試沒有找到相似查詢的情況"""
        # 清空向量存儲
        self.vector_store.clear()
        
        # 執行文本到 SQL 轉換
        result = self.text_to_sql_service.text_to_sql("測試查詢", find_similar=True)
        
        # 應該沒有相似查詢結果
        self.assertIsNone(result.similar_queries)
    
    def test_similar_query_threshold_filtering(self):
        """測試相似度閾值過濾"""
        # 添加一個查詢
        self.vector_store.add_query("測試查詢", "SELECT * FROM test")
        
        # 模擬搜索結果有一個低相似度的結果
        def mock_search_similar(query, k):
            return [
                {
                    "id": "test-id",
                    "query": "測試查詢",
                    "sql": "SELECT * FROM test",
                    "timestamp": datetime.now(),
                    "similarity": 0.6,  # 低於 0.7 的閾值
                    "metadata": {}
                }
            ]
        
        self.vector_store.search_similar = MagicMock(side_effect=mock_search_similar)
        
        # 執行文本到 SQL 轉換
        result = self.text_to_sql_service.text_to_sql("新的測試查詢", find_similar=True)
        
        # 因為相似度低於閾值，所以不應該有相似查詢結果
        self.assertIsNone(result.similar_queries)
    
    def test_similar_query_in_prompt(self):
        """測試相似查詢添加到提示詞"""
        # 添加一個查詢
        self.vector_store.add_query("測試查詢", "SELECT * FROM test")
        
        # 模擬搜索結果有一個高相似度的結果
        def mock_search_similar(query, k):
            return [
                {
                    "id": "test-id",
                    "query": "測試查詢",
                    "sql": "SELECT * FROM test",
                    "timestamp": datetime.now(),
                    "similarity": 0.8,  # 高於 0.7 的閾值
                    "metadata": {}
                }
            ]
        
        self.vector_store.search_similar = MagicMock(side_effect=mock_search_similar)
        
        # 執行文本到 SQL 轉換
        self.text_to_sql_service.text_to_sql("新的測試查詢", find_similar=True)
        
        # 檢查 LLM 服務是否收到包含相似查詢的提示詞
        # 獲取系統提示詞
        system_prompt = self.mock_llm_service.generate.call_args[1]["system_prompt"]
        
        # 確認相似查詢信息被包含在系統提示詞中
        self.assertIn("相似查詢", system_prompt)
        self.assertIn("測試查詢", system_prompt)
        self.assertIn("SELECT * FROM test", system_prompt)
    
    def test_similar_query_model(self):
        """測試 SimilarQuery 模型"""
        query = "測試查詢"
        sql = "SELECT * FROM test"
        similarity = 0.85
        timestamp = datetime.now()
        
        # 創建 SimilarQuery 實例
        similar_query = SimilarQuery(
            query=query,
            sql=sql,
            similarity=similarity,
            timestamp=timestamp
        )
        
        # 驗證欄位
        self.assertEqual(similar_query.query, query)
        self.assertEqual(similar_query.sql, sql)
        self.assertEqual(similar_query.similarity, similarity)
        self.assertEqual(similar_query.timestamp, timestamp)


if __name__ == '__main__':
    unittest.main()