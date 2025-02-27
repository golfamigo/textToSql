"""
測試查詢歷史服務 - 完全獨立模擬版本
"""
import pytest
import os
import json
import tempfile
from unittest.mock import MagicMock, patch
from datetime import datetime
from uuid import UUID

class MockQueryHistoryModel:
    """模擬查詢歷史模型"""
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)
        if not hasattr(self, 'id'):
            self.id = '123e4567-e89b-12d3-a456-426614174001'
        if not hasattr(self, 'user_query'):
            self.user_query = '測試查詢'
        if not hasattr(self, 'generated_sql'):
            self.generated_sql = 'SELECT * FROM test;'
        if not hasattr(self, 'explanation'):
            self.explanation = '這是測試查詢的解釋'
        if not hasattr(self, 'executed'):
            self.executed = True
        if not hasattr(self, 'execution_time'):
            self.execution_time = 10.5
        if not hasattr(self, 'is_favorite'):
            self.is_favorite = False
        if not hasattr(self, 'is_template'):
            self.is_template = False
        if not hasattr(self, 'template_name'):
            self.template_name = None
        if not hasattr(self, 'template_description'):
            self.template_description = None
        if not hasattr(self, 'template_tags'):
            self.template_tags = []

class MockQueryTemplateModel:
    """模擬查詢模板模型"""
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)
        if not hasattr(self, 'id'):
            self.id = '123e4567-e89b-12d3-a456-426614174002'
        if not hasattr(self, 'name'):
            self.name = '測試模板'
        if not hasattr(self, 'description'):
            self.description = '測試模板的描述'
        if not hasattr(self, 'user_query'):
            self.user_query = '模板查詢'
        if not hasattr(self, 'generated_sql'):
            self.generated_sql = 'SELECT * FROM templates;'
        if not hasattr(self, 'explanation'):
            self.explanation = '這是模板查詢的解釋'
        if not hasattr(self, 'tags'):
            self.tags = ['測試', '模板']
        if not hasattr(self, 'usage_count'):
            self.usage_count = 0

@pytest.fixture
def temp_dir():
    """建立臨時目錄"""
    with tempfile.TemporaryDirectory() as tmpdirname:
        yield tmpdirname

class TestHistoryServiceMock:
    """完全模擬的歷史服務測試"""
    
    def test_add_query_to_file(self, temp_dir):
        """測試添加查詢到文件"""
        # 建立測試文件路徑
        history_file = os.path.join(temp_dir, "query_history.json")
        
        # 模擬查詢模型
        query = MockQueryHistoryModel()
        
        # 調用_add_query_to_file方法
        with patch('app.services.history_service.os.path.exists', return_value=False):
            with patch('app.services.history_service.open', create=True) as mock_open:
                mock_open.return_value.__enter__.return_value = MagicMock()
                with patch('app.services.history_service.json.dump') as mock_json_dump:
                    # 模擬歷史服務
                    mock_service = MagicMock()
                    mock_service.history_file = history_file
                    
                    # 執行方法
                    from app.services.history_service import HistoryService
                    # 直接調用內部方法
                    result = HistoryService._add_query_to_file(mock_service, query)
                    
                    # 驗證結果
                    assert result is not None
                    assert result.id == query.id
                    assert result.user_query == query.user_query
                    assert mock_json_dump.called
    
    def test_toggle_favorite(self):
        """測試切換收藏狀態"""
        # 創建模擬查詢
        query = MockQueryHistoryModel(is_favorite=False)
        
        # 創建模擬服務
        mock_service = MagicMock()
        mock_service.get_query_by_id.return_value = query
        mock_service.update_query.return_value = True
        
        # 測試切換收藏
        from app.services.history_service import HistoryService
        result = HistoryService.toggle_favorite(mock_service, "test_id")
        
        # 驗證結果
        assert result is True
        assert query.is_favorite is True
        mock_service.get_query_by_id.assert_called_once_with("test_id")
        mock_service.update_query.assert_called_once_with(query)
    
    def test_save_as_template(self):
        """測試保存為模板"""
        # 創建模擬查詢
        query = MockQueryHistoryModel(is_template=False)
        
        # 創建模擬服務
        mock_service = MagicMock()
        mock_service.get_query_by_id.return_value = query
        mock_service.update_query.return_value = True
        mock_service._save_template.return_value = MockQueryTemplateModel(
            name="新模板", 
            description="模板描述"
        )
        
        # 測試保存為模板
        from app.services.history_service import HistoryService
        result = HistoryService.save_as_template(
            mock_service, 
            "test_id", 
            "新模板", 
            "模板描述", 
            ["標籤1", "標籤2"]
        )
        
        # 驗證結果
        assert result is not None
        assert result.name == "新模板"
        assert result.description == "模板描述"
        assert query.is_template is True
        assert query.template_name == "新模板"
        assert query.template_description == "模板描述"
        assert query.template_tags == ["標籤1", "標籤2"]
        mock_service.get_query_by_id.assert_called_once_with("test_id")
        mock_service.update_query.assert_called_once_with(query)
        mock_service._save_template.assert_called_once()