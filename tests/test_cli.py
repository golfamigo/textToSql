"""
測試 CLI 功能
"""
import pytest
from unittest.mock import patch, MagicMock
from click.testing import CliRunner
from app.cli import cli, list_history, list_favorites, toggle_favorite, list_templates, save_template
from app.models.query_history import QueryHistoryModel, QueryTemplateModel


class TestCliCommands:
    """測試 CLI 命令"""
    
    @pytest.fixture
    def cli_runner(self):
        """建立 CLI 測試運行器"""
        return CliRunner()
    
    @pytest.fixture
    def mock_history_service(self):
        """模擬歷史服務"""
        with patch('app.cli.HistoryService') as mock:
            # 創建模擬實例
            instance = MagicMock()
            mock.return_value = instance
            
            # 添加模擬查詢歷史數據
            query1 = QueryHistoryModel(
                id="1",
                user_query="測試查詢 1",
                generated_sql="SELECT * FROM test WHERE id = 1;",
                explanation="測試說明 1",
                executed=True,
                execution_time=10.5,
                is_favorite=True
            )
            query2 = QueryHistoryModel(
                id="2",
                user_query="測試查詢 2",
                generated_sql="SELECT * FROM test WHERE id = 2;",
                explanation="測試說明 2",
                executed=True,
                execution_time=15.2,
                is_favorite=False
            )
            
            # 添加模擬模板數據
            template1 = QueryTemplateModel(
                id="t1",
                name="測試模板 1",
                description="測試模板描述 1",
                user_query="模板查詢 1",
                generated_sql="SELECT * FROM templates WHERE id = 1;",
                tags=["test", "template"],
                usage_count=5
            )
            template2 = QueryTemplateModel(
                id="t2",
                name="測試模板 2",
                description="測試模板描述 2",
                user_query="模板查詢 2",
                generated_sql="SELECT * FROM templates WHERE id = 2;",
                tags=["example"],
                usage_count=2
            )
            
            # 設置模擬方法返回值
            instance.get_history.return_value = [query1, query2]
            instance.get_favorites.return_value = [query1]
            instance.get_templates.return_value = [template1, template2]
            instance.get_query_by_id.return_value = query1
            instance.toggle_favorite.return_value = True
            instance.save_as_template.return_value = template1
            
            yield instance
    
    def test_list_history(self, cli_runner, mock_history_service):
        """測試列出歷史命令"""
        # 執行命令
        result = cli_runner.invoke(list_history, [])
        
        # 驗證結果
        assert result.exit_code == 0
        assert "測試查詢 1" in result.output
        assert "測試查詢 2" in result.output
        
        # 驗證調用
        mock_history_service.get_history.assert_called_once()
    
    def test_list_favorites(self, cli_runner, mock_history_service):
        """測試列出收藏命令"""
        # 執行命令
        result = cli_runner.invoke(list_favorites, [])
        
        # 驗證結果
        assert result.exit_code == 0
        assert "測試查詢 1" in result.output
        assert "測試查詢 2" not in result.output  # 這個不是收藏的
        
        # 驗證調用
        mock_history_service.get_favorites.assert_called_once()
    
    def test_toggle_favorite(self, cli_runner, mock_history_service):
        """測試切換收藏狀態命令"""
        # 執行命令
        result = cli_runner.invoke(toggle_favorite, ["1"])
        
        # 驗證結果
        assert result.exit_code == 0
        assert "已成功切換收藏狀態" in result.output
        
        # 驗證調用
        mock_history_service.toggle_favorite.assert_called_once_with("1")
    
    def test_list_templates(self, cli_runner, mock_history_service):
        """測試列出模板命令"""
        # 執行命令
        result = cli_runner.invoke(list_templates, [])
        
        # 驗證結果
        assert result.exit_code == 0
        assert "測試模板 1" in result.output
        assert "測試模板 2" in result.output
        assert "模板查詢 1" in result.output
        
        # 驗證調用
        mock_history_service.get_templates.assert_called_once()
    
    def test_save_template(self, cli_runner, mock_history_service):
        """測試保存模板命令"""
        # 執行命令
        result = cli_runner.invoke(save_template, [
            "1", "--name", "新模板測試", "--description", "測試描述", "--tags", "test,cli"
        ])
        
        # 驗證結果
        assert result.exit_code == 0
        assert "成功將查詢保存為模板" in result.output
        
        # 驗證調用
        mock_history_service.save_as_template.assert_called_once_with(
            query_id="1", 
            name="新模板測試", 
            description="測試描述", 
            tags=["test", "cli"]
        )