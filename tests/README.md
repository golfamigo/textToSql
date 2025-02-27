# TextToSQL 測試說明

本文檔介紹如何執行和擴展 TextToSQL 專案的測試。

## 測試架構

測試使用 pytest 和 unittest 框架，主要測試以下組件：

1. **HistoryService** - 測試查詢歷史、收藏和模板功能
2. **文件存儲模式** - 測試使用 JSON 文件進行數據存儲的功能 
3. **CLI 命令** - 測試命令行界面功能

## 測試方式

本專案提供了兩種測試方式：

1. **pytest 測試** - 在 `tests/` 目錄，需要完整安裝環境
2. **unittest 測試** - 在 `unittest/` 目錄，使用獨立模擬環境，不依賴外部服務

## 執行測試

### 安裝測試依賴

```bash
pip install -e ".[test]"
# 或者
pip install pytest pytest-cov
```

### 執行 pytest 測試

注意：執行 pytest 測試需要完整設置環境變數和資料庫連接。

```bash
# 從專案根目錄執行
python -m pytest

# 或帶測試覆蓋率報告
python -m pytest --cov=textToSql
```

### 執行特定 pytest 測試

```bash
# 執行特定測試文件
python -m pytest tests/test_history_service.py

# 執行特定測試類
python -m pytest tests/test_history_service.py::TestHistoryService

# 執行特定測試方法
python -m pytest tests/test_history_service.py::TestHistoryService::test_add_query
```

### 執行 unittest 測試

unittest 測試使用完全獨立的模擬，不依賴外部資料庫或配置。

```bash
# 執行所有 unittest 測試
python -m unittest discover -v unittest

# 執行特定測試文件
python -m unittest unittest/test_history_service.py
```

## 測試說明

### HistoryService 測試 (pytest)

`tests/test_history_service.py` 測試 `HistoryService` 類的核心功能，包括:

- 添加和獲取查詢記錄
- 查詢收藏功能
- 模板管理功能

測試使用 SQLite 內存資料庫，確保測試環境與生產環境隔離。

### 文件存儲測試 (pytest)

`tests/test_file_storage.py` 專門測試 `HistoryService` 在文件存儲模式下的功能。

### CLI 測試 (pytest)

`tests/test_cli.py` 測試命令行界面功能。

### 獨立模擬測試 (unittest)

`unittest/test_history_service.py` 提供完全獨立的測試，使用 mock 對象模擬功能，不依賴外部服務。這些測試適合在任何環境中執行，包括缺少配置的環境。

## 擴展測試

### 添加新測試

1. 為新功能創建測試文件
   - pytest 測試：`tests/test_{component}.py`
   - unittest 測試：`unittest/test_{component}.py`
2. 在測試文件中創建測試類和測試方法
3. 根據測試類型使用適當的方法：
   - pytest：使用 fixtures 提供測試數據和依賴
   - unittest：使用模擬 (mock) 對象和 setUp/tearDown 方法

### 建議測試實踐

- 每個測試只測試一個功能點
- 使用 assert 驗證結果
- 模擬外部依賴，避免測試依賴真實外部服務
- 關鍵功能同時使用 pytest 和 unittest 測試，確保全面覆蓋