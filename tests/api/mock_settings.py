"""
用於API測試的模擬設置類，替代正常的配置類。
這樣可以在測試中繞過對環境變量的依賴。
"""
from enum import Enum
from typing import Dict, List, Optional, Any


class ModelProvider(str, Enum):
    """模型提供商枚舉"""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"
    AZURE = "azure"
    LOCAL = "local"


class ModelConfig:
    """模型配置類"""
    def __init__(self, 
                 model_name: str, 
                 provider: ModelProvider, 
                 max_tokens: int = 4000,
                 temperature: float = 0.2):
        self.model_name = model_name
        self.provider = provider
        self.max_tokens = max_tokens
        self.temperature = temperature


class MockSettings:
    """模擬設置類"""
    def __init__(self):
        # 模型配置
        self.models: Dict[str, ModelConfig] = {
            "dummy-model": ModelConfig("dummy-model", ModelProvider.ANTHROPIC),
            "test-model": ModelConfig("test-model", ModelProvider.OPENAI)
        }
        self.default_model = "dummy-model"
        
        # API 密鑰（在測試中不需要真實的值）
        self.openai_api_key = "dummy-key"
        self.anthropic_api_key = "dummy-key"
        self.google_api_key = "dummy-key"
        self.azure_openai_api_key = "dummy-key"
        self.azure_openai_endpoint = "dummy-endpoint"
        self.azure_deployment_name = "dummy-deployment"
        
        # 資料庫配置
        self.db_host = "localhost"
        self.db_port = 5432
        self.db_name = "dummy_db"
        self.db_user = "dummy_user"
        self.db_password = "dummy_password"
        
        # 向量存儲配置
        self.vector_store_directory = "/tmp/test_vector_store"
        self.vector_store_dimension = 384
        
        # 歷史記錄配置
        self.history_file = "/tmp/test_history.json"


# 創建全局設置實例
settings = MockSettings()