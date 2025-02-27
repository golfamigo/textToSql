#!/usr/bin/env python
"""
用於運行 unittest 風格測試的腳本
"""
import unittest
import sys
import os
import warnings
from unittest.mock import patch, MagicMock

# 忽略警告
warnings.filterwarnings('ignore')

# 設置路徑
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(script_dir, '../../')))

# 模擬應用程序模塊
sys.modules['app'] = MagicMock()
sys.modules['app.api'] = MagicMock()
sys.modules['app.api'].app = MagicMock()
sys.modules['app.services'] = MagicMock()
sys.modules['app.services.text_to_sql'] = MagicMock()
sys.modules['app.services.database_service'] = MagicMock()
sys.modules['app.services.vector_store'] = MagicMock()
sys.modules['app.services.llm_service'] = MagicMock()
sys.modules['app.models'] = MagicMock()

# 從 simple_test.py 導入測試案例
from simple_test import TestAPISimple

if __name__ == '__main__':
    print("運行 unittest 測試 (使用簡單的測試案例)")
    
    # 創建測試套件
    suite = unittest.TestLoader().loadTestsFromTestCase(TestAPISimple)
    
    # 運行測試
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    
    # 根據測試結果設置退出代碼
    sys.exit(len(result.errors) + len(result.failures))