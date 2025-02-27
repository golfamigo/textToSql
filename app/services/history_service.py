from datetime import datetime
from typing import List, Optional, Dict, Any
import json
import os
from uuid import uuid4
from ..models import QueryHistoryModel, QueryTemplateModel
import logging
from sqlalchemy import create_engine, Column, String, Boolean, Float, DateTime, Text, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from sqlalchemy.orm import sessionmaker, Session
from ..utils import settings

# 設定日誌
logger = logging.getLogger(__name__)

# SQLAlchemy ORM 定義
Base = declarative_base()


class QueryHistory(Base):
    """查詢歷史 SQLAlchemy 模型"""
    __tablename__ = "query_history"
    
    id = Column(UUID, primary_key=True, default=uuid4)
    user_query = Column(Text, nullable=False)
    generated_sql = Column(Text, nullable=False)
    explanation = Column(Text, nullable=False)
    executed = Column(Boolean, default=False)
    execution_time = Column(Float, nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, nullable=True, onupdate=datetime.now)
    
    # 對話支持欄位
    conversation_id = Column(String, nullable=True)
    references_query_id = Column(String, nullable=True)
    resolved_query = Column(Text, nullable=True)
    entity_references = Column(JSONB, nullable=True)
    
    # 參數化查詢
    parameters = Column(JSONB, nullable=True)
    
    # 收藏與模板支持
    is_favorite = Column(Boolean, default=False)
    is_template = Column(Boolean, default=False)
    template_name = Column(String, nullable=True)
    template_description = Column(Text, nullable=True)
    template_tags = Column(ARRAY(String), nullable=True)


class QueryTemplate(Base):
    """查詢模板 SQLAlchemy 模型"""
    __tablename__ = "query_templates"
    
    id = Column(UUID, primary_key=True, default=uuid4)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    user_query = Column(Text, nullable=False)
    generated_sql = Column(Text, nullable=False)
    explanation = Column(Text, nullable=True)
    parameters = Column(JSONB, nullable=True)
    tags = Column(ARRAY(String), nullable=True)
    usage_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, nullable=True, onupdate=datetime.now)


class HistoryService:
    """查詢歷史服務"""
    
    def __init__(self, use_db=True):
        """
        初始化查詢歷史服務
        
        Args:
            use_db (bool): 是否使用資料庫存儲歷史記錄，如果為 False 則使用 JSON 文件
        """
        self.use_db = use_db
        self.history_file = os.path.join(os.path.dirname(__file__), "../../query_history.json")
        self.templates_file = os.path.join(os.path.dirname(__file__), "../../query_templates.json")
        
        if use_db:
            try:
                self.engine = create_engine(settings.database_url)
                Base.metadata.create_all(self.engine)
                self.Session = sessionmaker(bind=self.engine)
                logger.info("已連接到資料庫並初始化查詢歷史表")
            except Exception as e:
                logger.error(f"連接資料庫失敗: {e}")
                self.use_db = False
                logger.info("改用 JSON 文件存儲歷史記錄")
    
    def add_query(self, query_model: QueryHistoryModel) -> QueryHistoryModel:
        """
        添加查詢歷史記錄
        
        Args:
            query_model: 查詢歷史模型
            
        Returns:
            保存的查詢歷史模型
        """
        if self.use_db:
            return self._add_query_to_db(query_model)
        else:
            return self._add_query_to_file(query_model)
    
    def _add_query_to_db(self, query_model: QueryHistoryModel) -> QueryHistoryModel:
        """使用資料庫存儲查詢歷史"""
        try:
            with self.Session() as session:
                # 將 Pydantic 模型轉換為 SQLAlchemy 模型
                query_history = QueryHistory(
                    id=query_model.id,
                    user_query=query_model.user_query,
                    generated_sql=query_model.generated_sql,
                    explanation=query_model.explanation,
                    executed=query_model.executed,
                    execution_time=query_model.execution_time,
                    error_message=query_model.error_message,
                    created_at=datetime.now(),
                    conversation_id=query_model.conversation_id,
                    references_query_id=query_model.references_query_id,
                    resolved_query=query_model.resolved_query,
                    entity_references=query_model.entity_references,
                    parameters=query_model.parameters,
                    is_favorite=query_model.is_favorite,
                    is_template=query_model.is_template,
                    template_name=query_model.template_name,
                    template_description=query_model.template_description,
                    template_tags=query_model.template_tags if query_model.template_tags else None
                )
                
                session.add(query_history)
                session.commit()
                
                return query_model
        except Exception as e:
            logger.error(f"保存查詢歷史到資料庫失敗: {e}")
            # 失敗時改用文件存儲
            return self._add_query_to_file(query_model)
    
    def _add_query_to_file(self, query_model: QueryHistoryModel) -> QueryHistoryModel:
        """使用 JSON 文件存儲查詢歷史"""
        try:
            # 讀取現有歷史記錄
            history = []
            if os.path.exists(self.history_file):
                with open(self.history_file, "r", encoding="utf-8") as f:
                    history = json.load(f)
            
            # 添加新記錄
            history.append({
                "id": str(query_model.id),
                "user_query": query_model.user_query,
                "generated_sql": query_model.generated_sql,
                "explanation": query_model.explanation,
                "executed": query_model.executed,
                "execution_time": query_model.execution_time,
                "error_message": query_model.error_message,
                "created_at": datetime.now().isoformat(),
                "conversation_id": query_model.conversation_id,
                "references_query_id": query_model.references_query_id,
                "resolved_query": query_model.resolved_query,
                "entity_references": query_model.entity_references,
                "parameters": query_model.parameters,
                "is_favorite": query_model.is_favorite,
                "is_template": query_model.is_template,
                "template_name": query_model.template_name,
                "template_description": query_model.template_description,
                "template_tags": query_model.template_tags
            })
            
            # 寫入文件
            with open(self.history_file, "w", encoding="utf-8") as f:
                json.dump(history, f, ensure_ascii=False, indent=2)
            
            return query_model
        except Exception as e:
            logger.error(f"保存查詢歷史到文件失敗: {e}")
            return query_model
    
    def get_history(self, limit: int = 20, offset: int = 0) -> List[QueryHistoryModel]:
        """
        獲取查詢歷史記錄
        
        Args:
            limit: 返回數量限制
            offset: 偏移量
            
        Returns:
            查詢歷史記錄列表
        """
        if self.use_db:
            return self._get_history_from_db(limit, offset)
        else:
            return self._get_history_from_file(limit, offset)
    
    def get_query_by_id(self, query_id: str) -> Optional[QueryHistoryModel]:
        """根據 ID 獲取查詢歷史"""
        if self.use_db:
            return self._get_query_by_id_from_db(query_id)
        else:
            return self._get_query_by_id_from_file(query_id)
            
    def _get_history_from_db(self, limit: int, offset: int) -> List[QueryHistoryModel]:
        """從資料庫獲取查詢歷史"""
        try:
            with self.Session() as session:
                records = session.query(QueryHistory).order_by(
                    QueryHistory.created_at.desc()
                ).limit(limit).offset(offset).all()
                
                return [
                    QueryHistoryModel(
                        id=record.id,
                        user_query=record.user_query,
                        generated_sql=record.generated_sql,
                        explanation=record.explanation,
                        executed=record.executed,
                        execution_time=record.execution_time,
                        error_message=record.error_message,
                        created_at=record.created_at,
                        updated_at=record.updated_at,
                        conversation_id=record.conversation_id,
                        references_query_id=record.references_query_id,
                        resolved_query=record.resolved_query,
                        entity_references=record.entity_references or {},
                        parameters=record.parameters or {},
                        is_favorite=record.is_favorite or False,
                        is_template=record.is_template or False,
                        template_name=record.template_name,
                        template_description=record.template_description,
                        template_tags=record.template_tags or []
                    ) for record in records
                ]
        except Exception as e:
            logger.error(f"從資料庫獲取查詢歷史失敗: {e}")
            # 失敗時改用文件讀取
            return self._get_history_from_file(limit, offset)
    
    def _get_query_by_id_from_db(self, query_id: str) -> Optional[QueryHistoryModel]:
        """從資料庫獲取指定 ID 的查詢歷史"""
        try:
            with self.Session() as session:
                record = session.query(QueryHistory).filter(QueryHistory.id == query_id).first()
                if record:
                    return QueryHistoryModel(
                        id=record.id,
                        user_query=record.user_query,
                        generated_sql=record.generated_sql,
                        explanation=record.explanation,
                        executed=record.executed,
                        execution_time=record.execution_time,
                        error_message=record.error_message,
                        created_at=record.created_at,
                        updated_at=record.updated_at,
                        conversation_id=record.conversation_id,
                        references_query_id=record.references_query_id,
                        resolved_query=record.resolved_query,
                        entity_references=record.entity_references or {},
                        parameters=record.parameters or {},
                        is_favorite=record.is_favorite or False,
                        is_template=record.is_template or False,
                        template_name=record.template_name,
                        template_description=record.template_description,
                        template_tags=record.template_tags or []
                    )
                return None
        except Exception as e:
            logger.error(f"從資料庫獲取查詢歷史失敗: {e}")
            return None
    
    def _get_query_by_id_from_file(self, query_id: str) -> Optional[QueryHistoryModel]:
        """從文件獲取指定 ID 的查詢歷史"""
        try:
            if not os.path.exists(self.history_file):
                return None
            
            with open(self.history_file, "r", encoding="utf-8") as f:
                history = json.load(f)
            
            for record in history:
                if record.get("id") == query_id:
                    return QueryHistoryModel(
                        id=record.get("id"),
                        user_query=record.get("user_query"),
                        generated_sql=record.get("generated_sql"),
                        explanation=record.get("explanation"),
                        executed=record.get("executed", False),
                        execution_time=record.get("execution_time"),
                        error_message=record.get("error_message"),
                        created_at=record.get("created_at"),
                        conversation_id=record.get("conversation_id"),
                        references_query_id=record.get("references_query_id"),
                        resolved_query=record.get("resolved_query"),
                        entity_references=record.get("entity_references", {}),
                        parameters=record.get("parameters", {}),
                        is_favorite=record.get("is_favorite", False),
                        is_template=record.get("is_template", False),
                        template_name=record.get("template_name"),
                        template_description=record.get("template_description"),
                        template_tags=record.get("template_tags", [])
                    )
            return None
        except Exception as e:
            logger.error(f"從文件獲取查詢歷史失敗: {e}")
            return None
                
    def get_history_by_conversation(self, conversation_id: str, limit: int = 20) -> List[QueryHistoryModel]:
        """獲取對話相關的查詢歷史"""
        if self.use_db:
            return self._get_history_by_conversation_from_db(conversation_id, limit)
        else:
            return self._get_history_by_conversation_from_file(conversation_id, limit)
    
    def _get_history_by_conversation_from_db(self, conversation_id: str, limit: int) -> List[QueryHistoryModel]:
        """從資料庫獲取對話相關的查詢歷史"""
        try:
            with self.Session() as session:
                records = session.query(QueryHistory).filter(
                    QueryHistory.conversation_id == conversation_id
                ).order_by(QueryHistory.created_at.desc()).limit(limit).all()
                
                return [
                    QueryHistoryModel(
                        id=record.id,
                        user_query=record.user_query,
                        generated_sql=record.generated_sql,
                        explanation=record.explanation,
                        executed=record.executed,
                        execution_time=record.execution_time,
                        error_message=record.error_message,
                        created_at=record.created_at,
                        updated_at=record.updated_at,
                        conversation_id=record.conversation_id,
                        references_query_id=record.references_query_id,
                        resolved_query=record.resolved_query,
                        entity_references=record.entity_references or {}
                    ) for record in records
                ]
        except Exception as e:
            logger.error(f"從資料庫獲取對話歷史失敗: {e}")
            return []
    
    def _get_history_by_conversation_from_file(self, conversation_id: str, limit: int) -> List[QueryHistoryModel]:
        """從文件獲取對話相關的查詢歷史"""
        try:
            if not os.path.exists(self.history_file):
                return []
            
            with open(self.history_file, "r", encoding="utf-8") as f:
                history = json.load(f)
            
            # 過濾並排序
            conversation_history = [record for record in history if record.get("conversation_id") == conversation_id]
            sorted_history = sorted(conversation_history, key=lambda x: x.get("created_at", ""), reverse=True)
            limited_history = sorted_history[:limit]
            
            # 轉換為 Pydantic 模型
            return [
                QueryHistoryModel(
                    id=record.get("id"),
                    user_query=record.get("user_query"),
                    generated_sql=record.get("generated_sql"),
                    explanation=record.get("explanation"),
                    executed=record.get("executed", False),
                    execution_time=record.get("execution_time"),
                    error_message=record.get("error_message"),
                    created_at=record.get("created_at"),
                    conversation_id=record.get("conversation_id"),
                    references_query_id=record.get("references_query_id"),
                    resolved_query=record.get("resolved_query"),
                    entity_references=record.get("entity_references", {}),
                    parameters=record.get("parameters", {}),
                    is_favorite=record.get("is_favorite", False),
                    is_template=record.get("is_template", False),
                    template_name=record.get("template_name"),
                    template_description=record.get("template_description"),
                    template_tags=record.get("template_tags", [])
                ) for record in limited_history
            ]
        except Exception as e:
            logger.error(f"從文件獲取對話歷史失敗: {e}")
            return []
            
    # 收藏功能相關方法
    def toggle_favorite(self, query_id: str) -> bool:
        """切換查詢的收藏狀態"""
        query = self.get_query_by_id(query_id)
        if not query:
            return False
        
        # 切換收藏狀態
        query.is_favorite = not query.is_favorite
        return self.update_query(query)
        
    def get_favorites(self, limit: int = 20, offset: int = 0) -> List[QueryHistoryModel]:
        """獲取收藏的查詢"""
        if self.use_db:
            return self._get_favorites_from_db(limit, offset)
        else:
            return self._get_favorites_from_file(limit, offset)
            
    def _get_favorites_from_db(self, limit: int, offset: int) -> List[QueryHistoryModel]:
        """從資料庫獲取收藏的查詢"""
        try:
            with self.Session() as session:
                records = session.query(QueryHistory).filter(
                    QueryHistory.is_favorite == True
                ).order_by(QueryHistory.created_at.desc()).limit(limit).offset(offset).all()
                
                return [
                    QueryHistoryModel(
                        id=record.id,
                        user_query=record.user_query,
                        generated_sql=record.generated_sql,
                        explanation=record.explanation,
                        executed=record.executed,
                        execution_time=record.execution_time,
                        error_message=record.error_message,
                        created_at=record.created_at,
                        updated_at=record.updated_at,
                        conversation_id=record.conversation_id,
                        references_query_id=record.references_query_id,
                        resolved_query=record.resolved_query,
                        entity_references=record.entity_references or {},
                        parameters=record.parameters or {},
                        is_favorite=record.is_favorite,
                        is_template=record.is_template,
                        template_name=record.template_name,
                        template_description=record.template_description,
                        template_tags=record.template_tags or []
                    ) for record in records
                ]
        except Exception as e:
            logger.error(f"從資料庫獲取收藏查詢失敗: {e}")
            return self._get_favorites_from_file(limit, offset)
            
    def _get_favorites_from_file(self, limit: int, offset: int) -> List[QueryHistoryModel]:
        """從文件獲取收藏的查詢"""
        try:
            if not os.path.exists(self.history_file):
                return []
            
            with open(self.history_file, "r", encoding="utf-8") as f:
                history = json.load(f)
            
            # 過濾、排序、分頁
            favorite_history = [record for record in history if record.get("is_favorite", False)]
            sorted_history = sorted(favorite_history, key=lambda x: x.get("created_at", ""), reverse=True)
            paged_history = sorted_history[offset:offset + limit]
            
            # 轉換為 Pydantic 模型
            return [
                QueryHistoryModel(
                    id=record.get("id"),
                    user_query=record.get("user_query"),
                    generated_sql=record.get("generated_sql"),
                    explanation=record.get("explanation"),
                    executed=record.get("executed", False),
                    execution_time=record.get("execution_time"),
                    error_message=record.get("error_message"),
                    created_at=record.get("created_at"),
                    conversation_id=record.get("conversation_id"),
                    references_query_id=record.get("references_query_id"),
                    resolved_query=record.get("resolved_query"),
                    entity_references=record.get("entity_references", {}),
                    parameters=record.get("parameters", {}),
                    is_favorite=record.get("is_favorite", False),
                    is_template=record.get("is_template", False),
                    template_name=record.get("template_name"),
                    template_description=record.get("template_description"),
                    template_tags=record.get("template_tags", [])
                ) for record in paged_history
            ]
        except Exception as e:
            logger.error(f"從文件獲取收藏查詢失敗: {e}")
            return []
    
    # 模板功能相關方法
    def save_as_template(self, query_id: str, name: str, description: Optional[str] = None, 
                        tags: List[str] = None) -> Optional[QueryTemplateModel]:
        """將查詢保存為模板"""
        # 獲取查詢歷史
        query = self.get_query_by_id(query_id)
        if not query:
            logger.error(f"無法找到查詢ID為 {query_id} 的記錄")
            return None
            
        # 設置為模板
        query.is_template = True
        query.template_name = name
        query.template_description = description
        query.template_tags = tags or []
        
        # 更新查詢記錄
        success = self.update_query(query)
        if not success:
            logger.error(f"更新查詢記錄為模板失敗")
            return None
            
        # 創建模板記錄
        template = QueryTemplateModel(
            name=name,
            description=description,
            user_query=query.user_query,
            generated_sql=query.generated_sql,
            explanation=query.explanation,
            parameters=query.parameters,
            tags=tags or []
        )
        
        # 保存模板
        return self._save_template(template)
    
    def _save_template(self, template: QueryTemplateModel) -> QueryTemplateModel:
        """保存查詢模板"""
        if self.use_db:
            return self._save_template_to_db(template)
        else:
            return self._save_template_to_file(template)
            
    def _save_template_to_db(self, template: QueryTemplateModel) -> QueryTemplateModel:
        """將模板保存到資料庫"""
        try:
            with self.Session() as session:
                # 將 Pydantic 模型轉換為 SQLAlchemy 模型
                template_record = QueryTemplate(
                    id=template.id,
                    name=template.name,
                    description=template.description,
                    user_query=template.user_query,
                    generated_sql=template.generated_sql,
                    explanation=template.explanation,
                    parameters=template.parameters,
                    tags=template.tags,
                    usage_count=template.usage_count,
                    created_at=datetime.now()
                )
                
                session.add(template_record)
                session.commit()
                
                return template
        except Exception as e:
            logger.error(f"保存模板到資料庫失敗: {e}")
            # 失敗時改用文件存儲
            return self._save_template_to_file(template)
            
    def _save_template_to_file(self, template: QueryTemplateModel) -> QueryTemplateModel:
        """將模板保存到文件"""
        try:
            # 讀取現有模板
            templates = []
            if os.path.exists(self.templates_file):
                with open(self.templates_file, "r", encoding="utf-8") as f:
                    templates = json.load(f)
            
            # 添加新模板
            templates.append({
                "id": str(template.id),
                "name": template.name,
                "description": template.description,
                "user_query": template.user_query,
                "generated_sql": template.generated_sql,
                "explanation": template.explanation,
                "parameters": template.parameters,
                "tags": template.tags,
                "usage_count": template.usage_count,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            })
            
            # 寫入文件
            with open(self.templates_file, "w", encoding="utf-8") as f:
                json.dump(templates, f, ensure_ascii=False, indent=2)
            
            return template
        except Exception as e:
            logger.error(f"保存模板到文件失敗: {e}")
            return template
            
    def get_templates(self, limit: int = 20, offset: int = 0, 
                     tag: Optional[str] = None) -> List[QueryTemplateModel]:
        """獲取查詢模板"""
        if self.use_db:
            return self._get_templates_from_db(limit, offset, tag)
        else:
            return self._get_templates_from_file(limit, offset, tag)
            
    def _get_templates_from_db(self, limit: int, offset: int, 
                              tag: Optional[str] = None) -> List[QueryTemplateModel]:
        """從資料庫獲取查詢模板"""
        try:
            with self.Session() as session:
                # 創建查詢
                query = session.query(QueryTemplate)
                
                # 如果有標籤過濾
                if tag:
                    query = query.filter(QueryTemplate.tags.contains([tag]))
                    
                # 排序和分頁
                records = query.order_by(
                    QueryTemplate.usage_count.desc(), 
                    QueryTemplate.created_at.desc()
                ).limit(limit).offset(offset).all()
                
                # 轉換為 Pydantic 模型
                return [
                    QueryTemplateModel(
                        id=record.id,
                        name=record.name,
                        description=record.description,
                        user_query=record.user_query,
                        generated_sql=record.generated_sql,
                        explanation=record.explanation,
                        parameters=record.parameters or {},
                        tags=record.tags or [],
                        usage_count=record.usage_count,
                        created_at=record.created_at,
                        updated_at=record.updated_at
                    ) for record in records
                ]
        except Exception as e:
            logger.error(f"從資料庫獲取模板失敗: {e}")
            return self._get_templates_from_file(limit, offset, tag)
            
    def _get_templates_from_file(self, limit: int, offset: int, 
                               tag: Optional[str] = None) -> List[QueryTemplateModel]:
        """從文件獲取查詢模板"""
        try:
            if not os.path.exists(self.templates_file):
                return []
                
            with open(self.templates_file, "r", encoding="utf-8") as f:
                templates = json.load(f)
                
            # 如果有標籤過濾
            if tag:
                templates = [t for t in templates if tag in t.get("tags", [])]
                
            # 排序
            sorted_templates = sorted(
                templates, 
                key=lambda x: (x.get("usage_count", 0), x.get("created_at", "")), 
                reverse=True
            )
            
            # 分頁
            paged_templates = sorted_templates[offset:offset + limit]
            
            # 轉換為 Pydantic 模型
            return [
                QueryTemplateModel(
                    id=record.get("id"),
                    name=record.get("name"),
                    description=record.get("description"),
                    user_query=record.get("user_query"),
                    generated_sql=record.get("generated_sql"),
                    explanation=record.get("explanation"),
                    parameters=record.get("parameters", {}),
                    tags=record.get("tags", []),
                    usage_count=record.get("usage_count", 0),
                    created_at=record.get("created_at"),
                    updated_at=record.get("updated_at")
                ) for record in paged_templates
            ]
        except Exception as e:
            logger.error(f"從文件獲取模板失敗: {e}")
            return []
            
    def get_template_by_id(self, template_id: str) -> Optional[QueryTemplateModel]:
        """根據 ID 獲取模板"""
        if self.use_db:
            return self._get_template_by_id_from_db(template_id)
        else:
            return self._get_template_by_id_from_file(template_id)
            
    def _get_template_by_id_from_db(self, template_id: str) -> Optional[QueryTemplateModel]:
        """從資料庫獲取指定 ID 的模板"""
        try:
            with self.Session() as session:
                record = session.query(QueryTemplate).filter(QueryTemplate.id == template_id).first()
                if record:
                    return QueryTemplateModel(
                        id=record.id,
                        name=record.name,
                        description=record.description,
                        user_query=record.user_query,
                        generated_sql=record.generated_sql,
                        explanation=record.explanation,
                        parameters=record.parameters or {},
                        tags=record.tags or [],
                        usage_count=record.usage_count,
                        created_at=record.created_at,
                        updated_at=record.updated_at
                    )
                return None
        except Exception as e:
            logger.error(f"從資料庫獲取模板失敗: {e}")
            return self._get_template_by_id_from_file(template_id)
            
    def _get_template_by_id_from_file(self, template_id: str) -> Optional[QueryTemplateModel]:
        """從文件獲取指定 ID 的模板"""
        try:
            if not os.path.exists(self.templates_file):
                return None
                
            with open(self.templates_file, "r", encoding="utf-8") as f:
                templates = json.load(f)
                
            # 查找指定 ID 的模板
            for record in templates:
                if record.get("id") == template_id:
                    return QueryTemplateModel(
                        id=record.get("id"),
                        name=record.get("name"),
                        description=record.get("description"),
                        user_query=record.get("user_query"),
                        generated_sql=record.get("generated_sql"),
                        explanation=record.get("explanation"),
                        parameters=record.get("parameters", {}),
                        tags=record.get("tags", []),
                        usage_count=record.get("usage_count", 0),
                        created_at=record.get("created_at"),
                        updated_at=record.get("updated_at")
                    )
            return None
        except Exception as e:
            logger.error(f"從文件獲取模板失敗: {e}")
            return None
            
    def update_template(self, template: QueryTemplateModel) -> bool:
        """更新查詢模板"""
        if self.use_db:
            return self._update_template_in_db(template)
        else:
            return self._update_template_in_file(template)
            
    def _update_template_in_db(self, template: QueryTemplateModel) -> bool:
        """在資料庫中更新查詢模板"""
        try:
            with self.Session() as session:
                record = session.query(QueryTemplate).filter(QueryTemplate.id == template.id).first()
                if not record:
                    return False
                    
                # 更新欄位
                record.name = template.name
                record.description = template.description
                record.user_query = template.user_query
                record.generated_sql = template.generated_sql
                record.explanation = template.explanation
                record.parameters = template.parameters
                record.tags = template.tags
                record.usage_count = template.usage_count
                record.updated_at = datetime.now()
                
                session.commit()
                return True
        except Exception as e:
            logger.error(f"更新資料庫中的模板失敗: {e}")
            return self._update_template_in_file(template)
            
    def _update_template_in_file(self, template: QueryTemplateModel) -> bool:
        """在文件中更新查詢模板"""
        try:
            if not os.path.exists(self.templates_file):
                return False
                
            with open(self.templates_file, "r", encoding="utf-8") as f:
                templates = json.load(f)
                
            # 查找並更新
            found = False
            for i, record in enumerate(templates):
                if record.get("id") == str(template.id):
                    templates[i] = {
                        "id": str(template.id),
                        "name": template.name,
                        "description": template.description,
                        "user_query": template.user_query,
                        "generated_sql": template.generated_sql,
                        "explanation": template.explanation,
                        "parameters": template.parameters,
                        "tags": template.tags,
                        "usage_count": template.usage_count,
                        "created_at": record.get("created_at"),
                        "updated_at": datetime.now().isoformat()
                    }
                    found = True
                    break
                    
            if not found:
                return False
                
            # 保存更新
            with open(self.templates_file, "w", encoding="utf-8") as f:
                json.dump(templates, f, ensure_ascii=False, indent=2)
                
            return True
        except Exception as e:
            logger.error(f"更新文件中的模板失敗: {e}")
            return False
            
    def delete_template(self, template_id: str) -> bool:
        """刪除查詢模板"""
        if self.use_db:
            return self._delete_template_from_db(template_id)
        else:
            return self._delete_template_from_file(template_id)
            
    def _delete_template_from_db(self, template_id: str) -> bool:
        """從資料庫刪除模板"""
        try:
            with self.Session() as session:
                record = session.query(QueryTemplate).filter(QueryTemplate.id == template_id).first()
                if not record:
                    return False
                    
                session.delete(record)
                session.commit()
                return True
        except Exception as e:
            logger.error(f"從資料庫刪除模板失敗: {e}")
            return False
            
    def _delete_template_from_file(self, template_id: str) -> bool:
        """從文件刪除模板"""
        try:
            if not os.path.exists(self.templates_file):
                return False
                
            with open(self.templates_file, "r", encoding="utf-8") as f:
                templates = json.load(f)
                
            # 查找並刪除
            templates = [t for t in templates if t.get("id") != template_id]
            
            # 保存更新
            with open(self.templates_file, "w", encoding="utf-8") as f:
                json.dump(templates, f, ensure_ascii=False, indent=2)
                
            return True
        except Exception as e:
            logger.error(f"從文件刪除模板失敗: {e}")
            return False
            
    def increment_template_usage(self, template_id: str) -> bool:
        """增加模板使用次數"""
        template = self.get_template_by_id(template_id)
        if not template:
            return False
            
        template.usage_count += 1
        return self.update_template(template)
                
    def update_query(self, query: QueryHistoryModel) -> bool:
        """更新查詢歷史"""
        if self.use_db:
            return self._update_query_in_db(query)
        else:
            return self._update_query_in_file(query)
    
    def _update_query_in_db(self, query: QueryHistoryModel) -> bool:
        """在資料庫中更新查詢歷史"""
        try:
            with self.Session() as session:
                record = session.query(QueryHistory).filter(QueryHistory.id == query.id).first()
                if not record:
                    return False
                
                # 更新欄位
                record.user_query = query.user_query
                record.generated_sql = query.generated_sql
                record.explanation = query.explanation
                record.executed = query.executed
                record.execution_time = query.execution_time
                record.error_message = query.error_message
                record.conversation_id = query.conversation_id
                record.references_query_id = query.references_query_id
                record.resolved_query = query.resolved_query
                record.entity_references = query.entity_references
                record.parameters = query.parameters
                record.is_favorite = query.is_favorite
                record.is_template = query.is_template
                record.template_name = query.template_name
                record.template_description = query.template_description
                record.template_tags = query.template_tags
                record.updated_at = datetime.now()
                
                session.commit()
                return True
        except Exception as e:
            logger.error(f"更新資料庫中的查詢歷史失敗: {e}")
            return False
    
    def _update_query_in_file(self, query: QueryHistoryModel) -> bool:
        """在文件中更新查詢歷史"""
        try:
            if not os.path.exists(self.history_file):
                return False
                
            with open(self.history_file, "r", encoding="utf-8") as f:
                history = json.load(f)
                
            # 查找並更新
            found = False
            for i, record in enumerate(history):
                if record.get("id") == str(query.id):
                    history[i] = {
                        "id": str(query.id),
                        "user_query": query.user_query,
                        "generated_sql": query.generated_sql,
                        "explanation": query.explanation,
                        "executed": query.executed,
                        "execution_time": query.execution_time,
                        "error_message": query.error_message,
                        "created_at": record.get("created_at"),
                        "conversation_id": query.conversation_id,
                        "references_query_id": query.references_query_id,
                        "resolved_query": query.resolved_query,
                        "entity_references": query.entity_references,
                        "parameters": query.parameters,
                        "is_favorite": query.is_favorite,
                        "is_template": query.is_template,
                        "template_name": query.template_name,
                        "template_description": query.template_description,
                        "template_tags": query.template_tags
                    }
                    found = True
                    break
                    
            if not found:
                return False
                
            # 保存更新
            with open(self.history_file, "w", encoding="utf-8") as f:
                json.dump(history, f, ensure_ascii=False, indent=2)
                
            return True
        except Exception as e:
            logger.error(f"更新文件中的查詢歷史失敗: {e}")
            return False
    
    def _get_history_from_db(self, limit: int, offset: int) -> List[QueryHistoryModel]:
        """從資料庫獲取查詢歷史"""
        try:
            with self.Session() as session:
                records = session.query(QueryHistory).order_by(
                    QueryHistory.created_at.desc()
                ).limit(limit).offset(offset).all()
                
                return [
                    QueryHistoryModel(
                        id=record.id,
                        user_query=record.user_query,
                        generated_sql=record.generated_sql,
                        explanation=record.explanation,
                        executed=record.executed,
                        execution_time=record.execution_time,
                        error_message=record.error_message,
                        created_at=record.created_at,
                        updated_at=record.updated_at,
                        conversation_id=record.conversation_id,
                        references_query_id=record.references_query_id,
                        resolved_query=record.resolved_query,
                        entity_references=record.entity_references or {},
                        parameters=record.parameters or {},
                        is_favorite=record.is_favorite or False,
                        is_template=record.is_template or False,
                        template_name=record.template_name,
                        template_description=record.template_description,
                        template_tags=record.template_tags or []
                    ) for record in records
                ]
        except Exception as e:
            logger.error(f"從資料庫獲取查詢歷史失敗: {e}")
            # 失敗時改用文件讀取
            return self._get_history_from_file(limit, offset)
    
    def _get_history_from_file(self, limit: int, offset: int) -> List[QueryHistoryModel]:
        """從 JSON 文件獲取查詢歷史"""
        try:
            if not os.path.exists(self.history_file):
                return []
            
            with open(self.history_file, "r", encoding="utf-8") as f:
                history = json.load(f)
            
            # 排序、分頁
            sorted_history = sorted(history, key=lambda x: x.get("created_at", ""), reverse=True)
            paged_history = sorted_history[offset:offset + limit]
            
            # 轉換為 Pydantic 模型
            return [
                QueryHistoryModel(
                    id=record.get("id"),
                    user_query=record.get("user_query"),
                    generated_sql=record.get("generated_sql"),
                    explanation=record.get("explanation"),
                    executed=record.get("executed", False),
                    execution_time=record.get("execution_time"),
                    error_message=record.get("error_message"),
                    created_at=record.get("created_at"),
                    conversation_id=record.get("conversation_id"),
                    references_query_id=record.get("references_query_id"),
                    resolved_query=record.get("resolved_query"),
                    entity_references=record.get("entity_references", {}),
                    parameters=record.get("parameters", {}),
                    is_favorite=record.get("is_favorite", False),
                    is_template=record.get("is_template", False),
                    template_name=record.get("template_name"),
                    template_description=record.get("template_description"),
                    template_tags=record.get("template_tags", [])
                ) for record in paged_history
            ]
        except Exception as e:
            logger.error(f"從文件獲取查詢歷史失敗: {e}")
            return []