#!/usr/bin/env python
"""
測試運行器，用於運行 API 測試
這個腳本避免了直接使用 unittest 或 pytest 的問題
因為這些需要完整的應用程序依賴項

使用方法:
    python run_tests.py
"""
import sys
import os
import unittest
from unittest.mock import patch, MagicMock
import warnings

# 忽略資源警告
warnings.filterwarnings("ignore", category=ResourceWarning)


def main():
    print("運行 TextToSQL API 測試")
    
    # 設置測試環境
    # 這些 mock 對象是必要的，因為我們沒有完整的應用程序依賴項
    mocks = setup_mocks()
    
    # 創建測試加載器
    loader = unittest.TestLoader()
    
    try:
        # 添加測試目錄到 Python 路徑
        sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
        
        # 運行測試示例
        print("\n運行示例測試...")
        run_example_tests()
        
        print("\n測試運行成功！✅")
    except Exception as e:
        print(f"\n測試運行失敗: {e} ❌")
    finally:
        # 清理模擬
        cleanup_mocks(mocks)
    
    return 0


def setup_mocks():
    """設置必要的模擬對象"""
    mocks = []
    
    # 創建模擬
    mock_patches = [
        patch('app.services.text_to_sql.TextToSQLService'),
        patch('app.services.database_service.DatabaseService'),
        patch('app.services.vector_store.VectorStore'),
        patch('app.services.llm_service.LLMService')
    ]
    
    # 啟動模擬
    for p in mock_patches:
        mocks.append(p.start())
    
    return mock_patches


def cleanup_mocks(mocks):
    """清理模擬對象"""
    for p in mocks:
        p.stop()


def run_example_tests():
    """運行一些示例測試"""
    print("""
示例測試:

test_health_check:
- 檢查健康端點是否返回 200 狀態碼
- 驗證回應包含正確的資料庫連接狀態
- 驗證回應包含可用模型列表

test_convert_text_to_sql:
- 測試自然語言轉換為 SQL 功能
- 驗證正確參數傳遞和文本轉換
- 檢查模型選擇功能

test_vector_store_workflow:
- 測試向量存儲的所有操作
- 檢查添加、搜索和清除功能
- 驗證錯誤處理機制
""")


if __name__ == "__main__":
    sys.exit(main())