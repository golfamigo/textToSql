"""
測試查詢歷史服務 - 無依賴版本
"""
import pytest
import os
import json
import tempfile
from uuid import uuid4
from datetime import datetime
from typing import Dict, Any, List, Optional

from app.models.query_history import QueryHistoryModel, QueryTemplateModel
from app.services.history_service import QueryHistory, QueryTemplate, HistoryService


class MockSession:
    """模擬SQLAlchemy會話"""
    
    def __init__(self):
        self.records = []
        self.query_filter = None
        self.query_order = None
        self.query_limit = None
        self.query_offset = None
        self.committed = False
    
    def query(self, model):
        self.query_model = model
        return self
    
    def filter(self, condition):
        self.query_filter = condition
        return self
    
    def order_by(self, order):
        self.query_order = order
        return self
    
    def limit(self, limit):
        self.query_limit = limit
        return self
    
    def offset(self, offset):
        self.query_offset = offset
        return self
    
    def all(self):
        return self.records
    
    def first(self):
        return self.records[0] if self.records else None
    
    def add(self, record):
        self.records.append(record)
    
    def commit(self):
        self.committed = True
    
    def close(self):
        pass
    
    def __enter__(self):
        return self
    
    def __exit__(self, *args):
        pass


class MockHistoryService(HistoryService):
    """模擬歷史服務，避免依賴資料庫和外部文件"""
    
    def __init__(self, use_db=True):
        self.use_db = use_db
        self.session = MockSession()
        self.history_data = []
        self.templates_data = []
        
        # 創建臨時文件
        self.temp_dir = tempfile.TemporaryDirectory()
        self.history_file = os.path.join(self.temp_dir.name, "query_history.json")
        self.templates_file = os.path.join(self.temp_dir.name, "query_templates.json")
        
        # 為資料庫模式設置模擬數據
        if use_db:
            self.Session = lambda: self.session
    
    def add_mock_query(self, query_model):
        if self.use_db:
            record = QueryHistory(
                id=query_model.id,
                user_query=query_model.user_query,
                generated_sql=query_model.generated_sql,
                explanation=query_model.explanation,
                executed=query_model.executed,
                execution_time=query_model.execution_time,
                created_at=datetime.now()
            )
            self.session.records.append(record)
        else:
            self.history_data.append({
                "id": str(query_model.id),
                "user_query": query_model.user_query,
                "generated_sql": query_model.generated_sql,
                "explanation": query_model.explanation,
                "executed": query_model.executed,
                "execution_time": query_model.execution_time,
                "created_at": datetime.now().isoformat(),
                "is_favorite": query_model.is_favorite
            })
            with open(self.history_file, "w", encoding="utf-8") as f:
                json.dump(self.history_data, f)


class TestHistoryServiceIsolated:
    """測試歷史服務，使用模擬的數據而非實際資料庫"""
    
    @pytest.fixture
    def history_service(self):
        """創建一個歷史服務實例，使用模擬的會話"""
        return MockHistoryService(use_db=True)
    
    @pytest.fixture
    def file_history_service(self):
        """創建一個基於文件的歷史服務實例"""
        return MockHistoryService(use_db=False)
    
    @pytest.fixture
    def sample_query(self):
        """創建一個測試查詢模型"""
        return QueryHistoryModel(
            user_query="測試查詢",
            generated_sql="SELECT * FROM test;",
            explanation="這是一個測試查詢",
            executed=True,
            execution_time=10.5
        )
    
    def test_add_query(self, history_service, sample_query):
        """測試添加查詢功能"""
        result = history_service.add_query(sample_query)
        
        # 驗證返回結果
        assert result is not None
        assert result.id is not None
        assert result.user_query == sample_query.user_query
        
        # 驗證添加到模擬會話中
        assert len(history_service.session.records) == 1
        assert history_service.session.records[0].user_query == sample_query.user_query
        assert history_service.session.committed is True
    
    def test_file_add_query(self, file_history_service, sample_query):
        """測試添加查詢到文件"""
        result = file_history_service.add_query(sample_query)
        
        # 驗證返回結果
        assert result is not None
        assert result.id is not None
        
        # 驗證文件已創建
        assert os.path.exists(file_history_service.history_file)
        
        # 讀取文件內容
        with open(file_history_service.history_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        # 驗證數據
        assert len(data) == 1
        assert data[0]["user_query"] == sample_query.user_query