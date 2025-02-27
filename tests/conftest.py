"""
測試配置文件
"""
import os
import sys
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# 添加應用路徑到系統路徑
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# 設置測試環境變數
os.environ["OPENAI_API_KEY"] = "test_key"
os.environ["ANTHROPIC_API_KEY"] = "test_key"
os.environ["GOOGLE_API_KEY"] = "test_key"
os.environ["AZURE_OPENAI_API_KEY"] = "test_key"
os.environ["AZURE_OPENAI_ENDPOINT"] = "https://test.com"
os.environ["AZURE_DEPLOYMENT_NAME"] = "test-deployment"
os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from app.services.history_service import Base, QueryHistory, QueryTemplate
from app.models.query_history import QueryHistoryModel, QueryTemplateModel
from app.services.history_service import HistoryService


@pytest.fixture
def db_engine():
    """建立一個 SQLite 內存數據庫引擎"""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    return engine


@pytest.fixture
def db_session(db_engine):
    """建立數據庫會話"""
    Session = sessionmaker(bind=db_engine)
    session = Session()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def history_service(monkeypatch, db_engine):
    """建立一個使用臨時數據庫的 HistoryService"""
    # 使用 monkeypatch 模擬設置
    monkeypatch.setattr("app.services.history_service.settings.database_url", "sqlite:///:memory:")
    
    # 創建服務實例
    service = HistoryService(use_db=True)
    
    # 替換數據庫引擎為測試引擎
    service.engine = db_engine
    service.Session = sessionmaker(bind=db_engine)
    
    return service


@pytest.fixture
def sample_query_history():
    """創建一個樣本查詢歷史記錄"""
    return QueryHistoryModel(
        user_query="列出所有活躍的商家",
        generated_sql="SELECT * FROM n8n_booking_businesses WHERE is_active = true;",
        explanation="此查詢從商家表中選擇所有活躍的商家。",
        executed=True,
        execution_time=15.7
    )


@pytest.fixture
def sample_query_template():
    """創建一個樣本查詢模板"""
    return QueryTemplateModel(
        name="活躍商家查詢",
        description="查詢所有目前活躍的商家記錄",
        user_query="列出所有活躍的商家",
        generated_sql="SELECT * FROM n8n_booking_businesses WHERE is_active = true;",
        explanation="此查詢從商家表中選擇所有活躍的商家。",
        tags=["商家", "基礎查詢"]
    )