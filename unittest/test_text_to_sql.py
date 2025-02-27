"""
測試文本到SQL轉換服務
"""
import unittest
from unittest.mock import MagicMock, patch
import json
import os
import sys
from datetime import datetime

# 添加應用路徑到系統路徑
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

class MockLLMResponse:
    """模擬LLM回應"""
    def __init__(self, content, is_error_val=False, error=None):
        self.content = content
        self._is_error = is_error_val
        self.error = error
        self.model = "test-model"
        self.token_usage = {"prompt_tokens": 10, "completion_tokens": 20}
        self.latency = 200.0  # 200ms
        
    def is_error(self):
        return self._is_error
        
    def get_parsed_json(self):
        return json.loads(self.content)


class TestTextToSQL(unittest.TestCase):
    """測試TextToSQL服務"""
    
    def setUp(self):
        """設置測試環境"""
        # 建立模擬的LLM服務
        self.mock_llm_service = MagicMock()
        self.mock_llm_response = MockLLMResponse(
            content=json.dumps({
                "sql": "SELECT * FROM test_table WHERE id = :id",
                "explanation": "這是一個測試查詢",
                "parameters": {"id": 1}
            })
        )
        self.mock_llm_service.generate.return_value = self.mock_llm_response
        
        # 建立模擬的歷史服務
        self.mock_history_service = MagicMock()
        
        # 建立模擬的資料庫服務
        self.mock_db_service = MagicMock()
        self.mock_db_service.is_connected.return_value = True
        
        # 建立模擬的向量存儲服務
        self.mock_vector_store = MagicMock()
        self.mock_vector_store.search_similar.return_value = []
        
        # 建立模擬的對話管理器
        self.mock_conversation_manager = MagicMock()
        self.mock_conversation_manager.get_conversation_history.return_value = []
    
    def test_basic_text_to_sql(self):
        """測試基本的文本到SQL轉換"""
        # 導入需要測試的類
        from app.services.text_to_sql import TextToSQLService, SQLResult
        
        # 創建服務實例並替換依賴
        with patch('app.services.text_to_sql.llm_service', self.mock_llm_service), \
             patch('app.services.text_to_sql.get_table_schema_description', return_value="測試資料庫模式"), \
             patch('app.services.text_to_sql.HistoryService', return_value=self.mock_history_service), \
             patch('app.services.text_to_sql.DatabaseService', return_value=self.mock_db_service), \
             patch('app.services.text_to_sql.vector_store', self.mock_vector_store), \
             patch('app.services.text_to_sql.conversation_manager', self.mock_conversation_manager), \
             patch('app.services.text_to_sql.get_function_suggestion', return_value=None):
            
            # 創建服務實例
            service = TextToSQLService()
            
            # 執行測試
            result = service.text_to_sql("查詢測試表中ID為1的數據")
            
            # 驗證結果
            self.assertIsInstance(result, SQLResult)
            self.assertEqual(result.sql, "SELECT * FROM test_table WHERE id = :id")
            self.assertEqual(result.explanation, "這是一個測試查詢")
            self.assertEqual(result.parameters, {"id": 1})
            
            # 驗證LLM服務調用
            self.mock_llm_service.generate.assert_called_once()
            
            # 驗證歷史服務調用
            self.mock_history_service.add_query.assert_called_once()
    
    def test_error_handling(self):
        """測試錯誤處理"""
        # 設置LLM服務返回錯誤
        error_response = MockLLMResponse(content="", is_error_val=True, error="測試錯誤")
        self.mock_llm_service.generate.return_value = error_response
        
        # 導入需要測試的類
        from app.services.text_to_sql import TextToSQLService
        
        # 創建服務實例並替換依賴
        with patch('app.services.text_to_sql.llm_service', self.mock_llm_service), \
             patch('app.services.text_to_sql.get_table_schema_description', return_value="測試資料庫模式"), \
             patch('app.services.text_to_sql.HistoryService', return_value=self.mock_history_service), \
             patch('app.services.text_to_sql.DatabaseService', return_value=self.mock_db_service), \
             patch('app.services.text_to_sql.vector_store', self.mock_vector_store), \
             patch('app.services.text_to_sql.conversation_manager', self.mock_conversation_manager), \
             patch('app.services.text_to_sql.get_function_suggestion', return_value=None):
            
            # 創建服務實例
            service = TextToSQLService()
            
            # 執行測試
            result = service.text_to_sql("查詢測試表中ID為1的數據")
            
            # 驗證結果包含錯誤信息
            self.assertTrue(result.sql.startswith("--"))
            self.assertTrue("錯誤" in result.explanation)
            
            # 驗證錯誤記錄到歷史
            self.mock_history_service.add_query.assert_called_once()
    
    def test_conversation_context(self):
        """測試對話上下文處理"""
        # 設置對話歷史
        from app.models.query_history import QueryHistoryModel
        
        mock_history = [
            QueryHistoryModel(
                id="1",
                user_query="查詢用戶'小明'的資料",
                generated_sql="SELECT * FROM users WHERE name = :name",
                explanation="查詢名為小明的用戶資料",
                executed=True,
                parameters={"name": "小明"}
            )
        ]
        self.mock_conversation_manager.get_conversation_history.return_value = mock_history
        
        # 設置參考解析回應
        reference_response = MockLLMResponse(
            content=json.dumps({
                "resolved_query": "查詢小明的預約記錄",
                "entity_references": {"他": "小明"}
            })
        )
        reference_response_mock = MagicMock(return_value=reference_response)
        
        # 導入需要測試的類
        from app.services.text_to_sql import TextToSQLService
        
        # 創建服務實例並替換依賴
        with patch('app.services.text_to_sql.llm_service', self.mock_llm_service), \
             patch('app.services.text_to_sql.get_table_schema_description', return_value="測試資料庫模式"), \
             patch('app.services.text_to_sql.HistoryService', return_value=self.mock_history_service), \
             patch('app.services.text_to_sql.DatabaseService', return_value=self.mock_db_service), \
             patch('app.services.text_to_sql.vector_store', self.mock_vector_store), \
             patch('app.services.text_to_sql.conversation_manager', self.mock_conversation_manager), \
             patch('app.services.text_to_sql.get_function_suggestion', return_value=None):
            
            # 創建服務實例
            service = TextToSQLService()
            
            # 模擬參考解析方法
            service._resolve_references = MagicMock(return_value=("查詢小明的預約記錄", {"他": "小明"}))
            
            # 執行測試
            result = service.text_to_sql("查詢他的預約記錄", session_id="test-session")
            
            # 驗證結果
            self.assertIsInstance(result, SQLResult)
            
            # 驗證對話上下文處理
            self.mock_conversation_manager.get_conversation_history.assert_called_once_with("test-session", limit=5)
            service._resolve_references.assert_called_once()
            
            # 驗證LLM服務調用包含上下文
            args, kwargs = self.mock_llm_service.generate.call_args
            self.assertTrue("system_prompt" in kwargs)
            self.assertIn("當前對話的上下文", kwargs.get("system_prompt", ""))
    
    def test_execute_query(self):
        """測試執行查詢功能"""
        # 導入需要測試的類
        from app.services.text_to_sql import TextToSQLService
        from app.services.database_service import QueryResult
        
        # 設置模擬的查詢結果
        mock_result = QueryResult(
            columns=["id", "name"],
            rows=[[1, "test"]],
            row_count=1,
            execution_time=10.5,
            error=None
        )
        self.mock_db_service.execute_query.return_value = mock_result
        self.mock_db_service.execute_query_with_viz.return_value = (mock_result, None)
        
        # 創建服務實例並替換依賴
        with patch('app.services.text_to_sql.llm_service', self.mock_llm_service), \
             patch('app.services.text_to_sql.get_table_schema_description', return_value="測試資料庫模式"), \
             patch('app.services.text_to_sql.HistoryService', return_value=self.mock_history_service), \
             patch('app.services.text_to_sql.DatabaseService', return_value=self.mock_db_service), \
             patch('app.services.text_to_sql.vector_store', self.mock_vector_store), \
             patch('app.services.text_to_sql.conversation_manager', self.mock_conversation_manager), \
             patch('app.services.text_to_sql.get_function_suggestion', return_value=None):
            
            # 創建服務實例
            service = TextToSQLService()
            
            # 執行測試: 執行查詢
            result = service.text_to_sql("查詢測試表中ID為1的數據", execute=True)
            
            # 驗證結果
            self.assertIsNotNone(result.execution_result)
            
            # 驗證資料庫服務調用
            self.mock_db_service.execute_query_with_viz.assert_called_once()
            
            # 直接測試execute_sql方法
            query_result = service.execute_sql("SELECT * FROM test", {"param": "value"})
            self.assertEqual(query_result, mock_result)
            self.mock_db_service.execute_query_with_viz.assert_called()


if __name__ == '__main__':
    unittest.main()