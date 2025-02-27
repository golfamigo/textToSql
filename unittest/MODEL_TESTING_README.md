# 模型驗證測試說明

本目錄包含用於測試 TextToSQL 應用程序中定義的 Pydantic 模型的測試套件。這些測試確保所有模型按照預期工作，驗證器正確運行，並且模型可以正確地序列化和反序列化。

## 測試文件概述

### 1. 基本模型驗證測試 (`test_model_validation.py`)

該測試文件包含對所有主要模型的基本驗證測試，包括：

- `TestUserModel`: 測試使用者模型的欄位驗證
- `TestBookingModel`: 測試預約模型的欄位驗證和時間驗證器
- `TestServiceModel`: 測試服務模型的欄位驗證
- `TestTimePeriodModel`: 測試時段模型的欄位驗證和時間驗證器
- `TestBusinessModel`: 測試商家模型的欄位驗證

### 2. 進階模型驗證測試 (`test_advanced_model_validation.py`)

該測試文件包含更複雜的模型驗證測試，包括：

- `TestNestedModels`: 測試嵌套 JSON 數據的驗證
- `TestComplexValidators`: 測試複雜的驗證邏輯，如時間範圍和狀態轉換
- `TestEdgeCases`: 測試各種邊界情況，如可選欄位為空、最小必填欄位等
- `TestQueryHistoryModel`: 測試查詢歷史模型的特定功能

### 3. 模型架構和序列化測試 (`test_model_schema_validation.py`)

該測試文件專注於模型的 JSON 架構和序列化/反序列化功能：

- `TestModelSerialization`: 測試模型與 dict 和 JSON 之間的轉換
- `TestSchemaValidation`: 測試模型的 JSON 架構是否正確
- `TestModelExamples`: 測試模型的示例數據是否正確
- `TestDataTypeValidation`: 測試特定數據類型的驗證，如 UUID、日期時間和枚舉

## 運行測試

您可以使用以下命令運行所有模型測試：

```bash
python -m unittest discover -s unittest -p "test_model_*.py"
```

或者運行特定的測試文件：

```bash
python -m unittest unittest/test_model_validation.py
```

## 測試覆蓋範圍

這些測試覆蓋了以下方面：

1. **基本驗證**：確保所有必填欄位都得到驗證，可選欄位有正確的默認值
2. **類型驗證**：確保欄位類型（如 UUID、日期時間、枚舉等）得到正確驗證
3. **自定義驗證器**：測試自定義欄位驗證器（如結束時間必須晚於開始時間）
4. **嵌套數據**：測試嵌套 JSON 數據的驗證和處理
5. **序列化/反序列化**：確保模型可以正確地序列化為 JSON 和從 JSON 反序列化
6. **架構驗證**：測試生成的 JSON 架構是否正確描述了模型

## 添加新測試

當添加新的模型或修改現有模型時，應該相應地更新這些測試。在添加新測試時，請考慮以下幾點：

1. 為新模型添加基本驗證測試
2. 為複雜欄位和自定義驗證器添加特定測試
3. 確保測試覆蓋邊界情況和潛在錯誤條件
4. 添加序列化/反序列化測試

## 測試設計原則

這些測試遵循以下設計原則：

1. **獨立性**：每個測試都是獨立的，不依賴於其他測試的結果
2. **完整性**：測試覆蓋了每個模型的所有重要方面
3. **清晰性**：測試名稱和文檔清晰地描述了測試的目的
4. **健壯性**：測試使用斷言和錯誤捕獲來驗證結果