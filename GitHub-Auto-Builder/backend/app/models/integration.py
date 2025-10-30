"""
نموذج التكامل مع منصات CI
"""
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, JSON, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from . import Base


class Integration(Base):
    """نموذج التكامل مع منصات CI"""
    
    __tablename__ = "integrations"
    
    # أنواع المنصات المدعومة
    PLATFORM_CHOICES = [
        ("github_actions", "GitHub Actions"),
        ("codemagic", "Codemagic"),
        ("circleci", "CircleCI"),
        ("bitrise", "Bitrise"),
        ("gitlab_ci", "GitLab CI"),
        ("azure_devops", "Azure DevOps"),
        ("travis_ci", "Travis CI"),
    ]
    
    id = Column(Integer, primary_key=True, index=True)
    repository_id = Column(Integer, ForeignKey("repositories.id"), nullable=False)
    platform = Column(String(50), nullable=False, index=True)
    
    # إعدادات التكامل
    config_json = Column(Text)  # JSON string للإعدادات
    token_encrypted = Column(Text)  # التوكن المشفر
    
    # معلومات الحالة
    is_active = Column(Boolean, default=True)
    last_used_at = Column(DateTime)
    
    # معلومات إضافية
    webhook_url = Column(Text)
    settings = Column(JSON)  # JSON للحالات الإضافية
    
    # تواريخ
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # العلاقات
    repository = relationship("Repository", back_populates="integrations")
    builds = relationship("Build", back_populates="integration")
    
    def __repr__(self):
        return f"<Integration(id={self.id}, platform='{self.platform}', repo='{self.repository.full_name}')>"
    
    @property
    def config(self) -> dict:
        """إعدادات التكامل كمكتبة"""
        if self.config_json:
            import json
            try:
                return json.loads(self.config_json)
            except json.JSONDecodeError:
                return {}
        return {}
    
    @property
    def display_name(self) -> str:
        """الاسم المعروض للتكامل"""
        platform_names = dict(self.PLATFORM_CHOICES)
        return platform_names.get(self.platform, self.platform.title())
    
    def update_config(self, new_config: dict):
        """تحديث الإعدادات"""
        import json
        self.config_json = json.dumps(new_config)
    
    @staticmethod
    def get_supported_platforms() -> list:
        """الحصول على قائمة المنصات المدعومة"""
        return [choice[0] for choice in Integration.PLATFORM_CHOICES]
    
    @staticmethod
    def get_platform_display_name(platform: str) -> str:
        """الحصول على الاسم المعروض للمنصة"""
        platform_names = dict(Integration.PLATFORM_CHOICES)
        return platform_names.get(platform, platform.title())
