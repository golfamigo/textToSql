import unittest
import os
import tempfile
import shutil
import numpy as np
from unittest.mock import patch, MagicMock
import faiss
from datetime import datetime
import sys

# 添加專用的 mock_settings 來繞過配置問題
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)
import mock_settings

# 在導入其他模塊前先模擬設置
sys.modules['app.utils.config'] = mock_settings
from app.services.vector_store import VectorStore, QueryEmbedding, VECTOR_DIMENSION


class TestVectorStore(unittest.TestCase):
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
        self.mock_model.encode.return_value = np.ones(VECTOR_DIMENSION, dtype=np.float32)
        self.mock_embedding_model.return_value = self.mock_model
        
        # 模擬路徑常量
        self.index_file_patcher = patch('app.services.vector_store.INDEX_FILE', self.index_path)
        self.metadata_file_patcher = patch('app.services.vector_store.METADATA_FILE', self.metadata_path)
        
        self.index_file_patcher.start()
        self.metadata_file_patcher.start()
        
        # 創建測試實例
        self.vector_store = VectorStore()
    
    def tearDown(self):
        # 停止所有模擬
        self.embedding_model_patcher.stop()
        self.index_file_patcher.stop()
        self.metadata_file_patcher.stop()
        
        # 刪除臨時目錄
        shutil.rmtree(self.temp_dir)
    
    def test_initialization(self):
        """測試向量存儲初始化"""
        # 確認模型被正確加載
        self.mock_embedding_model.assert_called_once()
        
        # 確認索引被初始化
        self.assertEqual(self.vector_store.get_count(), 0)
        self.assertIsInstance(self.vector_store.index, faiss.IndexFlatL2)
        self.assertEqual(len(self.vector_store.metadata), 0)
    
    def test_get_embedding(self):
        """測試獲取文本嵌入"""
        test_text = "測試查詢"
        embedding = self.vector_store.get_embedding(test_text)
        
        # 確認調用了模型的encode方法
        self.mock_model.encode.assert_called_once_with(test_text)
        
        # 確認返回了正確維度的向量
        self.assertEqual(embedding.shape, (VECTOR_DIMENSION,))
    
    def test_add_query(self):
        """測試添加查詢到向量存儲"""
        test_query = "找出所有預約"
        test_sql = "SELECT * FROM bookings"
        test_metadata = {"user_id": "test_user"}
        
        # 添加查詢
        embedding_id = self.vector_store.add_query(test_query, test_sql, test_metadata)
        
        # 確認索引中有一個項目
        self.assertEqual(self.vector_store.get_count(), 1)
        
        # 確認元數據被正確存儲
        self.assertEqual(len(self.vector_store.metadata), 1)
        self.assertEqual(self.vector_store.metadata[0]["query"], test_query)
        self.assertEqual(self.vector_store.metadata[0]["sql"], test_sql)
        self.assertEqual(self.vector_store.metadata[0]["metadata"], test_metadata)
        self.assertEqual(self.vector_store.metadata[0]["id"], embedding_id)
    
    def test_search_similar_empty_index(self):
        """測試在空索引中搜索"""
        results = self.vector_store.search_similar("測試查詢")
        self.assertEqual(len(results), 0)
    
    def test_search_similar(self):
        """測試搜索相似查詢"""
        # 添加一些測試數據
        test_queries = [
            ("找出所有預約", "SELECT * FROM bookings"),
            ("列出所有可用服務", "SELECT * FROM services"),
            ("找出特定用戶的預約", "SELECT * FROM bookings WHERE user_id = '123'")
        ]
        
        for query, sql in test_queries:
            self.vector_store.add_query(query, sql)
        
        # 搜索相似查詢
        results = self.vector_store.search_similar("查詢預約", k=2)
        
        # 確認返回了正確數量的結果
        self.assertEqual(len(results), 2)
        
        # 確認結果格式正確
        for result in results:
            self.assertIn("id", result)
            self.assertIn("query", result)
            self.assertIn("sql", result)
            self.assertIn("similarity", result)
            self.assertIn("timestamp", result)
            self.assertIn("metadata", result)
            
            # 相似度應該在0到1之間
            self.assertGreaterEqual(result["similarity"], 0)
            self.assertLessEqual(result["similarity"], 1)
    
    def test_save_and_load_index(self):
        """測試保存和加載索引"""
        # 添加一些測試數據
        test_query = "測試查詢"
        test_sql = "SELECT * FROM test"
        self.vector_store.add_query(test_query, test_sql)
        
        # 確認索引和元數據文件已創建
        self.assertTrue(os.path.exists(self.index_path))
        self.assertTrue(os.path.exists(self.metadata_path))
        
        # 創建新的向量存儲實例
        new_vector_store = VectorStore()
        
        # 確認數據被正確加載
        self.assertEqual(new_vector_store.get_count(), 1)
        self.assertEqual(len(new_vector_store.metadata), 1)
        self.assertEqual(new_vector_store.metadata[0]["query"], test_query)
        self.assertEqual(new_vector_store.metadata[0]["sql"], test_sql)
    
    def test_clear(self):
        """測試清除索引"""
        # 添加一些測試數據
        self.vector_store.add_query("測試查詢", "SELECT * FROM test")
        
        # 確認數據已添加
        self.assertEqual(self.vector_store.get_count(), 1)
        
        # 清除索引
        self.vector_store.clear()
        
        # 確認索引已清除
        self.assertEqual(self.vector_store.get_count(), 0)
        self.assertEqual(len(self.vector_store.metadata), 0)
    
    @patch('os.path.exists')
    def test_load_index_error_handling(self, mock_exists):
        """測試加載索引時的錯誤處理"""
        # 模擬索引文件存在但加載失敗
        mock_exists.return_value = True
        
        with patch('faiss.read_index', side_effect=Exception("測試錯誤")):
            # 應該捕獲異常並初始化新索引
            test_store = VectorStore()
            self.assertEqual(test_store.get_count(), 0)
    
    def test_query_embedding_model(self):
        """測試QueryEmbedding模型"""
        query = "測試查詢"
        sql = "SELECT * FROM test"
        embedding = [0.1] * 10
        metadata = {"test": "value"}
        
        # 創建QueryEmbedding實例
        query_embedding = QueryEmbedding(
            query=query,
            sql=sql,
            embedding=embedding,
            metadata=metadata
        )
        
        # 驗證欄位
        self.assertEqual(query_embedding.query, query)
        self.assertEqual(query_embedding.sql, sql)
        self.assertEqual(query_embedding.embedding, embedding)
        self.assertEqual(query_embedding.metadata, metadata)
        self.assertIsInstance(query_embedding.id, str)
        self.assertIsInstance(query_embedding.timestamp, datetime)


if __name__ == '__main__':
    unittest.main()