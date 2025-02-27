# 向量存儲服務測試

本目錄包含針對 TextToSQL 應用程序中向量存儲服務 (`VectorStore`) 的測試套件。

## 測試文件

1. `test_vector_store.py` - 基本向量存儲功能測試
2. `test_vector_store_integration.py` - 與文本到 SQL 服務的整合測試
3. `test_api_vector_store.py` - API 端點測試

## 運行測試

由於應用程序的配置依賴於環境變量（如 API 密鑰），為了簡化測試，提供了以下兩個測試運行器：

### 運行所有向量存儲測試

```bash
python tests/services/run_tests.py
```

### 運行單個測試文件

```bash
python tests/services/run_single_test.py tests/services/test_vector_store.py
```

或者

```bash
cd tests/services
python run_single_test.py test_vector_store.py
```

## 測試內容

### 基本向量存儲測試 (`test_vector_store.py`)

- 向量存儲初始化和配置
- 文本嵌入生成
- 添加和搜索查詢
- 保存和加載索引
- 錯誤處理和邊界條件

### 整合測試 (`test_vector_store_integration.py`)

- 向量存儲與 `TextToSQLService` 的整合
- 相似查詢搜索和存儲功能
- 向量存儲錯誤處理和容錯
- 相似度閾值過濾
- 向量搜索結果對提示詞的影響

### API 測試 (`test_api_vector_store.py`)

- 向量存儲 API 端點功能
- 錯誤處理和狀態碼
- 參數驗證
- 格式轉換