from typing import List, Dict, Any, Optional, Tuple
import time
import logging
from sqlalchemy import create_engine, text, exc
from ..utils import settings
import json
import re
from typing import Tuple

# 設定日誌
logger = logging.getLogger(__name__)


class QueryResult:
    """SQL 查詢結果"""
    
    def __init__(self, columns: List[str], rows: List[List[Any]], row_count: int, execution_time: float, error: Optional[str] = None):
        self.columns = columns
        self.rows = rows
        self.row_count = row_count
        self.execution_time = execution_time
        self.error = error
    
    def to_dict(self) -> Dict[str, Any]:
        """將查詢結果轉換為字典"""
        return {
            "columns": self.columns,
            "rows": self.rows,
            "row_count": self.row_count,
            "execution_time": self.execution_time,
            "error": self.error
        }
    
    def to_json(self) -> str:
        """將查詢結果轉換為 JSON 字符串"""
        return json.dumps(self.to_dict(), ensure_ascii=False, default=str)
    
    @classmethod
    def from_error(cls, error: str) -> 'QueryResult':
        """從錯誤創建查詢結果"""
        return cls(columns=[], rows=[], row_count=0, execution_time=0, error=error)


class DatabaseService:
    """數據庫服務"""
    
    def __init__(self):
        """初始化數據庫服務"""
        self.connected = False
        self.engine = None
        
        try:
            self.engine = create_engine(settings.database_url)
            # 測試連接
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            self.connected = True
            logger.info("數據庫連接成功")
        except Exception as e:
            logger.error(f"數據庫連接失敗: {e}")
    
    def is_connected(self) -> bool:
        """檢查是否連接到數據庫"""
        return self.connected
    
    def is_safe_query(self, sql: str) -> Tuple[bool, str]:
        """
        檢查 SQL 查詢是否安全（只讀查詢）
        
        Args:
            sql: SQL 查詢
            
        Returns:
            是否安全，以及不安全的原因（如果不安全）
        """
        # 移除註釋
        sql = re.sub(r'--.*?(\n|$)', ' ', sql)
        sql = re.sub(r'/\*.*?\*/', ' ', sql, flags=re.DOTALL)
        sql = sql.strip()
        
        # 檢查 SQL 是否為只讀查詢
        dangerous_keywords = [
            r'\bINSERT\b', r'\bUPDATE\b', r'\bDELETE\b', r'\bDROP\b', 
            r'\bCREATE\b', r'\bALTER\b', r'\bTRUNCATE\b', r'\bRENAME\b', 
            r'\bGRANT\b', r'\bREVOKE\b'
        ]
        
        for keyword in dangerous_keywords:
            if re.search(keyword, sql, re.IGNORECASE):
                return False, f"不允許執行包含 '{re.search(keyword, sql, re.IGNORECASE).group(0)}' 的查詢"
        
        return True, ""
    
    def execute_query(self, sql: str, params: Optional[Dict[str, Any]] = None) -> QueryResult:
        """
        執行 SQL 查詢
        
        Args:
            sql: SQL 查詢語句
            params: 查詢參數
            
        Returns:
            查詢結果
        """
        if not self.is_connected():
            return QueryResult.from_error("未連接到數據庫")
        
        # 檢查查詢安全性
        is_safe, reason = self.is_safe_query(sql)
        if not is_safe:
            return QueryResult.from_error(f"不安全的查詢: {reason}")
        
        try:
            start_time = time.time()
            
            # 檢查是否是函數調用
            is_function_call = False
            function_name = None
            
            # 簡單的函數調用檢測（更複雜的邏輯可能需要SQL解析器）
            if "FROM" in sql.upper() and "(" in sql and ")" in sql:
                # 提取 FROM 後的函數名
                from_parts = sql.upper().split("FROM")[1].strip().split()
                if from_parts and "(" in from_parts[0]:
                    function_parts = from_parts[0].split("(")[0].strip()
                    if function_parts:
                        is_function_call = True
                        function_name = function_parts.lower()
            
            with self.engine.connect() as conn:
                try:
                    # 執行查詢
                    result = conn.execute(text(sql), params or {})
                    
                    # 獲取列名
                    columns = result.keys()
                    
                    # 獲取行數據
                    rows = [list(row) for row in result.fetchall()]
                    
                    # 計算執行時間
                    execution_time = (time.time() - start_time) * 1000  # 轉換為毫秒
                    
                    return QueryResult(
                        columns=columns,
                        rows=rows,
                        row_count=len(rows),
                        execution_time=execution_time
                    )
                    
                except exc.ProgrammingError as e:
                    # 處理特定的函數不存在錯誤
                    if is_function_call and "function does not exist" in str(e).lower():
                        logger.error(f"數據庫函數不存在: {function_name}")
                        
                        # 記錄此函數錯誤，後續可以更新 db_functions 中的狀態
                        return QueryResult.from_error(
                            f"函數 '{function_name}' 不存在或未正確安裝到數據庫。請使用直接查詢替代此函數調用。"
                        )
                    else:
                        raise
                
        except exc.SQLAlchemyError as e:
            logger.error(f"SQL 查詢執行錯誤: {e}")
            return QueryResult.from_error(str(e))
        except Exception as e:
            logger.error(f"執行查詢時發生未知錯誤: {e}")
            return QueryResult.from_error(f"未知錯誤: {str(e)}")
            
    def execute_query_with_viz(self, sql: str, params: Optional[Dict[str, Any]] = None, visualize: bool = False) -> Tuple[QueryResult, Optional[Dict]]:
        """
        執行 SQL 查詢並生成視覺化
        
        Args:
            sql: SQL 查詢語句
            params: 查詢參數
            visualize: 是否生成視覺化
            
        Returns:
            (查詢結果, 視覺化元數據) 的元組
        """
        from .visualization_service import visualization_service
        
        # 執行查詢
        result = self.execute_query(sql, params)
        
        # 如果需要視覺化且查詢成功
        if visualize and not result.error and result.columns and result.rows:
            # 檢查查詢是否適合視覺化
            should_visualize = visualization_service.detect_visualization_query(sql)
            
            if should_visualize:
                # 生成查詢標題
                title = "SQL查詢結果視覺化"
                if len(sql) <= 50:
                    title = f"查詢: {sql}"
                else:
                    # 嘗試從 SELECT 和 FROM 提取主要內容
                    try:
                        select_pattern = re.search(r'SELECT\s+(.+?)\s+FROM', sql, re.IGNORECASE)
                        from_pattern = re.search(r'FROM\s+(.+?)(?:\s+WHERE|\s+GROUP|\s+ORDER|\s+LIMIT|$)', sql, re.IGNORECASE)
                        
                        if select_pattern and from_pattern:
                            select_part = select_pattern.group(1).strip()
                            from_part = from_pattern.group(1).strip()
                            if len(select_part) > 30:
                                select_part = select_part[:30] + "..."
                            title = f"查詢: {select_part} FROM {from_part}"
                    except:
                        pass
                
                # 生成視覺化
                viz_path, viz_metadata = visualization_service.create_visualization(
                    columns=result.columns,
                    rows=result.rows,
                    title=title
                )
                
                return result, viz_metadata
        
        return result, None
    
    def get_tables(self) -> List[str]:
        """獲取所有表名"""
        if not self.is_connected():
            return []
        
        try:
            with self.engine.connect() as conn:
                # PostgreSQL 特定查詢，獲取所有公共表
                result = conn.execute(text("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public'
                    ORDER BY table_name
                """))
                
                return [row[0] for row in result.fetchall()]
        except Exception as e:
            logger.error(f"獲取表名失敗: {e}")
            return []
    
    def get_table_schema(self, table_name: str) -> Dict[str, Any]:
        """
        獲取表結構
        
        Args:
            table_name: 表名
            
        Returns:
            表結構信息
        """
        if not self.is_connected():
            return {"error": "未連接到數據庫"}
        
        try:
            with self.engine.connect() as conn:
                # 獲取列信息
                columns_result = conn.execute(text("""
                    SELECT column_name, data_type, is_nullable, column_default
                    FROM information_schema.columns
                    WHERE table_schema = 'public' AND table_name = :table_name
                    ORDER BY ordinal_position
                """), {"table_name": table_name})
                
                columns = [{
                    "name": row[0],
                    "type": row[1],
                    "nullable": row[2] == "YES",
                    "default": row[3]
                } for row in columns_result.fetchall()]
                
                # 獲取主鍵信息
                pk_result = conn.execute(text("""
                    SELECT c.column_name
                    FROM information_schema.table_constraints tc
                    JOIN information_schema.constraint_column_usage AS ccu USING (constraint_schema, constraint_name)
                    JOIN information_schema.columns AS c ON c.table_schema = tc.constraint_schema
                        AND tc.table_name = c.table_name AND ccu.column_name = c.column_name
                    WHERE tc.constraint_type = 'PRIMARY KEY' AND tc.table_name = :table_name
                """), {"table_name": table_name})
                
                primary_keys = [row[0] for row in pk_result.fetchall()]
                
                # 獲取外鍵信息
                fk_result = conn.execute(text("""
                    SELECT
                        kcu.column_name,
                        ccu.table_name AS foreign_table_name,
                        ccu.column_name AS foreign_column_name
                    FROM information_schema.table_constraints AS tc
                    JOIN information_schema.key_column_usage AS kcu
                      ON tc.constraint_name = kcu.constraint_name
                      AND tc.table_schema = kcu.table_schema
                    JOIN information_schema.constraint_column_usage AS ccu
                      ON ccu.constraint_name = tc.constraint_name
                      AND ccu.table_schema = tc.table_schema
                    WHERE tc.constraint_type = 'FOREIGN KEY' AND tc.table_name = :table_name
                """), {"table_name": table_name})
                
                foreign_keys = [{
                    "column": row[0],
                    "reference_table": row[1],
                    "reference_column": row[2]
                } for row in fk_result.fetchall()]
                
                return {
                    "table_name": table_name,
                    "columns": columns,
                    "primary_keys": primary_keys,
                    "foreign_keys": foreign_keys
                }
                
        except Exception as e:
            logger.error(f"獲取表結構失敗: {e}")
            return {"error": str(e)}