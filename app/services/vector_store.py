import numpy as np
import faiss
import os
import joblib
from typing import List, Dict, Any, Optional, Tuple, Union
from pydantic import BaseModel, Field
from datetime import datetime
import logging
from uuid import UUID, uuid4
from sentence_transformers import SentenceTransformer
from ..utils import settings

# 設定日誌
logger = logging.getLogger(__name__)

# 向量嵌入模型設定
DEFAULT_EMBEDDING_MODEL = "paraphrase-multilingual-MiniLM-L12-v2"  # 支持多語言，適合中文
VECTOR_DIMENSION = 384  # 上述模型的嵌入維度

# 向量存儲目錄
VECTOR_STORE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../vector_store"))
os.makedirs(VECTOR_STORE_DIR, exist_ok=True)

# 索引文件路徑
INDEX_FILE = os.path.join(VECTOR_STORE_DIR, "query_index.faiss")
METADATA_FILE = os.path.join(VECTOR_STORE_DIR, "query_metadata.joblib")


class QueryEmbedding(BaseModel):
    """查詢嵌入模型"""
    id: str = Field(default_factory=lambda: str(uuid4()))
    query: str
    sql: str
    embedding: List[float] = None  # 嵌入向量
    metadata: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.now)
    
    class Config:
        arbitrary_types_allowed = True


class VectorStore:
    """向量存儲服務"""
    
    def __init__(self, embedding_model: str = DEFAULT_EMBEDDING_MODEL):
        """
        初始化向量存儲服務
        
        Args:
            embedding_model: 嵌入模型名稱
        """
        self.embedding_model_name = embedding_model
        
        # 初始化嵌入模型
        try:
            logger.info(f"加載文本嵌入模型: {embedding_model}")
            self.embedding_model = SentenceTransformer(embedding_model)
        except Exception as e:
            logger.error(f"加載嵌入模型失敗: {e}")
            raise
        
        # 初始化或加載向量索引
        if os.path.exists(INDEX_FILE) and os.path.exists(METADATA_FILE):
            self.load_index()
        else:
            self.initialize_index()
        
        logger.info(f"向量存儲服務初始化完成，當前包含 {self.get_count()} 個查詢")
    
    def initialize_index(self):
        """初始化新的索引"""
        # 創建 FAISS 索引
        self.index = faiss.IndexFlatL2(VECTOR_DIMENSION)
        
        # 初始化元數據存儲
        self.metadata = []
        
        # 保存索引
        self.save_index()
    
    def load_index(self):
        """加載現有索引"""
        try:
            # 加載 FAISS 索引
            self.index = faiss.read_index(INDEX_FILE)
            
            # 加載元數據
            self.metadata = joblib.load(METADATA_FILE)
            
            logger.info(f"成功加載索引和元數據: {self.get_count()} 個項目")
        except Exception as e:
            logger.error(f"加載索引失敗: {e}")
            self.initialize_index()
    
    def save_index(self):
        """保存索引和元數據"""
        try:
            # 保存 FAISS 索引
            faiss.write_index(self.index, INDEX_FILE)
            
            # 保存元數據
            joblib.dump(self.metadata, METADATA_FILE)
            
            logger.info(f"成功保存索引和元數據: {self.get_count()} 個項目")
        except Exception as e:
            logger.error(f"保存索引失敗: {e}")
            raise
    
    def get_embedding(self, text: str) -> np.ndarray:
        """
        獲取文本的嵌入向量
        
        Args:
            text: 要嵌入的文本
            
        Returns:
            嵌入向量
        """
        try:
            # 使用 SentenceTransformer 模型獲取嵌入
            embedding = self.embedding_model.encode(text)
            return embedding
        except Exception as e:
            logger.error(f"獲取嵌入向量失敗: {e}")
            raise
    
    def add_query(self, query: str, sql: str, metadata: Dict[str, Any] = None) -> str:
        """
        添加查詢嵌入到索引
        
        Args:
            query: 自然語言查詢
            sql: 生成的 SQL 查詢
            metadata: 額外的元數據
            
        Returns:
            嵌入 ID
        """
        # 生成唯一 ID
        embedding_id = str(uuid4())
        
        # 獲取嵌入向量
        embedding = self.get_embedding(query)
        
        # 添加到 FAISS 索引
        self.index.add(np.array([embedding], dtype=np.float32))
        
        # 創建元數據
        metadata_entry = {
            "id": embedding_id,
            "query": query,
            "sql": sql,
            "timestamp": datetime.now(),
            "metadata": metadata or {}
        }
        
        # 添加到元數據存儲
        self.metadata.append(metadata_entry)
        
        # 保存索引
        self.save_index()
        
        logger.info(f"添加查詢嵌入: {embedding_id}")
        return embedding_id
    
    def search_similar(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        """
        搜索與給定查詢相似的查詢
        
        Args:
            query: 要搜索的查詢
            k: 返回的最相似項目數量
            
        Returns:
            相似查詢列表
        """
        # 檢查索引是否為空
        if self.get_count() == 0:
            return []
        
        # 獲取查詢的嵌入向量
        query_embedding = self.get_embedding(query)
        
        # 用於搜索的向量
        search_vector = np.array([query_embedding], dtype=np.float32)
        
        # 在索引中搜索
        k = min(k, self.get_count())  # 確保 k 不超過索引中的項目數
        distances, indices = self.index.search(search_vector, k)
        
        # 構建結果
        results = []
        for i, idx in enumerate(indices[0]):
            if idx != -1:  # FAISS 可能返回 -1 表示沒有找到足夠的結果
                metadata_entry = self.metadata[idx]
                
                # 添加相似度分數 (轉換為 0-1 範圍，1 表示完全相似)
                similarity = max(0, 1 - distances[0][i] / 10)  # 根據 L2 距離轉換
                
                # 構建結果項
                result = {
                    "id": metadata_entry["id"],
                    "query": metadata_entry["query"],
                    "sql": metadata_entry["sql"],
                    "timestamp": metadata_entry["timestamp"],
                    "similarity": similarity,
                    "metadata": metadata_entry.get("metadata", {})
                }
                
                results.append(result)
        
        return results
    
    def get_count(self) -> int:
        """獲取索引中的項目數量"""
        return self.index.ntotal
    
    def clear(self):
        """清除所有索引數據"""
        self.initialize_index()
        logger.info("已清除所有向量索引數據")


# 創建全局向量存儲實例
vector_store = VectorStore()