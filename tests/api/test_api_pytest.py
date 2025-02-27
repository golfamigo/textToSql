"""
使用 pytest 的 API 測試
此版本使用 pytest 風格而非 unittest
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import MagicMock
import os

# 導入測試需要的類型
from app.services.text_to_sql import SQLResult
from app.models import QueryHistoryModel


def test_health_check(test_client, mock_db_service, mock_llm_service):
    """測試健康檢查端點"""
    # 設置模擬返回值
    mock_db_service.is_connected.return_value = True
    mock_llm_service.get_available_models.return_value = ["dummy-model", "test-model"]
    
    # 發送請求
    response = test_client.get("/health")
    
    # 驗證結果
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["database"] == "connected"
    assert data["models"]["default"] == "dummy-model"
    assert data["models"]["available"] == 2
    
    # 驗證調用
    mock_db_service.is_connected.assert_called_once()
    mock_llm_service.get_available_models.assert_called_once()


def test_convert_text_to_sql(test_client, mock_text_to_sql):
    """測試文本到SQL轉換端點"""
    # 準備模擬返回值
    mock_result = SQLResult(
        sql="SELECT * FROM n8n_booking_users WHERE email = :email",
        explanation="這個查詢從用戶表中查找符合指定電子郵件的用戶。",
        parameters={"email": "test@example.com"},
        query_id="test-query-id"
    )
    mock_text_to_sql.text_to_sql.return_value = mock_result
    
    # 發送請求
    request_data = {
        "query": "找到email是test@example.com的用戶",
        "execute": True,
        "model": "test-model",
        "find_similar": True
    }
    response = test_client.post("/api/text-to-sql", json=request_data)
    
    # 驗證結果
    assert response.status_code == 200
    data = response.json()
    assert data["sql"] == "SELECT * FROM n8n_booking_users WHERE email = :email"
    assert data["parameters"] == {"email": "test@example.com"}
    
    # 驗證調用
    mock_text_to_sql.text_to_sql.assert_called_once_with(
        query="找到email是test@example.com的用戶",
        execute=True,
        find_similar=True
    )


def test_convert_text_to_sql_error(test_client, mock_text_to_sql):
    """測試文本到SQL轉換錯誤處理"""
    # 模擬拋出異常
    mock_text_to_sql.text_to_sql.side_effect = Exception("測試錯誤")
    
    # 發送請求
    request_data = {
        "query": "無效查詢",
        "execute": False
    }
    response = test_client.post("/api/text-to-sql", json=request_data)
    
    # 驗證結果
    assert response.status_code == 500
    data = response.json()
    assert "detail" in data
    assert "測試錯誤" in data["detail"]


def test_get_query_history(test_client, mock_text_to_sql):
    """測試獲取查詢歷史"""
    # 準備模擬返回值
    mock_history = [
        QueryHistoryModel(
            id="hist-1",
            user_query="找到所有用戶",
            generated_sql="SELECT * FROM n8n_booking_users",
            explanation="查詢所有用戶",
            executed=True,
            created_at=datetime.now() - timedelta(days=1)
        ),
        QueryHistoryModel(
            id="hist-2",
            user_query="找到特定email的用戶",
            generated_sql="SELECT * FROM n8n_booking_users WHERE email = :email",
            explanation="查詢特定郵箱的用戶",
            executed=False,
            created_at=datetime.now()
        )
    ]
    mock_text_to_sql.get_history.return_value = mock_history
    
    # 發送請求
    response = test_client.get("/api/history?limit=10&offset=0")
    
    # 驗證結果
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["id"] == "hist-1"
    assert data[1]["id"] == "hist-2"
    
    # 驗證調用
    mock_text_to_sql.get_history.assert_called_once_with(10, 0)


def test_execute_sql(test_client, mock_text_to_sql, mock_db_service):
    """測試直接執行SQL"""
    # 準備模擬返回值
    mock_result = MagicMock()
    mock_result.error = None
    mock_result.to_dict.return_value = {
        "columns": ["id", "name", "email"],
        "rows": [[1, "測試用戶", "test@example.com"]],
        "execution_time": 0.1
    }
    mock_text_to_sql.execute_sql.return_value = mock_result
    
    # 模擬SQL安全性檢查
    mock_db_service.is_safe_query.return_value = (True, "")
    
    # 發送請求
    sql_query = "SELECT * FROM n8n_booking_users WHERE id = 1"
    response = test_client.post(f"/api/execute-sql?sql={sql_query}")
    
    # 驗證結果
    assert response.status_code == 200
    data = response.json()
    assert data["columns"] == ["id", "name", "email"]
    assert len(data["rows"]) == 1
    
    # 驗證調用
    mock_db_service.is_safe_query.assert_called_once_with(sql_query)
    mock_text_to_sql.execute_sql.assert_called_once_with(sql_query)


def test_execute_sql_unsafe(test_client, mock_db_service, mock_text_to_sql):
    """測試執行不安全的SQL"""
    # 模擬SQL安全性檢查
    mock_db_service.is_safe_query.return_value = (False, "不允許修改數據")
    
    # 發送請求
    sql_query = "DELETE FROM n8n_booking_users"
    response = test_client.post(f"/api/execute-sql?sql={sql_query}")
    
    # 驗證結果
    assert response.status_code == 400
    data = response.json()
    assert "detail" in data
    assert data["detail"] == "不允許修改數據"
    
    # 驗證未執行SQL
    mock_text_to_sql.execute_sql.assert_not_called()


def test_get_tables(test_client, mock_db_service):
    """測試獲取所有表名"""
    # 準備模擬返回值
    mock_db_service.get_tables.return_value = [
        "n8n_booking_users",
        "n8n_booking_services",
        "n8n_booking_bookings"
    ]
    
    # 發送請求
    response = test_client.get("/api/tables")
    
    # 驗證結果
    assert response.status_code == 200
    data = response.json()
    assert len(data["tables"]) == 3
    assert "n8n_booking_users" in data["tables"]
    
    # 驗證調用
    mock_db_service.get_tables.assert_called_once()


def test_get_table_schema(test_client, mock_db_service):
    """測試獲取表結構"""
    # 準備模擬返回值
    mock_schema = {
        "table_name": "n8n_booking_users",
        "columns": [
            {"name": "id", "type": "INTEGER", "nullable": False},
            {"name": "name", "type": "VARCHAR", "nullable": False},
            {"name": "email", "type": "VARCHAR", "nullable": True}
        ],
        "primary_keys": ["id"],
        "foreign_keys": []
    }
    mock_db_service.get_table_schema.return_value = mock_schema
    
    # 發送請求
    response = test_client.get("/api/table/n8n_booking_users/schema")
    
    # 驗證結果
    assert response.status_code == 200
    data = response.json()
    assert data["table_name"] == "n8n_booking_users"
    assert len(data["columns"]) == 3
    
    # 驗證調用
    mock_db_service.get_table_schema.assert_called_once_with("n8n_booking_users")


def test_vector_store_stats(test_client, mock_vector_store):
    """測試獲取向量存儲統計"""
    # 準備模擬返回值
    mock_vector_store.get_count.return_value = 15
    
    # 發送請求
    response = test_client.get("/api/vector-store/stats")
    
    # 驗證結果
    assert response.status_code == 200
    data = response.json()
    assert data["count"] == 15
    assert data["status"] == "active"
    
    # 驗證調用
    mock_vector_store.get_count.assert_called_once()


def test_search_similar_queries(test_client, mock_vector_store):
    """測試搜索相似查詢"""
    # 準備模擬返回值
    mock_results = [
        {
            "id": "query-1",
            "query": "查詢所有用戶",
            "sql": "SELECT * FROM n8n_booking_users",
            "similarity": 0.85,
            "timestamp": datetime.now().isoformat()
        },
        {
            "id": "query-2",
            "query": "查詢活躍用戶",
            "sql": "SELECT * FROM n8n_booking_users WHERE is_active = true",
            "similarity": 0.75,
            "timestamp": datetime.now().isoformat()
        }
    ]
    mock_vector_store.search_similar.return_value = mock_results
    
    # 發送請求
    response = test_client.get("/api/vector-store/search?query=查詢用戶&limit=5")
    
    # 驗證結果
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["id"] == "query-1"
    assert data[1]["id"] == "query-2"
    
    # 驗證調用
    mock_vector_store.search_similar.assert_called_once_with("查詢用戶", k=5)


# 使用整合測試標記
@pytest.mark.integration
def test_model_performance(test_client, mock_llm_service):
    """測試獲取模型性能統計"""
    # 準備模擬返回值
    mock_performance = {
        "dummy-model": {
            "total_requests": 100,
            "average_rating": 4.5,
            "latency": {
                "p50": 1.2,
                "p95": 2.3,
                "p99": 3.1
            }
        }
    }
    mock_llm_service.get_model_performance.return_value = mock_performance
    
    # 發送請求
    response = test_client.get("/api/model-performance?model_name=dummy-model")
    
    # 驗證結果
    assert response.status_code == 200
    data = response.json()
    assert data["dummy-model"]["total_requests"] == 100
    assert data["dummy-model"]["average_rating"] == 4.5
    
    # 驗證調用
    mock_llm_service.get_model_performance.assert_called_once_with("dummy-model")