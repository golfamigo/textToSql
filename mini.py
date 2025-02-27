import os
import sys
from typing import Dict, Any

print("===== 文本到SQL轉換服務 - 最小版本 =====")
print("此版本僅提供基本功能，不包含向量搜索，API和其他高級功能")

# 設置基本環境變量
os.environ["DUMMY_KEY"] = "dummy"

# 創建模擬模塊
class DummyModule:
    def __getattr__(self, name):
        return lambda *args, **kwargs: None

# 繞過導入複雜依賴
sys.modules["faiss"] = DummyModule()
sys.modules["sentence_transformers"] = DummyModule()
sys.modules["joblib"] = DummyModule()

try:
    # 導入必要組件
    from app.utils.config import settings
    print("\n配置加載成功!")
    
    from app.models.users import UserModel
    print("用戶模型加載成功!")
    
    from app.schema.schema import db_functions
    print(f"\n資料庫函數: {len(db_functions)} 個")
    for func_name in list(db_functions.keys())[:5]:
        print(f"- {func_name}")
    if len(db_functions) > 5:
        print(f"... 以及 {len(db_functions)-5} 個其他函數")
    
    print("\n系統基礎組件加載成功!")
    print("您可以在Windows上解決這些問題後嘗試完整版本")
    
except Exception as e:
    print(f"\n錯誤: {e}")
    print(f"類型: {type(e)}")
    import traceback
    traceback.print_exc()