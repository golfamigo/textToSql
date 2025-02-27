#!/usr/bin/env python3
"""
單一測試文件運行器，用於單獨運行向量存儲服務測試
"""
import unittest
import os
import sys
import tempfile
import shutil
from unittest.mock import patch
import importlib.util


def run_test_file(test_file_path):
    """運行單個測試文件"""
    # 添加項目根目錄到 Python 路徑
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
    sys.path.insert(0, project_root)
    
    # 創建臨時目錄用於測試
    temp_dir = tempfile.mkdtemp()
    
    try:
        # 設置環境變量以繞過配置驗證
        env_vars = {
            "DUMMY_KEY": "dummy",
            "OPENAI_API_KEY": "dummy",
            "ANTHROPIC_API_KEY": "dummy",
            "GOOGLE_API_KEY": "dummy",
            "AZURE_OPENAI_API_KEY": "dummy",
            "AZURE_OPENAI_ENDPOINT": "dummy",
            "AZURE_DEPLOYMENT_NAME": "dummy"
        }
        
        # 使用上述環境變量運行測試
        with patch.dict(os.environ, env_vars):
            if os.path.exists(test_file_path):
                # 動態加載測試模塊
                module_name = os.path.basename(test_file_path).replace('.py', '')
                test_dir = os.path.dirname(os.path.abspath(test_file_path))
                sys.path.insert(0, test_dir)
                
                # 通過文件路徑導入模塊
                spec = importlib.util.spec_from_file_location(module_name, test_file_path)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                
                # 從導入的模塊加載測試
                loader = unittest.TestLoader()
                suite = loader.loadTestsFromModule(module)
                
                # 運行測試
                runner = unittest.TextTestRunner(verbosity=2)
                result = runner.run(suite)
                return result.wasSuccessful()
            else:
                print(f"錯誤: 找不到測試文件 {test_file_path}")
                return False
    except Exception as e:
        print(f"運行測試時出錯: {e}")
        return False
    finally:
        # 清理臨時目錄
        shutil.rmtree(temp_dir)


if __name__ == "__main__":
    # 檢查命令行參數
    if len(sys.argv) != 2:
        print("用法: python run_single_test.py <測試文件路徑>")
        print("例如: python run_single_test.py test_vector_store.py")
        sys.exit(1)
        
    # 獲取測試文件路徑
    test_file = sys.argv[1]
    
    # 如果是相對路徑，轉換為絕對路徑
    if not os.path.isabs(test_file):
        # 檢查當前路徑相對測試文件
        current_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), test_file)
        if os.path.exists(current_file):
            test_file = current_file
        else:
            # 嘗試在當前工作目錄下查找
            cwd_file = os.path.join(os.getcwd(), test_file)
            if os.path.exists(cwd_file):
                test_file = cwd_file
            else:
                print(f"無法找到測試文件: {test_file}")
                print(f"嘗試的路徑: {current_file}")
                print(f"            {cwd_file}")
                sys.exit(1)
    
    # 運行測試
    success = run_test_file(test_file)
    sys.exit(0 if success else 1)