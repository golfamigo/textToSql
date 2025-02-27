"""
測試文件存儲模式
"""
import os
import json
import pytest
from app.services.history_service import HistoryService
from app.models.query_history import QueryHistoryModel, QueryTemplateModel


class TestFileStorage:
    """測試文件存儲模式下的功能"""
    
    @pytest.fixture
    def file_history_service(self, tmp_path):
        """創建使用臨時目錄的文件存儲服務"""
        service = HistoryService(use_db=False)
        service.history_file = str(tmp_path / "query_history.json")
        service.templates_file = str(tmp_path / "query_templates.json")
        return service
    
    def test_file_add_query(self, file_history_service, sample_query_history):
        """測試文件模式下添加查詢"""
        # 添加查詢
        result = file_history_service.add_query(sample_query_history)
        
        # 驗證添加是否成功
        assert result is not None
        assert result.id is not None
        
        # 驗證文件是否創建
        assert os.path.exists(file_history_service.history_file)
        
        # 讀取文件內容
        with open(file_history_service.history_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        # 驗證數據
        assert len(data) == 1
        assert data[0]["user_query"] == sample_query_history.user_query
        assert data[0]["generated_sql"] == sample_query_history.generated_sql
    
    def test_file_get_query_by_id(self, file_history_service, sample_query_history):
        """測試文件模式下根據ID獲取查詢"""
        # 添加查詢
        result = file_history_service.add_query(sample_query_history)
        query_id = str(result.id)
        
        # 獲取查詢
        query = file_history_service.get_query_by_id(query_id)
        
        # 驗證
        assert query is not None
        assert query.id == query_id
        assert query.user_query == sample_query_history.user_query
    
    def test_file_toggle_favorite(self, file_history_service, sample_query_history):
        """測試文件模式下的收藏功能"""
        # 添加查詢
        result = file_history_service.add_query(sample_query_history)
        query_id = str(result.id)
        
        # 收藏
        success = file_history_service.toggle_favorite(query_id)
        assert success is True
        
        # 驗證狀態
        query = file_history_service.get_query_by_id(query_id)
        assert query.is_favorite is True
        
        # 驗證文件內容
        with open(file_history_service.history_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        # 找到對應記錄
        file_record = next((item for item in data if item["id"] == query_id), None)
        assert file_record is not None
        assert file_record["is_favorite"] is True
    
    def test_file_save_template(self, file_history_service, sample_query_history):
        """測試文件模式下保存模板"""
        # 添加查詢
        result = file_history_service.add_query(sample_query_history)
        query_id = str(result.id)
        
        # 保存為模板
        template = file_history_service.save_as_template(
            query_id=query_id,
            name="文件模板測試",
            description="測試文件存儲模式下的模板功能",
            tags=["文件", "測試"]
        )
        
        # 驗證
        assert template is not None
        assert template.name == "文件模板測試"
        
        # 驗證模板文件
        assert os.path.exists(file_history_service.templates_file)
        with open(file_history_service.templates_file, "r", encoding="utf-8") as f:
            templates_data = json.load(f)
        
        assert len(templates_data) == 1
        assert templates_data[0]["name"] == "文件模板測試"
        assert templates_data[0]["tags"] == ["文件", "測試"]
    
    def test_file_get_templates(self, file_history_service, sample_query_history):
        """測試文件模式下獲取模板列表"""
        # 添加多個模板
        for i in range(3):
            query = QueryHistoryModel(
                user_query=f"文件模板查詢 {i}",
                generated_sql=f"SELECT * FROM file_test WHERE id = {i};",
                explanation=f"文件模式測試 {i}",
                executed=True
            )
            result = file_history_service.add_query(query)
            file_history_service.save_as_template(
                query_id=str(result.id),
                name=f"文件模板 {i}",
                description=f"文件模式測試描述 {i}",
                tags=[f"file{i}", "test"]
            )
        
        # 獲取所有模板
        templates = file_history_service.get_templates()
        assert len(templates) == 3
        
        # 按標籤過濾
        test_templates = file_history_service.get_templates(tag="test")
        assert len(test_templates) == 3
        
        file1_templates = file_history_service.get_templates(tag="file1")
        assert len(file1_templates) == 1
        assert file1_templates[0].name == "文件模板 1"
    
    def test_file_delete_template(self, file_history_service, sample_query_history):
        """測試文件模式下刪除模板"""
        # 添加模板
        query = QueryHistoryModel(
            user_query="要刪除的文件模板查詢",
            generated_sql="SELECT * FROM file_test WHERE delete = true;",
            explanation="這個模板將被從文件中刪除",
            executed=True
        )
        result = file_history_service.add_query(query)
        template = file_history_service.save_as_template(
            query_id=str(result.id),
            name="要刪除的文件模板",
            description="這個模板將被刪除"
        )
        
        template_id = str(template.id)
        
        # 確認模板已創建
        assert os.path.exists(file_history_service.templates_file)
        with open(file_history_service.templates_file, "r", encoding="utf-8") as f:
            templates_before = json.load(f)
        assert len(templates_before) == 1
        
        # 刪除模板
        success = file_history_service.delete_template(template_id)
        assert success is True
        
        # 驗證模板已從文件刪除
        with open(file_history_service.templates_file, "r", encoding="utf-8") as f:
            templates_after = json.load(f)
        assert len(templates_after) == 0