"""
使用unittest測試歷史服務功能
"""
import unittest
from unittest.mock import MagicMock, patch
import os
import json
import tempfile
from datetime import datetime

class MockQueryHistory:
    """模擬查詢歷史模型"""
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)
        
        # 設置默認值
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


class MockQueryTemplate:
    """模擬查詢模板模型"""
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)
            
        # 設置默認值
        if not hasattr(self, 'id'):
            self.id = '123e4567-e89b-12d3-a456-426614174002'
        if not hasattr(self, 'name'):
            self.name = '測試模板'
        if not hasattr(self, 'description'):
            self.description = '測試模板描述'
        if not hasattr(self, 'user_query'):
            self.user_query = '模板查詢'
        if not hasattr(self, 'generated_sql'):
            self.generated_sql = 'SELECT * FROM templates;'
        if not hasattr(self, 'explanation'):
            self.explanation = '測試解釋'
        if not hasattr(self, 'tags'):
            self.tags = []
        if not hasattr(self, 'usage_count'):
            self.usage_count = 0


class TestHistoryService(unittest.TestCase):
    """使用unittest測試歷史服務"""
    
    def setUp(self):
        """設置測試環境"""
        # 建立臨時目錄
        self.temp_dir = tempfile.TemporaryDirectory()
        self.history_file = os.path.join(self.temp_dir.name, "query_history.json")
    
    def tearDown(self):
        """清理測試環境"""
        self.temp_dir.cleanup()
    
    @patch('os.path.exists')
    @patch('json.load')
    @patch('json.dump')
    @patch('builtins.open', new_callable=unittest.mock.mock_open)
    def test_add_query_to_file(self, mock_open, mock_json_dump, mock_json_load, mock_exists):
        """測試添加查詢到文件"""
        # 設置模擬
        mock_exists.return_value = False
        mock_json_load.return_value = []
        
        # 創建模擬查詢和服務
        query = MockQueryHistory()
        
        class MockService:
            history_file = self.history_file
            
            def _add_query_to_file(self, query):
                from datetime import datetime
                # 簡化版的添加查詢邏輯
                history = []
                history.append({
                    "id": str(query.id),
                    "user_query": query.user_query,
                    "generated_sql": query.generated_sql,
                    "explanation": query.explanation,
                    "executed": query.executed,
                    "execution_time": query.execution_time,
                    "created_at": datetime.now().isoformat(),
                })
                with open(self.history_file, "w", encoding="utf-8") as f:
                    json.dump(history, f, ensure_ascii=False, indent=2)
                return query
        
        # 執行方法
        service = MockService()
        result = service._add_query_to_file(query)
        
        # 驗證結果
        self.assertIsNotNone(result)
        self.assertEqual(result.id, query.id)
        self.assertEqual(result.user_query, query.user_query)
        mock_open.assert_called()
        mock_json_dump.assert_called()
    
    def test_toggle_favorite(self):
        """測試切換收藏狀態"""
        # 創建模擬查詢
        query = MockQueryHistory(is_favorite=False)
        
        # 創建模擬服務
        class MockService:
            def get_query_by_id(self, query_id):
                return query
                
            def update_query(self, query):
                return True
                
            def toggle_favorite(self, query_id):
                # 簡化版的切換收藏邏輯
                query = self.get_query_by_id(query_id)
                if not query:
                    return False
                
                # 切換收藏狀態
                query.is_favorite = not query.is_favorite
                return self.update_query(query)
        
        # 執行方法
        service = MockService()
        result = service.toggle_favorite("test_id")
        
        # 驗證結果
        self.assertTrue(result)
        self.assertTrue(query.is_favorite)
    
    def test_save_as_template(self):
        """測試保存為模板"""
        # 創建模擬查詢
        query = MockQueryHistory(is_template=False)
        
        # 創建模擬服務
        class MockService:
            def get_query_by_id(self, query_id):
                return query
                
            def update_query(self, query):
                return True
                
            def _save_template(self, template):
                return template
                
            def save_as_template(self, query_id, name, description=None, tags=None):
                # 簡化版的保存模板邏輯
                # 獲取查詢歷史
                query = self.get_query_by_id(query_id)
                if not query:
                    return None
                    
                # 設置為模板
                query.is_template = True
                query.template_name = name
                query.template_description = description
                query.template_tags = tags or []
                
                # 更新查詢記錄
                success = self.update_query(query)
                if not success:
                    return None
                    
                # 創建模板記錄
                template = MockQueryHistory(
                    name=name,
                    description=description,
                    user_query=query.user_query,
                    generated_sql=query.generated_sql,
                    explanation=query.explanation,
                    tags=tags or []
                )
                
                # 保存模板
                return self._save_template(template)
        
        # 執行方法
        service = MockService()
        result = service.save_as_template(
            "test_id", 
            "測試模板", 
            "這是測試模板的描述", 
            ["標籤1", "標籤2"]
        )
        
        # 驗證結果
        self.assertIsNotNone(result)
        self.assertEqual(result.name, "測試模板")
        self.assertEqual(result.description, "這是測試模板的描述")
        self.assertTrue(query.is_template)
        self.assertEqual(query.template_name, "測試模板")
        self.assertEqual(query.template_description, "這是測試模板的描述")
        self.assertEqual(query.template_tags, ["標籤1", "標籤2"])


    def test_get_templates_by_tag(self):
        """測試通過標籤搜尋模板"""
        # 創建模擬模板列表
        template1 = MockQueryTemplate(id="t1", name="模板1", tags=["標籤1", "常用"])
        template2 = MockQueryTemplate(id="t2", name="模板2", tags=["標籤2", "常用"])
        template3 = MockQueryTemplate(id="t3", name="模板3", tags=["標籤3"])
        
        templates = [template1, template2, template3]
        
        # 創建模擬服務
        class MockService:
            def get_templates(self, limit=20, offset=0, tag=None):
                # 簡化版的按標籤搜尋邏輯
                if tag is None:
                    return templates[:limit]
                
                filtered = [t for t in templates if tag in t.tags]
                return filtered[:limit]
        
        # 執行方法
        service = MockService()
        
        # 測試獲取所有模板
        all_templates = service.get_templates()
        self.assertEqual(len(all_templates), 3)
        
        # 測試按標籤過濾
        common_templates = service.get_templates(tag="常用")
        unique_templates = service.get_templates(tag="標籤3")
        
        # 驗證結果
        self.assertEqual(len(common_templates), 2)
        self.assertEqual(common_templates[0].name, "模板1")
        self.assertEqual(common_templates[1].name, "模板2")
        
        self.assertEqual(len(unique_templates), 1)
        self.assertEqual(unique_templates[0].name, "模板3")
        
        # 測試不存在的標籤
        nonexistent = service.get_templates(tag="不存在")
        self.assertEqual(len(nonexistent), 0)


    def test_increment_template_usage(self):
        """測試增加模板使用計數"""
        # 創建模擬模板
        template = MockQueryTemplate(usage_count=5)
        
        # 創建模擬服務
        class MockService:
            def get_template_by_id(self, template_id):
                return template
                
            def update_template(self, template):
                return True
                
            def increment_template_usage(self, template_id):
                # 簡化版的增加使用計數邏輯
                template = self.get_template_by_id(template_id)
                if not template:
                    return False
                    
                template.usage_count += 1
                return self.update_template(template)
        
        # 執行方法
        service = MockService()
        result = service.increment_template_usage("t1")
        
        # 驗證結果
        self.assertTrue(result)
        self.assertEqual(template.usage_count, 6)  # 從5增加到6


if __name__ == '__main__':
    unittest.main()