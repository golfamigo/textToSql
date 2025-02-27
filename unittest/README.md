# TextToSQL 獨立單元測試

此目錄包含 TextToSQL 專案的獨立單元測試，使用 Python 標準庫的 unittest 框架實現。

## 特點

- **完全獨立** - 不依賴外部資源或配置
- **快速執行** - 使用模擬對象而非真實連接
- **可靠性高** - 在任何環境都能運行
- **適合CI/CD** - 適合在持續集成環境中使用

## 執行測試

```bash
# 從專案根目錄執行所有獨立測試 (不需要依賴外部資源或完整專案)
python -m unittest unittest/simple_test.py unittest/mock_textToSql.py unittest/test_history_service.py unittest/test_database_functions.py unittest/test_database_service.py

# 執行參數化查詢測試
python -m unittest unittest/test_parameterized_queries.py unittest/test_sql_function_params.py unittest/test_text_to_sql_params.py

# 執行特定測試文件
python -m unittest unittest/test_history_service.py
python -m unittest unittest/simple_test.py
python -m unittest unittest/mock_textToSql.py
python -m unittest unittest/test_database_functions.py
python -m unittest unittest/test_database_service.py
python -m unittest unittest/test_parameterized_queries.py
python -m unittest unittest/test_sql_function_params.py
python -m unittest unittest/test_text_to_sql_params.py

# 執行特定測試方法
python -m unittest unittest.test_history_service.TestHistoryService.test_toggle_favorite
python -m unittest unittest.test_parameterized_queries.TestParameterizedQueries.test_sql_injection_prevention
```

## 測試內容

### 1. 基本測試 (`simple_test.py`)

測試基本的 Python 操作，確保測試環境正常：

1. **JSON 操作測試** - 測試讀寫 JSON 文件
2. **字符串操作測試** - 測試字符串處理
3. **列表操作測試** - 測試列表操作
4. **字典操作測試** - 測試字典操作

### 2. 模擬 TextToSQL 測試 (`mock_textToSql.py`)

使用模擬對象測試核心功能：

1. **SQL 生成測試** - 測試不同查詢的 SQL 生成
2. **查詢執行測試** - 測試查詢執行結果
3. **端到端流程測試** - 測試完整查詢流程

### 3. 歷史服務測試 (`test_history_service.py`)

測試查詢歷史服務的功能，包括：

1. **添加查詢到文件** (`test_add_query_to_file`)
   - 驗證查詢能正確添加到文件中

2. **切換收藏狀態** (`test_toggle_favorite`)
   - 驗證收藏切換功能正常工作

3. **保存為模板** (`test_save_as_template`)
   - 驗證查詢能正確保存為模板

4. **通過標籤搜尋模板** (`test_get_templates_by_tag`)
   - 驗證模板標籤搜尋功能

5. **增加模板使用計數** (`test_increment_template_usage`)
   - 驗證模板使用計數增加功能

### 4. 資料庫函數測試 (`test_database_functions.py`)

測試資料庫函數的模擬實現：

1. **服務搜尋函數** (`test_find_service_*`)
   - 測試精確匹配服務
   - 測試部分匹配服務
   - 測試無匹配服務情況

2. **時段可用性函數** (`test_get_period_availability`)
   - 測試獲取特定時段的可用性
   - 驗證已預約和可用容量的計算

3. **員工可用性函數** (`test_get_staff_availability`)
   - 測試週期性排班規則
   - 測試特定日期排班規則

4. **預約詳情函數** (`test_get_booking_details`)
   - 測試獲取存在的預約詳情
   - 測試獲取不存在的預約詳情

### 5. 資料庫服務測試 (`test_database_service.py`)

測試資料庫服務層的功能：

1. **查詢執行功能** (`test_execute_query`)
   - 驗證SQL查詢的執行結果
   - 確保返回正確的列名和數據行

2. **錯誤處理** (`test_execute_query_error`)
   - 測試查詢執行錯誤時的處理邏輯
   - 驗證錯誤信息的傳遞

3. **連接管理** (`test_connection_management`)
   - 測試資料庫連接的建立與關閉
   - 確保連接狀態正確追蹤

4. **參數處理** (`test_parameter_handling`)
   - 測試參數化查詢的處理
   - 確保參數正確傳遞到SQL查詢

### 6. 參數化查詢測試 (`test_parameterized_queries.py`)

測試參數化SQL查詢的處理機制：

1. **基本參數傳遞** (`test_basic_parameter_passing`)
   - 驗證基本參數正確傳遞到SQL查詢

2. **多參數處理** (`test_multiple_parameters`)
   - 測試多個參數同時使用的情況

3. **參數類型處理** (`test_parameter_type_handling`)
   - 測試不同數據類型的參數處理 (字符串、整數、布爾值、浮點數)

4. **空值參數處理** (`test_none_parameters`)
   - 測試空值(None)參數的處理

5. **列表參數處理** (`test_list_parameters`)
   - 測試列表參數在IN子句中的使用

6. **SQL注入防護** (`test_sql_injection_prevention`)
   - 測試參數化查詢如何防止SQL注入攻擊

7. **缺失參數處理** (`test_missing_parameters`)
   - 測試缺少必要參數時的錯誤處理

8. **日期參數處理** (`test_date_parameters`)
   - 測試日期和時間參數的處理

9. **JSON參數處理** (`test_json_parameters`)
   - 測試JSON格式參數的處理

### 7. SQL函數參數測試 (`test_sql_function_params.py`)

測試真實SQL函數中的參數化查詢實現：

1. **服務搜尋函數參數** (`test_find_service_params`)
   - 測試服務搜尋函數中的參數處理

2. **預約詳情函數參數** (`test_get_booking_details_params`)
   - 測試獲取預約詳情函數中的參數處理

3. **客戶郵件查詢參數** (`test_get_bookings_by_customer_email_params`)
   - 測試通過客戶郵件查詢預約的參數處理

4. **創建預約參數** (`test_create_booking_params`)
   - 測試創建預約函數中的多參數處理

5. **更新服務參數** (`test_update_service_params`)
   - 測試更新服務函數中的參數處理

6. **時段可用性參數** (`test_get_period_availability_params`)
   - 測試獲取時段可用性函數中的參數處理

7. **日期時段可用性參數** (`test_get_period_availability_by_date_params`)
   - 測試獲取特定日期時段可用性函數中的參數處理

8. **設置員工可用性參數** (`test_set_staff_availability_params`)
   - 測試設置員工可用性函數中的參數處理

### 8. TextToSQL參數化測試 (`test_text_to_sql_params.py`)

測試TextToSQL服務中的參數化查詢生成與處理：

1. **基本參數提取** (`test_basic_parameter_extraction`)
   - 測試從LLM響應中提取參數的功能

2. **複雜參數類型處理** (`test_complex_parameter_types`)
   - 測試不同類型參數的處理（字符串、整數、布爾值等）

3. **日期參數處理** (`test_date_parameters`)
   - 測試日期參數的生成與處理

4. **列表參數處理** (`test_list_parameters`)
   - 測試列表參數在IN子句中的使用

5. **錯誤參數處理** (`test_malformed_parameter_handling`)
   - 測試處理不完整或錯誤參數的情況

6. **SQL注入防護** (`test_sql_injection_prevention`)
   - 測試TextToSQL服務如何防止SQL注入攻擊

7. **空值參數處理** (`test_null_parameters`)
   - 測試空值(None)參數的處理

## 擴展測試

添加新測試步驟：

1. 在現有測試類中添加新的測試方法，命名格式為 `test_功能名稱`
2. 為測試創建必要的模擬對象 (Mock)
3. 執行被測試的功能
4. 使用 `self.assert*` 方法驗證結果

例如：

```python
def test_new_feature(self):
    """測試新功能"""
    # 創建模擬對象
    mock_obj = MockObject()
    
    # 創建模擬服務
    class MockService:
        def new_feature(self, param):
            # 實現簡化版邏輯
            return "結果"
    
    # 執行方法
    service = MockService()
    result = service.new_feature("測試參數")
    
    # 驗證結果
    self.assertEqual(result, "期望結果")
```