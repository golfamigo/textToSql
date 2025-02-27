# TextToSQL API 測試文件列表

## 測試實現

1. **主要測試文件**
   - `test_api_integration.py` - 完整的 API 整合測試 (unittest 風格)
   - `test_api_pytest.py` - 完整的 API 測試 (pytest 風格)
   - `test_api_e2e.py` - 端到端 API 測試 (使用實際服務)
   - `simple_test.py` - 簡單的測試案例示例

2. **配置和模擬**
   - `mock_settings.py` - 模擬應用程序設置
   - `conftest.py` - pytest 測試配置和 fixtures

3. **測試執行**
   - `run_tests.py` - 統一的測試執行腳本
   - `run_unittest.py` - 專用於 unittest 測試
   - `run_pytest.py` - 專用於 pytest 測試
   - `run_single_test.py` - 執行單個簡單測試
   - `run_manual_test.py` - 手動測試示例

4. **文檔**
   - `README.md` - 測試文檔和使用說明
   - `IMPLEMENTATION_SUMMARY.md` - 實現詳情
   - `SUMMARY.md` - 項目摘要
   - `test_files_list.md` - 文件列表 (本文件)

## 測試覆蓋的 API 端點

1. **健康檢查**
   - `/health` - 服務健康狀態

2. **核心 TextToSQL 功能**
   - `/api/text-to-sql` - 文本到 SQL 轉換
   - `/api/execute-sql` - 直接執行 SQL
   - `/api/history` - 查詢歷史

3. **資料庫元數據**
   - `/api/tables` - 獲取表格列表
   - `/api/table/{table_name}/schema` - 獲取表結構

4. **向量存儲**
   - `/api/vector-store/stats` - 向量存儲統計
   - `/api/vector-store/search` - 搜索相似查詢
   - `/api/vector-store/clear` - 清除向量存儲
   - `/api/vector-store/add` - 添加查詢到向量存儲

5. **模型管理**
   - `/api/models` - 獲取可用模型
   - `/api/rate-model` - 評分模型響應
   - `/api/model-performance` - 獲取模型性能

## 使用方法

各測試執行文件的使用方法：

```bash
# 執行簡單測試 (不依賴外部環境)
python tests/api/simple_test.py

# 執行單個測試
python tests/api/run_single_test.py

# 執行手動測試
python tests/api/run_manual_test.py health
python tests/api/run_manual_test.py text-to-sql
python tests/api/run_manual_test.py tables

# 註: 完整測試需要在應用程序環境中運行
# python -m unittest tests/api/test_api_integration.py
# pytest tests/api/test_api_pytest.py
```

## 注意事項

- 完整測試需要依賴應用程序環境，包括模組、資料庫連接等
- 簡單測試和手動測試可以在任何環境中運行，不依賴實際應用程序
- 所有測試使用模擬響應，不需要實際的 API 服務器