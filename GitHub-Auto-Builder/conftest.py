"""
إعدادات Pytest
"""
import pytest
import sys
import os

# إضافة مسار المشروع إلى Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.models.database import Base, get_db

# إعداد قاعدة بيانات الاختبار
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="session")
def setup_database():
    """إعداد قاعدة بيانات الاختبار"""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db_session(setup_database):
    """session قاعدة بيانات للاختبار"""
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    
    yield session
    
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def client(db_session):
    """عميل الاختبار مع override قاعدة البيانات"""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def sample_repository_data():
    """بيانات مستودع عينة للاختبار"""
    return {
        "owner": "testuser",
        "name": "testrepo",
        "github_repo_id": 12345,
        "description": "مستودع اختبار",
        "auto_fix_enabled": True,
        "auto_fix_safe_only": True,
        "auto_merge_enabled": False
    }


@pytest.fixture
def sample_build_data():
    """بيانات بناء عينة للاختبار"""
    return {
        "branch": "main",
        "trigger_type": "push",
        "status": "pending"
    }


@pytest.fixture
def sample_integration_data():
    """بيانات تكامل عينة للاختبار"""
    return {
        "platform": "github_actions",
        "is_active": True,
        "config": {
            "workflow_file": ".github/workflows/build.yml"
        }
    }


@pytest.fixture
def sample_webhook_data():
    """بيانات webhook عينة للاختبار"""
    return {
        "action": "opened",
        "repository": {
            "full_name": "testuser/testrepo",
            "name": "testrepo",
            "owner": {
                "login": "testuser"
            }
        },
        "sender": {
            "login": "testuser",
            "id": 12345,
            "avatar_url": "https://github.com/images/error/testuser_happy.gif"
        }
    }


# معلومات إضافية للاختبار
TEST_CONFIG = {
    "test_user": {
        "username": "testuser",
        "email": "test@example.com",
        "github_id": 12345
    },
    "test_repo": {
        "owner": "testuser",
        "name": "testrepo",
        "github_repo_id": 12345,
        "full_name": "testuser/testrepo"
    },
    "test_integration": {
        "platform": "github_actions",
        "is_active": True
    }
}
