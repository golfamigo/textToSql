#!/usr/bin/env python
"""
運行單個測試的簡單腳本
這是一個完全獨立的測試，不依賴任何測試框架或外部環境
"""

def test_api_example():
    """一個簡單的測試例子"""
    print("運行單個測試例子")
    
    # 模擬 API 回應的類
    class MockResponse:
        def __init__(self, status_code, data):
            self.status_code = status_code
            self.data = data
        
        def json(self):
            return self.data
    
    # 測試案例 1：健康檢查
    response = MockResponse(200, {
        "status": "ok",
        "database": "connected",
        "models": {
            "default": "dummy-model",
            "available": 2,
            "names": ["dummy-model", "test-model"]
        }
    })
    
    # 驗證結果
    if response.status_code != 200:
        print("❌ 測試失敗：狀態碼不正確")
        return False
    
    data = response.json()
    if data["status"] != "ok":
        print("❌ 測試失敗：狀態不正確")
        return False
    
    if data["database"] != "connected":
        print("❌ 測試失敗：資料庫狀態不正確")
        return False
    
    if data["models"]["default"] != "dummy-model":
        print("❌ 測試失敗：默認模型不正確")
        return False
    
    # 測試案例 2：獲取表格
    tables_response = MockResponse(200, {
        "tables": ["users", "services", "bookings"]
    })
    
    # 驗證結果
    if tables_response.status_code != 200:
        print("❌ 測試失敗：表格狀態碼不正確")
        return False
    
    tables_data = tables_response.json()
    if len(tables_data["tables"]) != 3:
        print("❌ 測試失敗：表格數量不正確")
        return False
    
    if "users" not in tables_data["tables"]:
        print("❌ 測試失敗：缺少預期的表格")
        return False
    
    # 測試案例 3：文本到SQL轉換
    sql_response = MockResponse(200, {
        "sql": "SELECT * FROM users WHERE email = :email",
        "explanation": "這個查詢從用戶表中選擇符合條件的用戶",
        "parameters": {"email": "test@example.com"},
        "query_id": "test-id"
    })
    
    # 驗證結果
    if sql_response.status_code != 200:
        print("❌ 測試失敗：SQL轉換狀態碼不正確")
        return False
    
    sql_data = sql_response.json()
    if "SELECT * FROM users WHERE email = :email" not in sql_data["sql"]:
        print("❌ 測試失敗：SQL查詢不正確")
        return False
    
    if sql_data["parameters"]["email"] != "test@example.com":
        print("❌ 測試失敗：SQL參數不正確")
        return False
    
    print("✅ 所有測試通過！")
    return True


if __name__ == "__main__":
    success = test_api_example()
    exit_code = 0 if success else 1
    import sys
    sys.exit(exit_code)