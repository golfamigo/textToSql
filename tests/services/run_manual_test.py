#!/usr/bin/env python3
"""
手動測試腳本，專門用於測試向量存儲
"""

import os
import sys
import unittest
import importlib.util

# 添加項目根目錄到 Python 路徑
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
sys.path.insert(0, project_root)

# 導入模擬設置模塊
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)
import mock_settings

# 設置環境變量以繞過配置驗證
os.environ["OPENAI_API_KEY"] = "dummy"
os.environ["ANTHROPIC_API_KEY"] = "dummy"
os.environ["GOOGLE_API_KEY"] = "dummy"
os.environ["AZURE_OPENAI_API_KEY"] = "dummy"
os.environ["AZURE_OPENAI_ENDPOINT"] = "dummy"
os.environ["AZURE_DEPLOYMENT_NAME"] = "dummy"

# 在導入其他模塊前先模擬設置
sys.modules['app.utils.config'] = mock_settings

# 直接加載並運行測試
if __name__ == "__main__":
    # 載入測試模塊
    test_file = os.path.join(current_dir, "test_vector_store.py")
    
    # 通過文件路徑導入模塊
    spec = importlib.util.spec_from_file_location("test_vector_store", test_file)
    test_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(test_module)
    
    # 運行測試
    unittest.main(module=test_module)