# API 整合測試

本目錄包含 TextToSQL API 的整合測試和單元測試。

## 測試設置

所有測試使用模擬（mock）方式創建服務對象，避免對真實資料庫和外部服務的依賴。主要的測試方法有兩種：

1. **unittest 風格測試**: 使用 Python 標準的 unittest 框架
2. **pytest 風格測試**: 使用 pytest 框架和 fixtures

## 文件結構

- `mock_settings.py`: 模擬的應用程序配置，替代真實的環境變量設置
- `conftest.py`: pytest 的配置文件，包含所有共享的 fixtures
- `test_api_integration.py`: 使用 unittest 風格的 API 整合測試
- `test_api_pytest.py`: 使用 pytest 風格的 API 測試
- `test_api_e2e.py`: 端到端 API 測試 (需要真實服務)

## 運行測試

### 運行 unittest 風格測試

```bash
# 運行所有 unittest 測試
python -m unittest tests/api/test_api_integration.py

# 運行特定測試
python -m unittest tests.api.test_api_integration.TestAPIIntegration.test_health_check
```

### 運行 pytest 風格測試

```bash
# 運行所有 pytest 測試
pytest tests/api/test_api_pytest.py -v

# 運行標記為集成測試的測試
pytest tests/api/test_api_pytest.py -v -m integration

# 運行特定測試
pytest tests/api/test_api_pytest.py::test_health_check -v
```

### 端到端測試

注意：端到端測試默認是被跳過的，因為它們需要真實服務連接。

```bash
# 運行端到端測試（強制運行被標記為跳過的測試）
pytest tests/api/test_api_e2e.py -v --runxfail
```

## 測試內容

API 測試覆蓋以下端點：

1. `/health`: 健康檢查
2. `/api/text-to-sql`: 文本到 SQL 轉換
3. `/api/history`: 查詢歷史
4. `/api/execute-sql`: 直接執行 SQL
5. `/api/tables` 和 `/api/table/{table_name}/schema`: 表格和結構
6. `/api/vector-store/*`: 向量存儲操作
7. `/api/models` 和 `/api/model-performance`: 模型管理和性能
8. `/api/rate-model`: 模型評分

## 模擬的服務

測試模擬了以下服務：

1. `TextToSQLService`: 處理自然語言到 SQL 的轉換
2. `DatabaseService`: 處理資料庫操作
3. `VectorStore`: 管理向量存儲
4. `LLMService`: 與語言模型交互

## 最佳實踐

1. 每個測試方法應該獨立，不依賴於其他測試的狀態
2. 使用 `setUp` 和 `tearDown` 方法初始化和清理測試環境
3. 為每個服務創建適當的模擬對象
4. 測試錯誤處理和邊界情況
5. 使用臨時目錄進行文件操作測試
6. 通過 fixtures 共享常用的測試資源
7. 使用標記區分不同類型的測試（如集成測試、端到端測試）