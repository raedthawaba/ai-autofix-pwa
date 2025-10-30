"""
اختبارات أساسية للتطبيق
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.models.database import Base, get_db
from app.config import settings

# إعداد قاعدة بيانات الاختبار
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture
def db():
    """إنشاء قاعدة بيانات اختبار"""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client():
    """عميل الاختبار"""
    def override_get_db():
        try:
            db = TestingSessionLocal()
            yield db
        finally:
            db.close()
    
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def test_read_root(client):
    """اختبار الصفحة الرئيسية"""
    response = client.get("/")
    assert response.status_code == 200
    assert "GitHub Auto Builder API" in response.json()["message"]


def test_health_check(client):
    """اختبار فحص الصحة"""
    response = client.get("/api/health/")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "components" in data


def test_api_info(client):
    """اختبار معلومات API"""
    response = client.get("/api")
    assert response.status_code == 200
    data = response.json()
    assert "name" in data
    assert "endpoints" in data


def test_create_repository(client):
    """اختبار إنشاء مستودع"""
    repo_data = {
        "owner": "testuser",
        "name": "testrepo",
        "github_repo_id": 12345,
        "auto_fix_enabled": True
    }
    
    response = client.post("/api/repositories/", json=repo_data)
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert data["repository"]["full_name"] == "testuser/testrepo"


def test_list_repositories(client):
    """اختبار قائمة المستودعات"""
    response = client.get("/api/repositories/")
    assert response.status_code == 200
    data = response.json()
    assert "repositories" in data
    assert "pagination" in data


def test_github_webhook(client):
    """اختبار webhook GitHub"""
    webhook_data = {
        "action": "opened",
        "repository": {
            "full_name": "testuser/testrepo"
        },
        "sender": {
            "login": "testuser"
        }
    }
    
    response = client.post(
        "/api/webhooks/github",
        json=webhook_data,
        headers={"X-GitHub-Event": "pull_request"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert data["status"] == "received"


def test_build_statistics(client):
    """اختبار إحصائيات البناء"""
    response = client.get("/api/builds/statistics/summary")
    assert response.status_code == 200
    data = response.json()
    assert "totals" in data
    assert "rates" in data


def test_supported_platforms(client):
    """اختبار المنصات المدعومة"""
    response = client.get("/api/integrations/platforms/supported")
    assert response.status_code == 200
    data = response.json()
    assert "supported_platforms" in data


def test_create_integration(client):
    """اختبار إنشاء تكامل"""
    # أولاً إنشاء مستودع
    repo_data = {
        "owner": "testuser", 
        "name": "testrepo",
        "github_repo_id": 12345
    }
    repo_response = client.post("/api/repositories/", json=repo_data)
    repo_id = repo_response.json()["repository"]["id"]
    
    # إنشاء تكامل
    integration_data = {
        "repository_id": repo_id,
        "platform": "github_actions",
        "is_active": True
    }
    
    response = client.post("/api/integrations/", json=integration_data)
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert data["integration"]["platform"] == "github_actions"
