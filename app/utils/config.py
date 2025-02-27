from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, validator
from typing import Dict, Any, List, Optional
import os
from dotenv import load_dotenv
from enum import Enum

# 加載 .env 文件
load_dotenv()

class ModelProvider(str, Enum):
    """模型提供商枚舉"""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"
    AZURE = "azure"
    LOCAL = "local"

class ModelConfig(BaseSettings):
    """模型配置"""
    provider: ModelProvider = Field(description="模型提供商")
    model_name: str = Field(description="模型名稱")
    api_key_env: str = Field(description="API金鑰環境變數名稱") 
    base_url: Optional[str] = Field(default=None, description="API基礎URL")
    temperature: float = Field(default=0.0, description="溫度參數")
    supports_json_mode: bool = Field(default=False, description="是否支持JSON模式")
    context_window: int = Field(default=8000, description="上下文窗口大小")
    max_tokens: Optional[int] = Field(default=None, description="最大生成token數")
    additional_params: Dict[str, Any] = Field(default_factory=dict, description="額外參數")
    
    @validator('api_key_env')
    def validate_api_key(cls, v):
        """驗證API金鑰環境變數"""
        if not os.getenv(v):
            # 只發出警告，不報錯，允許使用沒有API key的模型配置
            print(f"警告: 未找到環境變數 {v} 的值")
        return v

class Settings(BaseSettings):
    """應用程式設定"""
    
    # 資料庫設定
    database_url: str = os.getenv("DATABASE_URL", "postgresql://user:password@localhost:5432/n8n_booking")
    
    # 默認模型設定
    default_model: str = os.getenv("DEFAULT_MODEL", "gpt-4o")
    
    # 模型配置
    models: Dict[str, ModelConfig] = {
        # OpenAI 模型
        "gpt-4o": ModelConfig(
            provider=ModelProvider.OPENAI,
            model_name="gpt-4o",
            api_key_env="OPENAI_API_KEY",
            temperature=0.0,
            supports_json_mode=True,
            context_window=128000,
            max_tokens=4096
        ),
        "gpt-4-turbo": ModelConfig(
            provider=ModelProvider.OPENAI,
            model_name="gpt-4-turbo",
            api_key_env="OPENAI_API_KEY",
            temperature=0.0,
            supports_json_mode=True,
            context_window=128000,
            max_tokens=4096
        ),
        "gpt-3.5-turbo": ModelConfig(
            provider=ModelProvider.OPENAI,
            model_name="gpt-3.5-turbo",
            api_key_env="OPENAI_API_KEY",
            temperature=0.0,
            supports_json_mode=True,
            context_window=16000,
            max_tokens=4096
        ),
        
        # Anthropic 模型
        "claude-3-opus": ModelConfig(
            provider=ModelProvider.ANTHROPIC,
            model_name="claude-3-opus-20240229",
            api_key_env="ANTHROPIC_API_KEY",
            temperature=0.0,
            supports_json_mode=True,
            context_window=200000,
            max_tokens=4096
        ),
        "claude-3-sonnet": ModelConfig(
            provider=ModelProvider.ANTHROPIC,
            model_name="claude-3-sonnet-20240229",
            api_key_env="ANTHROPIC_API_KEY",
            temperature=0.0,
            supports_json_mode=True,
            context_window=200000,
            max_tokens=4096
        ),
        "claude-3-haiku": ModelConfig(
            provider=ModelProvider.ANTHROPIC,
            model_name="claude-3-haiku-20240307",
            api_key_env="ANTHROPIC_API_KEY",
            temperature=0.0,
            supports_json_mode=True,
            context_window=200000,
            max_tokens=4096
        ),
        
        # Google 模型
        "gemini-pro": ModelConfig(
            provider=ModelProvider.GOOGLE,
            model_name="gemini-pro",
            api_key_env="GOOGLE_API_KEY",
            temperature=0.0,
            supports_json_mode=False,
            context_window=32000,
            max_tokens=8192
        ),
        
        # Azure OpenAI
        "azure-gpt-4": ModelConfig(
            provider=ModelProvider.AZURE,
            model_name="gpt-4", 
            api_key_env="AZURE_OPENAI_API_KEY",
            base_url=os.getenv("AZURE_OPENAI_ENDPOINT", ""),
            temperature=0.0,
            supports_json_mode=True,
            context_window=8192,
            additional_params={
                "api_version": "2023-05-15",
                "deployment_name": os.getenv("AZURE_DEPLOYMENT_NAME", "")
            }
        ),
        
        # 本地模型 (如使用 Ollama)
        "llama3": ModelConfig(
            provider=ModelProvider.LOCAL,
            model_name="llama3",
            api_key_env="DUMMY_KEY",  # 不需要實際的API密鑰
            base_url="http://localhost:11434/api",
            temperature=0.0,
            supports_json_mode=False,
            context_window=8192
        )
    }
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )
    
    def get_model_config(self, model_name: Optional[str] = None) -> ModelConfig:
        """獲取模型配置"""
        model = model_name or self.default_model
        if model not in self.models:
            raise ValueError(f"未知的模型: {model}")
        return self.models[model]

# 創建設定實例
settings = Settings()