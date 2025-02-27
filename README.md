# TextToSQL 專案

這是一個使用 Pydantic 和 OpenAI 將自然語言轉換為 SQL 查詢的專案，專門針對 N8N 預約系統資料庫設計。本專案可以將用戶的自然語言描述自動轉換為精確的 PostgreSQL 查詢語句，提供查詢解釋，並可選擇性地執行查詢。

## 功能特點

- 將自然語言轉換為準確的 SQL 查詢
- 利用資料庫函數處理複雜預約邏輯
- 智能處理資料庫函數錯誤，提供替代查詢方案
- 支援多種語言模型（OpenAI、Anthropic、Google、Azure、本地模型）
- 模型評分與性能跟蹤功能
- 提供 SQL 查詢的詳細解釋
- 選擇性地執行生成的查詢並顯示結果
- 保存查詢歷史記錄
- 支持命令行和 API 兩種使用方式
- 美化的控制臺輸出
- 安全的查詢執行（僅允許只讀查詢）

## 環境設置

1. 安裝依賴項：
   ```bash
   # 安裝基本套件
   pip install -e .

   # 安裝開發工具
   pip install -e ".[dev]"

   # 安裝測試工具
   pip install -e ".[test]"
   ```

2. 設置環境變數：
   創建一個 `.env` 文件並添加：
   ```
   OPENAI_API_KEY=your_api_key_here
   ANTHROPIC_API_KEY=your_anthropic_api_key
   DATABASE_URL=postgresql://user:password@localhost:5432/n8n_booking
   ```

3. 安裝開發工具:
   ```bash
   # 安裝 pre-commit 勾子
   pre-commit install
   ```

## 專案結構

- `app/`: 主要應用程式程式碼
  - `models/`: Pydantic 資料庫模型
  - `schema/`: 資料庫結構定義
  - `services/`: 業務邏輯服務（Text-to-SQL、資料庫、歷史記錄服務）
  - `utils/`: 工具函數和設定
- `n8n_booking_schemas/`: 資料庫結構 SQL 文件
- `main.py`: FastAPI 應用程式入口
- `setup.py`: Python 包安裝設定

## 使用方法

### 命令行使用

1. 將自然語言轉換為 SQL：
   ```
   python -m app "列出所有活躍的商家"
   ```
   
   或使用 `convert` 子命令：
   ```
   python -m app convert "列出所有活躍的商家"
   ```

2. 轉換並執行查詢：
   ```
   python -m app convert "列出所有活躍的商家" -e
   ```

3. 從文件讀取查詢並輸出到文件：
   ```
   python -m app convert -f query.txt -o result.sql
   ```

4. 查看查詢歷史：
   ```
   python -m app history
   ```

5. 直接執行 SQL 查詢：
   ```
   python -m app execute "SELECT * FROM n8n_booking_businesses"
   ```

### API 使用

1. 啟動 API 伺服器：
   ```
   python main.py
   ```

2. API 端點：
   - `POST /api/text-to-sql`: 將自然語言轉換為 SQL
   - `GET /api/history`: 獲取查詢歷史
   - `POST /api/execute-sql`: 執行 SQL 查詢
   - `GET /api/tables`: 獲取所有表名
   - `GET /api/table/{table_name}/schema`: 獲取表結構

## 安全注意事項

- 本專案僅允許執行只讀查詢（SELECT）
- 禁止執行修改數據的查詢（INSERT、UPDATE、DELETE等）
- 所有查詢執行前都會通過安全檢查
- 建議在開發環境中使用，或為生產環境設置只讀資料庫用戶

## 開發者指南

### 程式碼風格與檢查

本專案使用多種工具確保代碼質量：

```bash
# 格式化代碼
black app
isort app

# 靜態類型檢查
mypy app

# 代碼風格檢查
flake8 app
pylint app

# 使用 ruff 進行快速檢查
ruff check app

# 運行測試
pytest
```

### CI/CD 流程

本專案使用 GitHub Actions 進行持續整合：

- 每次 push 和 pull request 時自動運行代碼檢查和測試
- 程式碼風格檢查 (black, isort)
- 靜態類型檢查 (mypy)
- 代碼品質檢查 (flake8, pylint, ruff)
- 自動化測試 (pytest)

## 案例示範

以下是一些查詢範例：

1. "找出所有提供'美容'服務的員工"
   ```sql
   SELECT u.name, u.email, u.phone 
   FROM get_staff_by_service('美容') gs 
   JOIN n8n_booking_users u ON gs.staff_id = u.id;
   ```

2. "顯示下週美甲服務的可用時段"
   ```sql
   SELECT * FROM get_period_availability_by_service(
     (SELECT id FROM n8n_booking_services WHERE name LIKE '%美甲%' LIMIT 1), 
     CURRENT_DATE, 
     CURRENT_DATE + INTERVAL '7 days'
   );
   ```

3. "查找客戶張小明的所有預約"
   ```sql
   SELECT * FROM get_bookings_by_customer_email('張小明%');
   ```

4. "列出本週預約最多的前三名服務項目"
   ```sql
   SELECT s.name AS service_name, COUNT(b.id) AS booking_count
   FROM n8n_booking_bookings b
   JOIN n8n_booking_services s ON b.service_id = s.id
   WHERE booking_start_time BETWEEN 
     date_trunc('week', CURRENT_DATE) AND 
     date_trunc('week', CURRENT_DATE) + INTERVAL '6 days'
   GROUP BY s.name
   ORDER BY booking_count DESC
   LIMIT 3;
   ```

5. "找出目前有空的所有員工"
   ```sql
   SELECT * FROM get_staff_availability_by_date(CURRENT_DATE);
   ```