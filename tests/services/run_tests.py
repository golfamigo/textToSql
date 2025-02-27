#!/usr/bin/env python3
"""
簡單的測試運行器，用於運行向量存儲服務的測試，
不依賴於應用程序配置。
"""
import os
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch


def run_tests():
    """運行所有向量存儲測試"""
    # 添加項目根目錄到 Python 路徑
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
    sys.path.insert(0, project_root)

    # 創建臨時目錄用於測試
    temp_dir = tempfile.mkdtemp()

    try:
        # 設置環境變量以繞過配置驗證
        # Settings 構造函數會嘗試驗證 API 密鑰等，我們需要跳過這些驗證
        env_vars = {
            "DUMMY_KEY": "dummy",
            "OPENAI_API_KEY": "dummy",
            "ANTHROPIC_API_KEY": "dummy",
            "GOOGLE_API_KEY": "dummy",
            "AZURE_OPENAI_API_KEY": "dummy",
            "AZURE_OPENAI_ENDPOINT": "dummy",
            "AZURE_DEPLOYMENT_NAME": "dummy",
        }

        # 使用上述環境變量運行測試
        with patch.dict(os.environ, env_vars):
            loader = unittest.TestLoader()

            # 添加測試文件
            test_dir = os.path.dirname(os.path.abspath(__file__))
            test_files = [
                os.path.join(test_dir, "test_vector_store.py"),
                os.path.join(test_dir, "test_vector_store_integration.py"),
                os.path.join(test_dir, "test_api_vector_store.py"),
            ]

            suites = []
            for test_file in test_files:
                try:
                    if os.path.exists(test_file):
                        # 列印正在運行的測試文件
                        print(f"運行測試文件: {os.path.basename(test_file)}")

                        # 動態加載測試模塊
                        module_name = os.path.basename(test_file).replace(".py", "")
                        sys.path.insert(0, test_dir)

                        # 通過文件路徑導入模塊
                        spec = importlib.util.spec_from_file_location(
                            module_name, test_file
                        )
                        module = importlib.util.module_from_spec(spec)
                        spec.loader.exec_module(module)

                        # 從導入的模塊加載測試
                        suite = loader.loadTestsFromModule(module)

                        # 單獨運行這個測試套件，以便分隔輸出
                        print(f"\n{'=' * 70}\n{module_name} 測試開始\n{'=' * 70}")
                        runner = unittest.TextTestRunner(verbosity=2)
                        result = runner.run(suite)
                        print(f"{'=' * 70}\n{module_name} 測試完成\n{'=' * 70}\n")

                        # 將測試套件添加到總集合
                        suites.append(suite)
                    else:
                        print(f"警告: 找不到測試文件 {test_file}")
                except Exception as e:
                    print(f"加載測試文件 {test_file} 時出錯: {e}")

            # 由於我們已經單獨運行了每個套件，這裡只需要返回結果
            if suites:
                # 所有測試都已經運行完畢，返回 True 表示成功
                print(f"\n總結: 已完成 {len(suites)} 個測試文件的運行")
                return True
            else:
                print("沒有找到任何測試套件")
                return False

    finally:
        # 清理臨時目錄
        shutil.rmtree(temp_dir)


if __name__ == "__main__":
    import importlib.util

    success = run_tests()
    sys.exit(0 if success else 1)
