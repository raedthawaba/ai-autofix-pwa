"""
إعدادات التطبيق - تحميل وإدارة جميع متغيرات البيئة
"""
from typing import Optional, List
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """إعدادات التطبيق الأساسية"""
    
    # Database
    database_url: str = Field(default="postgresql://builder:password@localhost:5432/github_builder")
    
    # Redis
    redis_url: str = Field(default="redis://localhost:6379/0")
    
    # Security
    secret_key: str = Field(default="change-me-in-production")
    algorithm: str = Field(default="HS256")
    access_token_expire_minutes: int = Field(default=30)
    
    # GitHub Integration
    github_app_id: Optional[int] = Field(default=None)
    github_private_key_path: Optional[str] = Field(default=None)
    github_client_secret: Optional[str] = Field(default=None)
    github_webhook_secret: str = Field(default="github-webhook-secret")
    
    # OpenAI Integration
    openai_api_key: Optional[str] = Field(default=None)
    
    # CI Platform Tokens
    codemagic_api_token: Optional[str] = Field(default=None)
    circleci_token: Optional[str] = Field(default=None)
    bitrise_token: Optional[str] = Field(default=None)
    
    # Email Notifications
    smtp_host: str = Field(default="localhost")
    smtp_port: int = Field(default=587)
    smtp_user: Optional[str] = Field(default=None)
    smtp_password: Optional[str] = Field(default=None)
    
    # Slack Integration
    slack_webhook_url: Optional[str] = Field(default=None)
    
    # Rate Limiting
    rate_limit_requests_per_hour: int = Field(default=100)
    rate_limit_requests_per_day: int = Field(default=1000)
    
    # Auto-Fix Settings
    auto_fix_max_attempts: int = Field(default=3)
    auto_fix_safe_types: List[str] = Field(
        default=["requirements.txt", "package.json", "pipfile", "composer.json", "Cargo.toml"]
    )
    auto_fix_primary_branch: str = Field(default="main")
    
    # Logging
    log_level: str = Field(default="INFO")
    log_retention_days: int = Field(default=30)
    
    # Development
    env: str = Field(default="development")
    debug: bool = Field(default=True)
    
    # API Settings
    api_host: str = Field(default="0.0.0.0")
    api_port: int = Field(default=8000)
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# إنشاء instance عام للإعدادات
settings = Settings()


# Validation functions
def validate_database_url() -> bool:
    """التحقق من صحة رابط قاعدة البيانات"""
    return settings.database_url.startswith("postgresql://")


def validate_github_config() -> bool:
    """التحقق من صحة إعدادات GitHub"""
    if not settings.github_app_id:
        return False
    if not settings.github_private_key_path:
        return False
    return True


def get_allowed_file_types() -> List[str]:
    """الحصول على أنواع الملفات المسموحة للإصلاح التلقائي"""
    return settings.auto_fix_safe_types


def is_production() -> bool:
    """التحقق من بيئة الإنتاج"""
    return settings.env.lower() == "production"


def get_security_headers() -> dict:
    """الحصول على headers الأمان الأساسية"""
    return {
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
        "X-XSS-Protection": "1; mode=block",
        "Strict-Transport-Security": "max-age=31536000; includeSubDomains"
    }
