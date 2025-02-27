"""
測試文本到SQL轉換核心功能
"""
import pytest
from unittest.mock import MagicMock, patch
import json
from datetime import datetime
import sys
import os
# 添加應用路徑到系統路徑
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from textToSql.app.services.text_to_sql import TextToSQLService, SQLResult
from textToSql.app.models.query_history import QueryHistoryModel


class MockLLMResponse:
    """模擬LLM回應"""
    def __init__(self, content, is_error_val=False, error=None):
        self.content = content
        self._is_error = is_error_val
        self.error = error
        self.model = "test-model"
        
    def is_error(self):
        return self._is_error
        
    def get_parsed_json(self):
        return json.loads(self.content)


@pytest.fixture
def mock_services():
    """設置模擬服務"""
    # 建立模擬的LLM服務
    mock_llm_service = MagicMock()
    mock_llm_response = MockLLMResponse(
        content=json.dumps({
            "sql": "SELECT * FROM test_table WHERE id = :id",
            "explanation": "這是一個測試查詢",
            "parameters": {"id": 1}
        })
    )
    mock_llm_service.generate.return_value = mock_llm_response
    
    # 建立模擬的歷史服務
    mock_history_service = MagicMock()
    
    # 建立模擬的資料庫服務
    mock_db_service = MagicMock()
    mock_db_service.is_connected.return_value = True
    
    # 建立模擬的向量存儲服務
    mock_vector_store = MagicMock()
    mock_vector_store.search_similar.return_value = []
    
    # 建立模擬的對話管理器
    mock_conversation_manager = MagicMock()
    mock_conversation_manager.get_conversation_history.return_value = []
    
    # 返回所有模擬服務
    return {
        "llm_service": mock_llm_service,
        "history_service": mock_history_service,
        "db_service": mock_db_service,
        "vector_store": mock_vector_store,
        "conversation_manager": mock_conversation_manager
    }


def test_basic_text_to_sql(mock_services):
    """測試基本的文本到SQL轉換"""
    # 創建服務實例並替換依賴
    with patch('textToSql.app.services.text_to_sql.llm_service', mock_services["llm_service"]), \
            patch('textToSql.app.services.text_to_sql.get_table_schema_description', return_value="測試資料庫模式"), \
            patch('textToSql.app.services.text_to_sql.HistoryService', return_value=mock_services["history_service"]), \
            patch('textToSql.app.services.text_to_sql.DatabaseService', return_value=mock_services["db_service"]), \
            patch('textToSql.app.services.text_to_sql.vector_store', mock_services["vector_store"]), \
            patch('textToSql.app.services.text_to_sql.conversation_manager', mock_services["conversation_manager"]), \
            patch('textToSql.app.services.text_to_sql.get_function_suggestion', return_value=None):
        
        # 創建服務實例
        service = TextToSQLService()
        
        # 執行測試
        result = service.text_to_sql("查詢測試表中ID為1的數據")
        
        # 驗證結果
        assert isinstance(result, SQLResult)
        assert result.sql == "SELECT * FROM test_table WHERE id = :id"
        assert result.explanation == "這是一個測試查詢"
        assert result.parameters == {"id": 1}
        
        # 驗證LLM服務調用
        mock_services["llm_service"].generate.assert_called_once()
        
        # 驗證歷史服務調用
        mock_services["history_service"].add_query.assert_called_once()


def test_error_handling(mock_services):
    """測試錯誤處理"""
    # 設置LLM服務返回錯誤
    error_response = MockLLMResponse(content="", is_error_val=True, error="測試錯誤")
    mock_services["llm_service"].generate.return_value = error_response
    
    # 創建服務實例並替換依賴
    with patch('textToSql.app.services.text_to_sql.llm_service', mock_services["llm_service"]), \
            patch('textToSql.app.services.text_to_sql.get_table_schema_description', return_value="測試資料庫模式"), \
            patch('textToSql.app.services.text_to_sql.HistoryService', return_value=mock_services["history_service"]), \
            patch('textToSql.app.services.text_to_sql.DatabaseService', return_value=mock_services["db_service"]), \
            patch('textToSql.app.services.text_to_sql.vector_store', mock_services["vector_store"]), \
            patch('textToSql.app.services.text_to_sql.conversation_manager', mock_services["conversation_manager"]), \
            patch('textToSql.app.services.text_to_sql.get_function_suggestion', return_value=None):
        
        # 創建服務實例
        service = TextToSQLService()
        
        # 執行測試
        result = service.text_to_sql("查詢測試表中ID為1的數據")
        
        # 驗證結果包含錯誤信息
        assert result.sql.startswith("--")
        assert "錯誤" in result.explanation
        
        # 驗證錯誤記錄到歷史
        mock_services["history_service"].add_query.assert_called_once()


def test_conversation_context(mock_services):
    """測試對話上下文處理"""
    # 設置對話歷史
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
    mock_services["conversation_manager"].get_conversation_history.return_value = mock_history
    
    # 創建服務實例並替換依賴
    with patch('textToSql.app.services.text_to_sql.llm_service', mock_services["llm_service"]), \
            patch('textToSql.app.services.text_to_sql.get_table_schema_description', return_value="測試資料庫模式"), \
            patch('textToSql.app.services.text_to_sql.HistoryService', return_value=mock_services["history_service"]), \
            patch('textToSql.app.services.text_to_sql.DatabaseService', return_value=mock_services["db_service"]), \
            patch('textToSql.app.services.text_to_sql.vector_store', mock_services["vector_store"]), \
            patch('textToSql.app.services.text_to_sql.conversation_manager', mock_services["conversation_manager"]), \
            patch('textToSql.app.services.text_to_sql.get_function_suggestion', return_value=None):
        
        # 創建服務實例
        service = TextToSQLService()
        
        # 模擬參考解析方法
        service._resolve_references = MagicMock(return_value=("查詢小明的預約記錄", {"他": "小明"}))
        
        # 執行測試
        result = service.text_to_sql("查詢他的預約記錄", session_id="test-session")
        
        # 驗證結果
        assert isinstance(result, SQLResult)
        
        # 驗證對話上下文處理
        mock_services["conversation_manager"].get_conversation_history.assert_called_once_with("test-session", limit=5)
        service._resolve_references.assert_called_once()
        
        # 驗證LLM服務調用包含上下文
        args, kwargs = mock_services["llm_service"].generate.call_args
        assert "system_prompt" in kwargs
        assert "當前對話的上下文" in kwargs.get("system_prompt", "")