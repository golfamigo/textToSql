# 模型錯誤驗證測試

本文檔說明了如何進行模型錯誤驗證測試，包括測試範例、設計策略和實現方法。

## 測試框架

我們使用了兩種測試方法：

1. **單元測試 (unittest)** - 用於簡單、獨立的測試，不依賴應用程序的其他部分。
2. **Pytest** - 用於更複雜的測試場景和完整的集成測試。

## 測試檔案結構

我們創建了以下測試檔案：

1. **test_model_error_validation.py** - 基本錯誤驗證測試
2. **test_advanced_error_validation.py** - 進階和複雜錯誤驗證
3. **test_model_boundary_validation.py** - 邊界值和極端情況測試
4. **run_model_tests.py** - 簡易測試運行器，無需依賴完整應用程序配置

## 測試策略

### 1. 基本錯誤驗證

測試基本的欄位驗證規則，例如：

- 無效的電子郵件格式
- 無效的枚舉值（如用戶角色、預約狀態）
- 缺少必填欄位
- 時間順序檢查（結束時間必須晚於開始時間）

### 2. 進階錯誤驗證

測試更複雜的驗證規則，例如：

- JSON 數據格式驗證
- 日期時間格式錯誤
- UUID 格式錯誤
- 複雜驗證條件違反
- 嵌套數據結構驗證

### 3. 邊界值測試

測試極端情況和邊界值，例如：

- 價格的最大/最小值
- 極短/極長的時間間隔
- 時間段邊界（整天或跨日時段）
- 枚舉邊界值
- 空值或最小必填欄位測試

## 測試模式

所有測試都遵循相似的模式：

1. 準備測試數據
2. 創建模型實例，預期會引發錯誤
3. 檢查錯誤訊息包含預期的內容
4. 對於不應該引發錯誤的邊界情況，確保沒有錯誤發生

```python
# 典型的錯誤測試模式
with self.assertRaises(Exception) as context:
    TestModel(
        # 包含無效數據的參數
    )

# 檢查錯誤訊息
self.assertTrue("預期的錯誤訊息" in str(context.exception))
```

## 關鍵驗證器

我們實現了以下關鍵驗證器：

1. **時間順序驗證**
   ```python
   if self.end_time <= self.start_time:
       raise ValueError('結束時間必須晚於開始時間')
   ```

2. **必填依賴欄位驗證**
   ```python
   if self.specific_date is None and self.day_of_week is None:
       raise ValueError('必須指定 day_of_week 或 specific_date')
   ```

3. **數值範圍驗證**
   ```python
   if v < 0:
       raise ValueError('價格必須為正數')
   ```

4. **字串格式驗證**
   ```python
   # 使用 Pydantic 的 EmailStr 類型
   email: EmailStr = Field(description="使用者信箱")
   ```

## 測試執行

### 運行單一測試文件
```bash
python tests/run_model_tests.py
```

### 運行所有模型測試
```bash
pytest tests/test_model_*.py -v
```

## 建議改進

根據測試結果，我們建議對模型進行以下改進：

1. 為所有模型的價格和數量欄位增加正數驗證
2. 為必須成對出現的欄位增加相互依賴性驗證
3. 考慮使用更嚴格的 UUID 和日期時間格式驗證
4. 為全部字串欄位增加長度限制
5. 考慮為 JSON 欄位增加結構驗證