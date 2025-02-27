from typing import List, Dict, Any, Optional
from uuid import uuid4
from datetime import datetime
from pydantic import BaseModel, Field
from ..models.query_history import QueryHistoryModel
import logging

# 設定日誌
logger = logging.getLogger(__name__)

class ConversationContext(BaseModel):
    """對話上下文模型"""
    conversation_id: str = Field(default_factory=lambda: str(uuid4()), description="對話ID")
    queries: List[str] = Field(default_factory=list, description="查詢ID列表")
    context_variables: Dict[str, Any] = Field(default_factory=dict, description="上下文變數")
    created_at: datetime = Field(default_factory=datetime.now, description="創建時間")
    last_updated: datetime = Field(default_factory=datetime.now, description="最後更新時間")
    
    class Config:
        arbitrary_types_allowed = True


class ConversationManager:
    """對話管理服務"""
    
    def __init__(self, history_service=None):
        """
        初始化對話管理器
        
        Args:
            history_service: 歷史紀錄服務實例
        """
        self.active_conversations = {}  # session_id -> ConversationContext
        self.history_service = history_service
        self.logger = logging.getLogger(__name__)
        
    def get_or_create_conversation(self, session_id: str) -> ConversationContext:
        """
        獲取或創建對話上下文
        
        Args:
            session_id: 會話ID
            
        Returns:
            對話上下文
        """
        if session_id not in self.active_conversations:
            self.active_conversations[session_id] = ConversationContext()
            self.logger.info(f"創建新對話: {session_id}")
        
        return self.active_conversations[session_id]
    
    def add_query_to_conversation(self, session_id: str, query: QueryHistoryModel):
        """
        將查詢添加到對話中
        
        Args:
            session_id: 會話ID
            query: 查詢歷史模型
        """
        context = self.get_or_create_conversation(session_id)
        context.queries.append(query.id)
        context.last_updated = datetime.now()
        
        # 更新查詢模型中的對話ID
        if self.history_service:
            query.conversation_id = context.conversation_id
            self.history_service.update_query(query)
        
        self.logger.info(f"添加查詢到對話 {session_id}: {query.id}")
    
    def get_conversation_history(self, session_id: str, limit: int = 5) -> List[QueryHistoryModel]:
        """
        獲取對話歷史
        
        Args:
            session_id: 會話ID
            limit: 返回歷史數量限制
            
        Returns:
            查詢歷史列表
        """
        context = self.get_or_create_conversation(session_id)
        
        if not context.queries:
            return []
        
        # 取最近的查詢ID列表
        recent_query_ids = context.queries[-limit:] if len(context.queries) > limit else context.queries
        
        # 如果有歷史服務，從歷史服務獲取查詢記錄
        if self.history_service:
            history_entries = []
            for query_id in recent_query_ids:
                query = self.history_service.get_query_by_id(query_id)
                if query:
                    history_entries.append(query)
            return history_entries
        
        return []
    
    def update_context_variables(self, session_id: str, variables: Dict[str, Any]):
        """
        更新對話上下文變數
        
        Args:
            session_id: 會話ID
            variables: 要更新的變數字典
        """
        context = self.get_or_create_conversation(session_id)
        context.context_variables.update(variables)
    
    def get_context_variable(self, session_id: str, key: str, default=None) -> Any:
        """
        獲取對話上下文變數
        
        Args:
            session_id: 會話ID
            key: 變數鍵
            default: 默認值
            
        Returns:
            變數值
        """
        context = self.get_or_create_conversation(session_id)
        return context.context_variables.get(key, default)
    
    def clear_conversation(self, session_id: str):
        """
        清除對話
        
        Args:
            session_id: 會話ID
        """
        if session_id in self.active_conversations:
            del self.active_conversations[session_id]
            self.logger.info(f"清除對話: {session_id}")
    
    def get_conversation_ids(self) -> List[str]:
        """
        獲取所有對話ID列表
        
        Returns:
            對話ID列表
        """
        return list(self.active_conversations.keys())


# 創建全局對話管理器實例
conversation_manager = ConversationManager()