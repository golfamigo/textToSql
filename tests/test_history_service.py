"""
測試查詢歷史服務
"""
import pytest
import os
import json
from typing import List, Optional
from app.services.history_service import HistoryService
from app.models.query_history import QueryHistoryModel, QueryTemplateModel


class TestHistoryService:
    """測試歷史服務功能"""

    def test_add_query(self, history_service, sample_query_history):
        """測試添加查詢功能"""
        # 添加查詢
        result = history_service.add_query(sample_query_history)
        
        # 驗證添加是否成功
        assert result is not None
        assert result.id is not None
        assert result.user_query == sample_query_history.user_query
        assert result.generated_sql == sample_query_history.generated_sql
        
        # 檢查是否能夠查詢到
        saved_query = history_service.get_query_by_id(str(result.id))
        assert saved_query is not None
        assert saved_query.user_query == sample_query_history.user_query
        
    def test_get_history(self, history_service, sample_query_history):
        """測試獲取歷史列表功能"""
        # 添加多個查詢
        for i in range(3):
            modified_query = QueryHistoryModel(
                user_query=f"測試查詢 {i}",
                generated_sql=f"SELECT * FROM test WHERE id = {i};",
                explanation=f"這是第 {i} 個測試查詢",
                executed=True
            )
            history_service.add_query(modified_query)
        
        # 獲取歷史記錄
        history = history_service.get_history(limit=10)
        
        # 驗證
        assert len(history) == 3
        # 應該按照創建時間倒序排列
        assert history[0].user_query.startswith("測試查詢")
        
    def test_toggle_favorite(self, history_service, sample_query_history):
        """測試收藏功能"""
        # 添加查詢
        result = history_service.add_query(sample_query_history)
        query_id = str(result.id)
        
        # 切換收藏狀態為 True
        success = history_service.toggle_favorite(query_id)
        assert success is True
        
        # 驗證狀態已更改
        query = history_service.get_query_by_id(query_id)
        assert query.is_favorite is True
        
        # 再次切換狀態為 False
        history_service.toggle_favorite(query_id)
        query = history_service.get_query_by_id(query_id)
        assert query.is_favorite is False
        
    def test_get_favorites(self, history_service):
        """測試獲取收藏列表"""
        # 添加多個查詢，部分設為收藏
        for i in range(5):
            query = QueryHistoryModel(
                user_query=f"查詢 {i}",
                generated_sql=f"SELECT * FROM test WHERE id = {i};",
                explanation=f"測試查詢 {i}",
                executed=True,
                is_favorite=i % 2 == 0  # 偶數索引的設為收藏
            )
            history_service.add_query(query)
        
        # 獲取收藏列表
        favorites = history_service.get_favorites()
        
        # 驗證
        assert len(favorites) == 3  # 應該有3個收藏項 (0, 2, 4)
        for fav in favorites:
            assert fav.is_favorite is True
    
    def test_save_as_template(self, history_service, sample_query_history):
        """測試保存為模板功能"""
        # 添加查詢
        result = history_service.add_query(sample_query_history)
        query_id = str(result.id)
        
        # 保存為模板
        template = history_service.save_as_template(
            query_id=query_id,
            name="測試模板",
            description="這是一個測試模板",
            tags=["測試", "模板"]
        )
        
        # 驗證
        assert template is not None
        assert template.name == "測試模板"
        assert template.description == "這是一個測試模板"
        assert "測試" in template.tags and "模板" in template.tags
        
        # 驗證原查詢記錄已更新
        query = history_service.get_query_by_id(query_id)
        assert query.is_template is True
        assert query.template_name == "測試模板"
        
    def test_get_templates(self, history_service, sample_query_history):
        """測試獲取模板列表"""
        # 添加查詢並轉為模板
        for i in range(3):
            query = QueryHistoryModel(
                user_query=f"模板查詢 {i}",
                generated_sql=f"SELECT * FROM templates WHERE id = {i};",
                explanation=f"模板說明 {i}",
                executed=True
            )
            result = history_service.add_query(query)
            history_service.save_as_template(
                query_id=str(result.id),
                name=f"測試模板 {i}",
                description=f"這是測試模板 {i}",
                tags=[f"tag{i}", "common"]
            )
        
        # 獲取所有模板
        templates = history_service.get_templates()
        assert len(templates) == 3
        
        # 按標籤篩選
        tag1_templates = history_service.get_templates(tag="tag1")
        assert len(tag1_templates) == 1
        assert tag1_templates[0].name == "測試模板 1"
        
        # 測試通用標籤
        common_templates = history_service.get_templates(tag="common")
        assert len(common_templates) == 3
        
    def test_update_template(self, history_service, sample_query_history):
        """測試更新模板功能"""
        # 創建模板
        result = history_service.add_query(sample_query_history)
        template = history_service.save_as_template(
            query_id=str(result.id),
            name="原始模板",
            description="原始描述",
            tags=["原始標籤"]
        )
        
        # 更新模板
        template.name = "更新後的模板"
        template.description = "更新後的描述"
        template.tags = ["更新後的標籤"]
        success = history_service.update_template(template)
        
        # 驗證
        assert success is True
        updated = history_service.get_template_by_id(str(template.id))
        assert updated.name == "更新後的模板"
        assert updated.description == "更新後的描述"
        assert updated.tags == ["更新後的標籤"]
        
    def test_delete_template(self, history_service, sample_query_history):
        """測試刪除模板功能"""
        # 創建模板
        result = history_service.add_query(sample_query_history)
        template = history_service.save_as_template(
            query_id=str(result.id),
            name="要刪除的模板",
            description="這個模板將被刪除"
        )
        
        template_id = str(template.id)
        
        # 刪除前確認存在
        assert history_service.get_template_by_id(template_id) is not None
        
        # 刪除模板
        success = history_service.delete_template(template_id)
        assert success is True
        
        # 確認已刪除
        assert history_service.get_template_by_id(template_id) is None
        
    def test_increment_template_usage(self, history_service, sample_query_history):
        """測試增加模板使用計數功能"""
        # 創建模板
        result = history_service.add_query(sample_query_history)
        template = history_service.save_as_template(
            query_id=str(result.id),
            name="使用計數測試"
        )
        
        template_id = str(template.id)
        
        # 初始使用次數應為0
        initial = history_service.get_template_by_id(template_id)
        assert initial.usage_count == 0
        
        # 增加使用計數
        success = history_service.increment_template_usage(template_id)
        assert success is True
        
        # 驗證計數已增加
        updated = history_service.get_template_by_id(template_id)
        assert updated.usage_count == 1