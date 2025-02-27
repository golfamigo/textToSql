"""
API 集成測試的 pytest 配置
提供常用的 fixtures 和測試設置
"""
import os
import sys
import pytest
import tempfile
import shutil
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

# 添加當前目錄到模塊搜索路徑
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)
import mock_settings

# 在導入其他模塊前先模擬設置
sys.modules['app.utils.config'] = mock_settings

# 導入 API 和相關服務
from app.api import app


@pytest.fixture(scope="session")
def temp_dir():
    """創建測試使用的臨時目錄"""
    temp_path = tempfile.mkdtemp()
    yield temp_path
    shutil.rmtree(temp_path)


@pytest.fixture(scope="session")
def test_client():
    """返回測試用的 FastAPI 客戶端"""
    return TestClient(app)


@pytest.fixture(scope="function")
def mock_text_to_sql():
    """模擬 TextToSQLService"""
    with patch('app.api.text_to_sql_service') as mock:
        yield mock


@pytest.fixture(scope="function")
def mock_db_service():
    """模擬 DatabaseService"""
    with patch('app.api.db_service') as mock:
        # 設置默認連接狀態
        mock.is_connected.return_value = True
        yield mock


@pytest.fixture(scope="function")
def mock_vector_store():
    """模擬 VectorStore"""
    with patch('app.api.vector_store') as mock:
        yield mock


@pytest.fixture(scope="function")
def mock_llm_service():
    """模擬 LLMService"""
    with patch('app.api.llm_service') as mock:
        # 設置默認可用模型
        mock.get_available_models.return_value = ["dummy-model", "test-model"]
        yield mock


@pytest.fixture(scope="function")
def mock_all_services(mock_text_to_sql, mock_db_service, mock_vector_store, mock_llm_service):
    """同時模擬所有服務"""
    return {
        "text_to_sql": mock_text_to_sql,
        "db_service": mock_db_service,
        "vector_store": mock_vector_store,
        "llm_service": mock_llm_service
    }


# 整合測試標記
def pytest_configure(config):
    """添加自定義標記"""
    config.addinivalue_line(
        "markers", "integration: 標記測試為集成測試"
    )
    config.addinivalue_line(
        "markers", "e2e: 標記測試為端到端測試"
    )