#!/usr/bin/env python
"""
手動測試 API 的互動式腳本

這個腳本展示如何手動測試 API 功能，
而不是使用自動化測試框架。

使用方法：
python run_manual_test.py [endpoint]

例如：
python run_manual_test.py health
python run_manual_test.py text-to-sql
"""
import sys
import json

# 定義測試用例
TEST_CASES = {
    "health": {
        "description": "測試健康檢查端點 (/health)",
        "method": "GET",
        "url": "/health",
        "expected_status": 200,
        "expected_data": {
            "status": "ok",
            "database": "connected"
        }
    },
    "tables": {
        "description": "測試獲取表格列表 (/api/tables)",
        "method": "GET",
        "url": "/api/tables",
        "expected_status": 200,
        "expected_data": {
            "tables": ["n8n_booking_users", "n8n_booking_services", "n8n_booking_bookings"]
        }
    },
    "text-to-sql": {
        "description": "測試文本到SQL轉換 (/api/text-to-sql)",
        "method": "POST",
        "url": "/api/text-to-sql",
        "body": {
            "query": "找到email是test@example.com的用戶",
            "execute": False,
            "model": "dummy-model"
        },
        "expected_status": 200,
        "expected_fields": ["sql", "explanation", "parameters", "query_id"]
    }
}

def mock_api_call(method, url, body=None):
    """模擬 API 呼叫，返回模擬響應"""
    print(f"\n模擬 {method} 請求到 {url}")
    if body:
        print(f"請求體: {json.dumps(body, indent=2, ensure_ascii=False)}")
    
    # 健康檢查端點
    if url == "/health":
        return {
            "status_code": 200,
            "response": {
                "status": "ok",
                "database": "connected",
                "models": {
                    "default": "dummy-model",
                    "available": 2,
                    "names": ["dummy-model", "test-model"]
                }
            }
        }
    
    # 表格列表端點
    if url == "/api/tables":
        return {
            "status_code": 200,
            "response": {
                "tables": ["n8n_booking_users", "n8n_booking_services", "n8n_booking_bookings"]
            }
        }
    
    # 文本到SQL轉換
    if url == "/api/text-to-sql" and method == "POST":
        return {
            "status_code": 200,
            "response": {
                "sql": "SELECT * FROM n8n_booking_users WHERE email = :email",
                "explanation": "這個查詢從用戶表中選擇符合條件的用戶",
                "parameters": {"email": "test@example.com"},
                "query_id": "test-id"
            }
        }
    
    # 默認響應
    return {
        "status_code": 404,
        "response": {
            "detail": "端點未找到"
        }
    }

def run_test(test_name):
    """運行特定測試用例"""
    if test_name not in TEST_CASES:
        print(f"錯誤：未找到測試用例 '{test_name}'")
        print(f"可用的測試用例: {', '.join(TEST_CASES.keys())}")
        return False
    
    test = TEST_CASES[test_name]
    print(f"運行測試: {test['description']}")
    
    # 模擬 API 調用
    response = mock_api_call(
        method=test["method"],
        url=test["url"],
        body=test.get("body")
    )
    
    # 驗證狀態碼
    if response["status_code"] != test["expected_status"]:
        print(f"❌ 測試失敗：狀態碼 {response['status_code']} 與預期 {test['expected_status']} 不符")
        return False
    
    # 驗證響應數據
    if "expected_data" in test:
        for key, value in test["expected_data"].items():
            if key not in response["response"] or response["response"][key] != value:
                print(f"❌ 測試失敗：響應中的 '{key}' 不符合預期")
                return False
    
    # 驗證響應字段
    if "expected_fields" in test:
        for field in test["expected_fields"]:
            if field not in response["response"]:
                print(f"❌ 測試失敗：響應中缺少 '{field}' 字段")
                return False
    
    print(f"✅ 測試通過！")
    print(f"響應數據：")
    print(json.dumps(response["response"], indent=2, ensure_ascii=False))
    return True

def list_tests():
    """列出所有可用的測試用例"""
    print("可用的測試用例：")
    for name, test in TEST_CASES.items():
        print(f"- {name}: {test['description']}")

def main():
    """主函數"""
    if len(sys.argv) < 2 or sys.argv[1] == "help" or sys.argv[1] == "--help":
        print("使用方法: python run_manual_test.py [test_name]")
        print("         python run_manual_test.py list    # 列出所有測試")
        list_tests()
        return 0
    
    if sys.argv[1] == "list":
        list_tests()
        return 0
    
    test_name = sys.argv[1]
    success = run_test(test_name)
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())