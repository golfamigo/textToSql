from typing import Dict, Any, List, Optional, Union, Tuple
import os
import json
import time
from uuid import uuid4
import logging
from abc import ABC, abstractmethod

from ..utils.config import ModelProvider, ModelConfig, settings

# 設定日誌
logger = logging.getLogger(__name__)


class LLMResponse:
    """語言模型回應"""
    
    def __init__(
        self, 
        content: str, 
        model: str,
        token_usage: Dict[str, int] = None,
        raw_response: Any = None,
        error: Optional[str] = None,
        latency: float = 0.0
    ):
        self.content = content
        self.model = model
        self.token_usage = token_usage or {}
        self.raw_response = raw_response
        self.error = error
        self.latency = latency  # 毫秒
        self.request_id = str(uuid4())
        self.timestamp = time.time()
    
    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典"""
        return {
            "content": self.content,
            "model": self.model,
            "token_usage": self.token_usage,
            "error": self.error,
            "latency": self.latency,
            "request_id": self.request_id,
            "timestamp": self.timestamp
        }
    
    def is_error(self) -> bool:
        """是否為錯誤回應"""
        return self.error is not None
    
    def get_parsed_json(self) -> Dict[str, Any]:
        """嘗試解析 JSON 內容"""
        try:
            return json.loads(self.content)
        except json.JSONDecodeError as e:
            logger.error(f"JSON 解析錯誤: {e}")
            return {"error": f"無法解析 JSON: {str(e)}"}


class LLMProvider(ABC):
    """語言模型提供者基類"""
    
    def __init__(self, model_config: ModelConfig):
        self.model_config = model_config
        self.model_name = model_config.model_name
        self.api_key = os.getenv(model_config.api_key_env, "")
        self.base_url = model_config.base_url
        self.temperature = model_config.temperature
        self.max_tokens = model_config.max_tokens
        self.supports_json_mode = model_config.supports_json_mode
        self.additional_params = model_config.additional_params
        
        self._setup()
    
    @abstractmethod
    def _setup(self):
        """設置 API 客戶端"""
        pass
    
    @abstractmethod
    def generate(
        self, 
        prompt: str, 
        system_prompt: Optional[str] = None,
        json_mode: bool = False
    ) -> LLMResponse:
        """生成文本"""
        pass


class OpenAIProvider(LLMProvider):
    """OpenAI 模型提供者"""
    
    def _setup(self):
        """設置 OpenAI API 客戶端"""
        try:
            import openai
            self.client = openai.OpenAI(api_key=self.api_key, base_url=self.base_url)
        except ImportError:
            logger.error("OpenAI 套件未安裝，請執行 pip install openai")
            raise
    
    def generate(
        self, 
        prompt: str, 
        system_prompt: Optional[str] = None,
        json_mode: bool = False
    ) -> LLMResponse:
        """使用 OpenAI API 生成文本"""
        try:
            start_time = time.time()
            
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            # 準備參數
            params = {
                "model": self.model_name,
                "messages": messages,
                "temperature": self.temperature
            }
            
            # 添加 JSON 模式
            if json_mode and self.supports_json_mode:
                params["response_format"] = {"type": "json_object"}
            
            # 添加 max_tokens 如果有設定
            if self.max_tokens:
                params["max_tokens"] = self.max_tokens
            
            # 添加額外參數
            for key, value in self.additional_params.items():
                params[key] = value
            
            # 調用 API
            response = self.client.chat.completions.create(**params)
            
            # 計算耗時
            latency = (time.time() - start_time) * 1000  # 轉換為毫秒
            
            # 獲取 token 使用量
            token_usage = {}
            if hasattr(response, 'usage'):
                token_usage = {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                }
            
            # 構建回應
            content = response.choices[0].message.content
            
            return LLMResponse(
                content=content,
                model=self.model_name,
                token_usage=token_usage,
                raw_response=response,
                latency=latency
            )
            
        except Exception as e:
            logger.error(f"OpenAI API 調用錯誤: {e}")
            return LLMResponse(
                content="",
                model=self.model_name,
                error=str(e)
            )


class AnthropicProvider(LLMProvider):
    """Anthropic 模型提供者"""
    
    def _setup(self):
        """設置 Anthropic API 客戶端"""
        try:
            import anthropic
            self.client = anthropic.Anthropic(api_key=self.api_key)
        except ImportError:
            logger.error("Anthropic 套件未安裝，請執行 pip install anthropic")
            raise
    
    def generate(
        self, 
        prompt: str, 
        system_prompt: Optional[str] = None,
        json_mode: bool = False
    ) -> LLMResponse:
        """使用 Anthropic API 生成文本"""
        try:
            start_time = time.time()
            
            # 準備參數
            params = {
                "model": self.model_name,
                "max_tokens": self.max_tokens or 4096,
                "temperature": self.temperature,
                "messages": [
                    {"role": "user", "content": prompt}
                ]
            }
            
            # 添加 system 提示
            if system_prompt:
                params["system"] = system_prompt
            
            # 添加 JSON 模式
            if json_mode and self.supports_json_mode:
                params["response_format"] = {"type": "json_object"}
            
            # 添加額外參數
            for key, value in self.additional_params.items():
                params[key] = value
            
            # 調用 API
            response = self.client.messages.create(**params)
            
            # 計算耗時
            latency = (time.time() - start_time) * 1000  # 轉換為毫秒
            
            # 獲取 token 使用量
            token_usage = {}
            if hasattr(response, 'usage'):
                token_usage = {
                    "input_tokens": response.usage.input_tokens,
                    "output_tokens": response.usage.output_tokens
                }
            
            # 構建回應
            content = response.content[0].text
            
            return LLMResponse(
                content=content,
                model=self.model_name,
                token_usage=token_usage,
                raw_response=response,
                latency=latency
            )
            
        except Exception as e:
            logger.error(f"Anthropic API 調用錯誤: {e}")
            return LLMResponse(
                content="",
                model=self.model_name,
                error=str(e)
            )


class GoogleProvider(LLMProvider):
    """Google 模型提供者"""
    
    def _setup(self):
        """設置 Google Generative AI 客戶端"""
        try:
            import google.generativeai as genai
            genai.configure(api_key=self.api_key)
            self.genai = genai
        except ImportError:
            logger.error("Google Generative AI 套件未安裝，請執行 pip install google-generativeai")
            raise
    
    def generate(
        self, 
        prompt: str, 
        system_prompt: Optional[str] = None,
        json_mode: bool = False
    ) -> LLMResponse:
        """使用 Google Generative AI API 生成文本"""
        try:
            start_time = time.time()
            
            # 設置模型
            model = self.genai.GenerativeModel(self.model_name)
            
            # 配置生成參數
            generation_config = {
                "temperature": self.temperature,
                "max_output_tokens": self.max_tokens or 2048,
                "top_p": 0.95,
                "top_k": 0
            }
            
            # 添加系統提示
            if system_prompt:
                chat = model.start_chat(system_instruction=system_prompt)
                response = chat.send_message(
                    prompt,
                    generation_config=generation_config
                )
            else:
                response = model.generate_content(
                    prompt,
                    generation_config=generation_config
                )
            
            # 計算耗時
            latency = (time.time() - start_time) * 1000  # 轉換為毫秒
            
            # 構建回應
            if json_mode:
                # Gemini 沒有原生的 JSON 模式，使用提示詞來模擬
                prompt = f"{prompt}\n\n請只返回有效的 JSON 格式，不要加入任何解釋文字。"
            
            content = response.text
            
            return LLMResponse(
                content=content,
                model=self.model_name,
                raw_response=response,
                latency=latency
            )
            
        except Exception as e:
            logger.error(f"Google API 調用錯誤: {e}")
            return LLMResponse(
                content="",
                model=self.model_name,
                error=str(e)
            )


class AzureProvider(LLMProvider):
    """Azure OpenAI 模型提供者"""
    
    def _setup(self):
        """設置 Azure OpenAI API 客戶端"""
        try:
            from openai import AzureOpenAI
            self.client = AzureOpenAI(
                api_key=self.api_key,
                api_version=self.additional_params.get("api_version", "2023-05-15"),
                azure_endpoint=self.base_url
            )
        except ImportError:
            logger.error("OpenAI 套件未安裝，請執行 pip install openai")
            raise
    
    def generate(
        self, 
        prompt: str, 
        system_prompt: Optional[str] = None,
        json_mode: bool = False
    ) -> LLMResponse:
        """使用 Azure OpenAI API 生成文本"""
        try:
            start_time = time.time()
            
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            # 準備參數
            params = {
                "messages": messages,
                "temperature": self.temperature,
                "deployment_name": self.additional_params.get("deployment_name", "")
            }
            
            # 添加 JSON 模式
            if json_mode and self.supports_json_mode:
                params["response_format"] = {"type": "json_object"}
            
            # 添加 max_tokens 如果有設定
            if self.max_tokens:
                params["max_tokens"] = self.max_tokens
            
            # 調用 API
            response = self.client.chat.completions.create(**params)
            
            # 計算耗時
            latency = (time.time() - start_time) * 1000  # 轉換為毫秒
            
            # 獲取 token 使用量
            token_usage = {}
            if hasattr(response, 'usage'):
                token_usage = {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                }
            
            # 構建回應
            content = response.choices[0].message.content
            
            return LLMResponse(
                content=content,
                model=self.model_name,
                token_usage=token_usage,
                raw_response=response,
                latency=latency
            )
            
        except Exception as e:
            logger.error(f"Azure OpenAI API 調用錯誤: {e}")
            return LLMResponse(
                content="",
                model=self.model_name,
                error=str(e)
            )


class LocalProvider(LLMProvider):
    """本地模型提供者 (如 Ollama)"""
    
    def _setup(self):
        """設置本地模型客戶端"""
        # Ollama 使用 REST API，不需要特殊客戶端
        import requests
        self.requests = requests
    
    def generate(
        self, 
        prompt: str, 
        system_prompt: Optional[str] = None,
        json_mode: bool = False
    ) -> LLMResponse:
        """使用本地模型生成文本"""
        try:
            start_time = time.time()
            
            # 準備請求數據
            headers = {'Content-Type': 'application/json'}
            data = {
                "model": self.model_name,
                "prompt": prompt,
                "temperature": self.temperature,
                "stream": False
            }
            
            if system_prompt:
                data["system"] = system_prompt
            
            # 如果需要 JSON 輸出，添加到提示詞中
            if json_mode:
                data["prompt"] = f"{prompt}\n\n請只返回有效的 JSON 格式，不要加入任何解釋文字。"
            
            # 發送請求
            response = self.requests.post(
                f"{self.base_url}/generate",
                headers=headers,
                json=data
            )
            
            # 確保請求成功
            response.raise_for_status()
            
            # 解析回應
            json_response = response.json()
            
            # 計算耗時
            latency = (time.time() - start_time) * 1000  # 轉換為毫秒
            
            # 構建回應
            content = json_response.get("response", "")
            
            return LLMResponse(
                content=content,
                model=self.model_name,
                raw_response=json_response,
                latency=latency
            )
            
        except Exception as e:
            logger.error(f"本地模型 API 調用錯誤: {e}")
            return LLMResponse(
                content="",
                model=self.model_name,
                error=str(e)
            )


class LLMService:
    """語言模型服務"""
    
    def __init__(self):
        self.provider_classes = {
            ModelProvider.OPENAI: OpenAIProvider,
            ModelProvider.ANTHROPIC: AnthropicProvider,
            ModelProvider.GOOGLE: GoogleProvider,
            ModelProvider.AZURE: AzureProvider,
            ModelProvider.LOCAL: LocalProvider
        }
        
        # 初始化提供者緩存
        self.providers = {}
        
        # 模型評分記錄
        self.model_scores = {}
    
    def get_provider(self, model_name: Optional[str] = None) -> LLMProvider:
        """獲取語言模型提供者"""
        model_name = model_name or settings.default_model
        
        # 如果提供者已經被初始化過，則直接返回
        if model_name in self.providers:
            return self.providers[model_name]
        
        # 獲取模型配置
        model_config = settings.get_model_config(model_name)
        
        # 獲取提供者類
        provider_class = self.provider_classes.get(model_config.provider)
        if not provider_class:
            raise ValueError(f"不支持的模型提供者: {model_config.provider}")
        
        # 初始化提供者
        try:
            provider = provider_class(model_config)
            self.providers[model_name] = provider
            return provider
        except Exception as e:
            logger.error(f"初始化模型提供者 {model_name} 失敗: {e}")
            raise
    
    def generate(
        self, 
        prompt: str, 
        system_prompt: Optional[str] = None,
        model_name: Optional[str] = None,
        json_mode: bool = False
    ) -> LLMResponse:
        """生成文本"""
        try:
            provider = self.get_provider(model_name)
            return provider.generate(prompt, system_prompt, json_mode)
        except Exception as e:
            logger.error(f"生成文本失敗: {e}")
            return LLMResponse(
                content="",
                model=model_name or settings.default_model,
                error=str(e)
            )
    
    def rate_response(self, response: LLMResponse, score: float, reason: Optional[str] = None) -> None:
        """為回應評分"""
        model = response.model
        
        # 初始化模型評分記錄
        if model not in self.model_scores:
            self.model_scores[model] = {
                "total_score": 0.0,
                "count": 0,
                "scores": []
            }
        
        # 添加評分
        self.model_scores[model]["total_score"] += score
        self.model_scores[model]["count"] += 1
        self.model_scores[model]["scores"].append({
            "request_id": response.request_id,
            "score": score,
            "reason": reason,
            "timestamp": time.time()
        })
        
        logger.info(f"模型 {model} 獲得評分: {score}, 原因: {reason}")
    
    def get_model_performance(self, model_name: Optional[str] = None) -> Dict[str, Any]:
        """獲取模型性能統計"""
        if model_name:
            if model_name not in self.model_scores:
                return {"error": f"沒有模型 {model_name} 的評分記錄"}
            
            scores = self.model_scores[model_name]
            return {
                "model": model_name,
                "average_score": scores["total_score"] / scores["count"] if scores["count"] > 0 else 0,
                "total_requests": scores["count"],
                "recent_scores": scores["scores"][-10:]  # 最近 10 條評分
            }
        else:
            # 返回所有模型的性能統計
            result = {}
            for model, scores in self.model_scores.items():
                result[model] = {
                    "average_score": scores["total_score"] / scores["count"] if scores["count"] > 0 else 0,
                    "total_requests": scores["count"]
                }
            return result
    
    def get_available_models(self) -> List[str]:
        """獲取可用模型列表"""
        return list(settings.models.keys())


# 建立全局 LLM 服務實例
llm_service = LLMService()