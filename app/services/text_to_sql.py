from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional, Union
from ..schema import get_table_schema_description
from ..utils import (
    settings, 
    get_function_suggestion, 
    generate_function_example, 
    get_fallback_query, 
    is_function_working
)
from .history_service import HistoryService
from .database_service import DatabaseService, QueryResult
from .llm_service import llm_service, LLMResponse
# 暫時註解掉 vector_store 以便程式可以啟動
# from .vector_store import vector_store
from .conversation_service import conversation_manager
from ..models import QueryHistoryModel
import logging
import json
import time
from uuid import uuid4
from datetime import datetime

class SimilarQuery(BaseModel):
    """相似查詢模型"""
    query: str = Field(description="原始自然語言查詢")
    sql: str = Field(description="SQL 查詢")
    similarity: float = Field(description="相似度分數 (0-1)")
    timestamp: Union[datetime, str] = Field(description="查詢時間")


class SQLResult(BaseModel):
    """SQL 查詢結果"""
    sql: str = Field(description="生成的 SQL 查詢")
    explanation: str = Field(description="SQL 查詢的解釋")
    parameters: Optional[Dict[str, Any]] = Field(default=None, description="SQL參數")
    execution_result: Optional[Dict[str, Any]] = Field(default=None, description="執行結果")
    query_id: Optional[str] = Field(default=None, description="查詢ID")
    similar_queries: Optional[List[SimilarQuery]] = Field(default=None, description="相似查詢列表")


class TextToSQLService:
    """文本到 SQL 轉換服務"""
    
    def __init__(self):
        # 初始化 LLM 服務
        self.llm_service = llm_service
        self.schema_description = get_table_schema_description()
        
        # 初始化歷史記錄和資料庫服務
        self.history_service = HistoryService(use_db=False)  # 預設使用 JSON 文件存儲
        self.db_service = DatabaseService()
        
        # 初始化向量存儲服務（暫時註解掉）
        # self.vector_store = vector_store
        # 建立一個临時空物件供使用
        from types import SimpleNamespace
        self.vector_store = SimpleNamespace()
        self.vector_store.search_similar = lambda *args, **kwargs: []
        self.vector_store.add_query = lambda *args, **kwargs: None
        
        # 初始化對話管理器
        self.conversation_manager = conversation_manager
        self.conversation_manager.history_service = self.history_service
        
        # 設定日誌
        self.logger = logging.getLogger(__name__)
    
    def text_to_sql(self, query: str, session_id: str = None, execute: bool = False, find_similar: bool = True) -> SQLResult:
        """
        將自然語言查詢轉換為 SQL 查詢
        
        Args:
            query: 自然語言查詢
            session_id: 會話ID，用於對話上下文管理
            execute: 是否執行生成的 SQL 查詢
            find_similar: 是否查找相似查詢
            
        Returns:
            SQL 查詢結果
        """
        # 生成查詢 ID
        query_id = str(uuid4())
        
        try:
            # 處理對話上下文
            conversation_history = []
            resolved_query = query
            entity_references = {}
            
            if session_id:
                # 獲取會話歷史
                conversation_history = self.conversation_manager.get_conversation_history(session_id, limit=5)
                
                if conversation_history:
                    # 解析引用
                    self.logger.info(f"嘗試解析查詢中的引用: {query}")
                    resolved_query, entity_references = self._resolve_references(query, conversation_history)
                    
                    if resolved_query != query:
                        self.logger.info(f"已解析查詢: {resolved_query}")
                    
            # 查找相似查詢
            similar_queries = []
            if find_similar:
                try:
                    # 查找相似的歷史查詢
                    similar_results = self.vector_store.search_similar(query, k=3)
                    
                    # 將結果轉換為 SimilarQuery 模型
                    similar_queries = [
                        SimilarQuery(
                            query=result["query"],
                            sql=result["sql"],
                            similarity=result["similarity"],
                            timestamp=result["timestamp"] if isinstance(result["timestamp"], str) else result["timestamp"].isoformat()
                        )
                        for result in similar_results
                        if result["similarity"] > 0.7  # 只返回相似度大於 0.7 的查詢
                    ]
                    
                    if similar_queries:
                        self.logger.info(f"找到 {len(similar_queries)} 個相似查詢")
                except Exception as e:
                    self.logger.error(f"查找相似查詢時出錯: {e}")
                    # 如果查找相似查詢時出錯，忽略錯誤，繼續處理
            
            # 嘗試推薦適合的資料庫函數
            function_suggestion = get_function_suggestion(query)
            
            # 建構基本 prompt
            prompt = self._build_prompt(query)
            
            # 如果有對話歷史，添加對話上下文到 prompt
            if conversation_history:
                conversation_prompt = self._build_conversation_context_prompt(conversation_history)
                prompt = f"{prompt}\n\n{conversation_prompt}"
            
            # 如果找到相似查詢，添加到 prompt 中
            if similar_queries:
                similar_query_prompt = self._build_similar_query_prompt(similar_queries)
                prompt = f"{prompt}\n\n{similar_query_prompt}"
                
            # 使用解析後的查詢（如果有）
            user_query_to_use = resolved_query if resolved_query != query else query
            
            # 如果有合適的函數推薦，檢查函數是否可用，並添加到 prompt 中
            if function_suggestion:
                func_name, func_info = function_suggestion
                
                # 檢查推薦的函數是否可用
                if is_function_working(func_name):
                    # 函數可用，使用正常的函數示例
                    example = generate_function_example(func_name, func_info)
                    
                    func_prompt = f"""
根據你的查詢，我推薦使用 {func_name} 函數：

函數名稱: {func_name}
描述: {func_info.get('description', '無描述')}
參數: {func_info.get('parameters', '無參數')}
返回類型: {func_info.get('return_type', '無返回類型')}

使用示例:
{example}

請儘量利用這個函數來回答用戶的查詢。
"""
                else:
                    # 函數不可用，提供替代方案
                    fallback_query = get_fallback_query(query, func_name)
                    
                    func_prompt = f"""
原本推薦使用 {func_name} 函數，但該函數目前可能不可用或有解析錯誤。

請使用以下替代查詢方式：
{fallback_query}

請根據用戶需求調整上述查詢中的參數值。
"""
                
                # 將用戶查詢和函數建議結合
                user_query = f"{user_query_to_use}\n\n{func_prompt}"
            else:
                user_query = user_query_to_use
            
            # 使用 LLM 服務生成回應
            model_name = settings.default_model
            llm_response = self.llm_service.generate(
                prompt=user_query,
                system_prompt=prompt,
                model_name=model_name,
                json_mode=True
            )
            
            # 檢查是否有錯誤
            if llm_response.is_error():
                raise Exception(f"生成回應時出錯: {llm_response.error}")
            
            # 解析回應
            result = llm_response.get_parsed_json()
            
            sql = result.get("sql", "")
            explanation = result.get("explanation", "")
            parameters = result.get("parameters", {})  # 提取參數
            
            # 創建查詢結果
            sql_result = SQLResult(
                sql=sql,
                explanation=explanation,
                parameters=parameters,  # 添加參數到結果
                query_id=query_id,
                similar_queries=similar_queries if similar_queries else None
            )
            
            # 添加到歷史記錄
            history_entry = QueryHistoryModel(
                id=query_id,
                user_query=query,
                generated_sql=sql,
                explanation=explanation,
                executed=False,
                created_at=datetime.now(),
                conversation_id=None if not session_id else self.conversation_manager.get_or_create_conversation(session_id).conversation_id,
                resolved_query=resolved_query if resolved_query != query else None,
                entity_references=entity_references,
                parameters=parameters  # 添加參數到歷史記錄
            )
            
            # 如果需要執行查詢
            if execute and sql:
                execution_result = self.execute_sql(sql, parameters)  # 傳遞參數到執行函數
                
                # 更新查詢結果和歷史記錄
                sql_result.execution_result = execution_result.to_dict()
                history_entry.executed = True
                history_entry.execution_time = execution_result.execution_time
                history_entry.error_message = execution_result.error
            
            # 保存歷史記錄
            self.history_service.add_query(history_entry)
            
            # 如果有會話ID，將查詢添加到對話
            if session_id:
                self.conversation_manager.add_query_to_conversation(session_id, history_entry)
            
            # 將查詢添加到向量存儲
            try:
                metadata = {
                    "executed": execute,
                    "model": settings.default_model,
                    "timestamp": datetime.now().isoformat(),
                    "parameters": parameters  # 添加參數信息到元數據
                }
                
                # 只有在查詢成功時才添加到向量存儲
                if sql and not sql.startswith("--"):
                    self.vector_store.add_query(query, sql, metadata)
            except Exception as e:
                self.logger.error(f"添加查詢到向量存儲時出錯: {e}")
                # 如果添加到向量存儲失敗，忽略錯誤，不影響主要功能
            
            return sql_result
            
        except Exception as e:
            self.logger.error(f"處理查詢時發生錯誤: {e}")
            
            # 記錄錯誤到歷史
            error_entry = QueryHistoryModel(
                id=query_id,
                user_query=query,
                generated_sql="-- 生成 SQL 查詢時發生錯誤",
                explanation=f"發生錯誤: {str(e)}",
                executed=False,
                error_message=str(e),
                created_at=datetime.now(),
                conversation_id=None if not session_id else self.conversation_manager.get_or_create_conversation(session_id).conversation_id
            )
            self.history_service.add_query(error_entry)
            
            return SQLResult(
                sql="-- 生成 SQL 查詢時發生錯誤",
                explanation=f"發生錯誤: {str(e)}",
                query_id=query_id
            )
    
    def execute_sql(self, sql: str, params: Optional[Dict[str, Any]] = None, visualize: bool = True) -> QueryResult:
        """
        執行 SQL 查詢
        
        Args:
            sql: SQL 查詢
            params: 查詢參數
            visualize: 是否生成視覺化圖表
            
        Returns:
            查詢結果
        """
        # 檢查資料庫連接
        if not self.db_service.is_connected():
            return QueryResult.from_error("未連接到資料庫")
        
        # 使用增強版查詢執行 (帶視覺化)
        if visualize:
            result, viz_metadata = self.db_service.execute_query_with_viz(sql, params, visualize=True)
            
            # 如果有視覺化數據，添加到結果中
            if viz_metadata:
                result_dict = result.to_dict()
                result_dict["visualization"] = viz_metadata
                # 在原來的 QueryResult 基礎上增加 visualization 欄位
                setattr(result, "visualization", viz_metadata)
                return result
            return result
        else:
            # 普通查詢執行（無視覺化）
            return self.db_service.execute_query(sql, params)
    
    def get_history(self, limit: int = 20, offset: int = 0) -> List[QueryHistoryModel]:
        """
        獲取查詢歷史
        
        Args:
            limit: 返回結果數量限制
            offset: 偏移量
            
        Returns:
            查詢歷史列表
        """
        return self.history_service.get_history(limit, offset)
    
    def _build_prompt(self, query: str) -> str:
        """建構基本提示詞"""
        return f"""你是一個專業的 PostgreSQL 資料庫專家。你的任務是將用戶的自然語言查詢轉換成精確的 SQL 查詢。
以下是資料庫結構的詳細描述，請根據這些信息生成正確的 SQL 查詢：

{self.schema_description}

重要說明：
1. 針對預約、時段可用性、服務搜尋等功能，優先使用資料庫函數而非直接編寫複雜查詢。
2. 當用戶詢問的問題可以使用資料庫函數解決時，優先生成使用函數的查詢，例如：
   - 查詢服務可用時段，使用 get_period_availability 函數
   - 查詢員工可用性，使用 get_staff_availability_by_date 函數
   - 模糊搜尋服務，使用 find_service 函數
   - 查詢預約詳情，使用 get_booking_details 函數
3. 重要：請將所有動態值轉換為參數化查詢，使用 :param_name 格式
   - 例如，不要寫 "WHERE name = 'John'"，而是寫 "WHERE name = :name"
   - 將參數值作為額外的 parameters 欄位返回

請遵循以下規則：
1. 僅生成有效的 PostgreSQL SQL 查詢
2. 確保使用正確的資料表名稱和欄位名稱
3. 適當處理表間關聯，根據查詢需求使用 JOIN
4. 提供詳細的查詢解釋，說明 SQL 查詢的邏輯和目的
5. 回傳 JSON 格式，包含 'sql', 'explanation' 和 'parameters' 欄位
6. 使用正確的聯結語法和條件
7. 僅產生只讀查詢 (SELECT)，不生成任何修改數據的查詢
8. 當查詢涉及多個表時，確保使用正確的JOIN條件和關聯欄位
9. 當使用資料庫函數時，確保正確傳遞所需參數
10. 以繁體中文解釋生成的 SQL 查詢
11. 若用戶的查詢不明確，請生成最合理的解釋和 SQL 查詢

回傳格式範例：
```json
{{
  "sql": "SELECT * FROM get_period_availability(:service_name, :period_name, :start_date, :end_date);",
  "parameters": {{
    "service_name": "基礎美容護理",
    "period_name": "上午",
    "start_date": "2025-01-15",
    "end_date": "2025-01-20"
  }},
  "explanation": "此查詢使用 get_period_availability 函數獲取 '基礎美容護理' 服務在 2025年1月15日 至 2025年1月20日 期間 '上午' 時段的可用預約情況。返回結果包含每天的可用預約數和總容量。"
}}
```

另一個使用JOIN的範例：
```json
{{
  "sql": "SELECT u.name, s.name AS service_name FROM n8n_booking_users u JOIN n8n_booking_staff_services ss ON u.id = ss.staff_id JOIN n8n_booking_services s ON ss.service_id = s.id WHERE u.role = :role AND u.is_active = :is_active;",
  "parameters": {{
    "role": "staff",
    "is_active": true
  }},
  "explanation": "此查詢從用戶資料表中選擇活躍的員工，並通過關聯表和服務表獲取這些員工提供的服務名稱。結果顯示員工姓名和其提供的服務。"
}}
```

請將回應格式化為可解析的 JSON。"""
        
    def _build_conversation_context_prompt(self, conversation_history) -> str:
        """建構對話上下文提示詞"""
        prompt = "以下是當前對話的上下文，這些是用戶最近的查詢及生成的SQL，請參考以理解用戶的意圖：\n\n"
        
        for i, history in enumerate(conversation_history):
            prompt += f"查詢 {i+1}:\n"
            prompt += f"用戶問題: {history.user_query}\n"
            if history.resolved_query and history.resolved_query != history.user_query:
                prompt += f"解析後問題: {history.resolved_query}\n"
            prompt += f"生成SQL: {history.generated_sql}\n\n"
        
        prompt += """
請根據上述對話歷史，理解用戶的當前查詢。用戶可能會使用代詞（如「它們」、「這些」、「他」）參考之前的實體，
或者省略之前提到過的條件。你應該識別這些潛在的指代，並在生成SQL時包含必要的上下文信息。

如果你可以識別出當前查詢中的代詞或省略，請在返回的JSON中加入以下欄位：
1. entity_references: 一個字典，表示你識別出的實體引用，例如 {"它們": "服務", "這個員工": "John Smith"}

例如，如果之前的查詢是關於「美甲服務」，而當前查詢是「它的價格是多少？」，你應該理解「它」指的是「美甲服務」。
"""
        return prompt
        
    def _resolve_references(self, query: str, conversation_history) -> str:
        """解析查詢中的引用"""
        if not conversation_history:
            return query
            
        # 構建系統提示詞
        system_prompt = """你是參考解析專家。你的任務是分析用戶的當前查詢，並解析其中可能存在的代詞或隱含引用。
        
請識別當前查詢中的代詞（如「它們」、「這些」、「他」等），並使用對話歷史中的信息將其替換為具體的實體名稱或描述。

你的回應必須是JSON格式，包含以下欄位:
1. resolved_query: 完整的、獨立的查詢，其中不包含任何需要依賴上下文才能理解的代詞或引用
2. entity_references: 一個字典，表示你識別出的實體引用，例如 {"它們": "服務", "這個員工": "John Smith"}

例如:
輸入: "它們的價格是多少?"
輸出: 
```json
{
  "resolved_query": "美甲服務的價格是多少?",
  "entity_references": {"它們": "美甲服務"}
}
```
"""
        
        # 格式化對話歷史
        history_text = "\n\n對話歷史:\n"
        for i, hist in enumerate(conversation_history[-3:]):  # 使用最近3個查詢
            history_text += f"用戶問題 {i+1}: {hist.user_query}\n"
            if hist.resolved_query and hist.resolved_query != hist.user_query:
                history_text += f"解析後問題: {hist.resolved_query}\n"
            history_text += f"SQL: {hist.generated_sql}\n\n"
        
        # 添加當前查詢
        user_prompt = f"{history_text}\n\n當前查詢: {query}\n\n請解析當前查詢中的引用，返回一個完整的查詢和識別出的實體引用。"
        
        # 使用LLM解析引用
        response = self.llm_service.generate(
            prompt=user_prompt,
            system_prompt=system_prompt,
            model_name=settings.default_model,
            json_mode=True
        )
        
        if response.is_error():
            self.logger.warning(f"參考解析失敗: {response.error}，使用原始查詢")
            return query
            
        try:
            result = response.get_parsed_json()
            resolved_query = result.get("resolved_query", query)
            entity_references = result.get("entity_references", {})
            
            # 記錄識別的實體引用
            if entity_references:
                self.logger.info(f"識別實體引用: {entity_references}")
            
            return resolved_query, entity_references
        except Exception as e:
            self.logger.warning(f"解析LLM響應失敗: {e}，使用原始查詢")
            return query, {}
    
    def _build_similar_query_prompt(self, similar_queries: List[SimilarQuery]) -> str:
        """建構相似查詢提示詞"""
        prompt = "我發現以下與您當前查詢相似的歷史查詢，可供參考：\n\n"
        
        for i, query in enumerate(similar_queries):
            similarity_percent = int(query.similarity * 100)
            prompt += f"相似查詢 {i+1} (相似度: {similarity_percent}%):\n"
            prompt += f"自然語言查詢: {query.query}\n"
            prompt += f"SQL查詢: {query.sql}\n\n"
        
        prompt += "請參考這些相似查詢，為用戶生成最適合的SQL查詢。您可以直接使用相似查詢，或者根據用戶的需求進行調整。"
        
        return prompt