# TextToSQL 專案 (重構版)

這是TextToSQL專案的重構版本，使用pydantic-ai和異步數據庫連接進行了全面升級。

## 新功能

- 使用pydantic-ai提供更強大的LLM整合
- 使用AsyncPG進行異步數據庫操作
- 採用logfire進行結構化日誌記錄
- 完全異步的API設計

## 安裝需求

```bash
# 安裝所有依賴
pip install -r requirements.txt
```

## 環境設置

1. 複製`.env.example`到`.env`並根據您的需求進行配置：
   ```
   cp .env.example .env
   ```

2. 配置以下必要設定：
   - `DATABASE_URL`: 資料庫連接字串
   - `OPENAI_API_KEY`: OpenAI API密鑰
   - `DEFAULT_MODEL`: 預設使用的模型 (例如 "gpt-4o")

## 運行應用

```bash
python main.py
```

應用將在 http://localhost:8000 啟動。

## API端點

- **POST /api/text-to-sql**
  轉換自然語言為SQL查詢

  請求體參數:
  ```json
  {
    "query": "列出所有活躍的服務",
    "execute": true,
    "find_similar": true,
    "session_id": "optional-session-id"
  }
  ```

- **GET /health**
  檢查應用健康狀態

## 開發文檔

- 使用異步數據庫連接 (AsyncPG)
- 使用pydantic-ai建立Agent
- 使用logfire進行日誌記錄

## 技術重構特點

1. **建立於pydantic-ai之上**
   - 類型安全的AI交互
   - 結構化的Agent設計
   - 支援函數調用

2. **異步架構**
   - 使用AsyncPG提高數據庫性能
   - FastAPI的異步端點處理
   - 支援高併發請求

3. **改進的日誌系統**
   - 使用logfire進行結構化日誌
   - 更好的錯誤跟踪
   - 可觀察性提升