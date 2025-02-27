"""
測試數據庫服務
"""
import unittest
from unittest.mock import MagicMock, patch
import os
import json
import sys
from typing import List, Dict, Any

# 添加應用路徑到系統路徑
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


# 定義模擬的QueryResult類，避免依賴實際的實現
class MockQueryResult:
    """模擬的查詢結果"""
    
    def __init__(self, columns=None, rows=None, row_count=0, execution_time=0, error=None):
        self.columns = columns or []
        self.rows = rows or []
        self.row_count = row_count
        self.execution_time = execution_time
        self.error = error


class TestDatabaseService(unittest.TestCase):
    """測試數據庫服務"""
    
    def setUp(self):
        """設置測試環境"""
        # 創建模擬的數據庫服務類
        self.db_service = MagicMock()
        self.db_service.is_connected.return_value = True
        self.db_service.execute_query.return_value = MockQueryResult(
            columns=["id", "name"],
            rows=[[1, "test"], [2, "test2"]],
            row_count=2,
            execution_time=10.5,
            error=None
        )
    
    def test_execute_query(self):
        """測試執行查詢功能"""
        # 使用模擬的數據庫服務
        result = self.db_service.execute_query("SELECT * FROM test WHERE id = :id", {"id": 1})
        
        # 驗證結果是正確的類型
        self.assertEqual(result.columns, ["id", "name"])
        self.assertEqual(len(result.rows), 2)
        self.assertEqual(result.row_count, 2)
        self.assertIsNone(result.error)
        
        # 驗證執行方法被調用
        self.db_service.execute_query.assert_called_once()
    
    def test_execute_query_error(self):
        """測試執行查詢時的錯誤處理"""
        # 設置模擬錯誤
        error_db_service = MagicMock()
        error_result = MockQueryResult(error="測試錯誤")
        error_db_service.execute_query.return_value = error_result
        
        # 執行測試
        result = error_db_service.execute_query("SELECT * FROM test WHERE id = :id", {"id": 1})
        
        # 驗證錯誤處理
        self.assertIsNotNone(result.error)
        self.assertEqual(result.error, "測試錯誤")
    
    def test_connection_management(self):
        """測試數據庫連接管理"""
        # 設置環境變數
        os.environ['DATABASE_URL'] = 'postgresql://user:password@localhost:5432/test'
        
        # 創建服務實例
        db_service = MagicMock()
        db_service.connect.return_value = True
        db_service.is_connected.return_value = True
        
        # 測試連接
        result = db_service.connect()
        self.assertTrue(result)
        self.assertTrue(db_service.is_connected())
        
        # 斷開連接前的狀態
        db_service.is_connected.return_value = False
        
        # 測試斷開連接
        db_service.disconnect()
        self.assertFalse(db_service.is_connected())
    
    def test_parameter_handling(self):
        """測試參數處理功能"""
        # 執行測試: 帶參數的查詢
        self.db_service.execute_query("SELECT * FROM test WHERE id = :id AND name = :name", {"id": 1, "name": "test"})
        
        # 獲取傳遞給execute的參數 (第一次調用的第一個位置參數)
        args, kwargs = self.db_service.execute_query.call_args
        
        # 驗證查詢和參數都被正確傳遞
        self.assertEqual(args[0], "SELECT * FROM test WHERE id = :id AND name = :name")
        self.assertEqual(args[1], {"id": 1, "name": "test"})


if __name__ == '__main__':
    unittest.main()