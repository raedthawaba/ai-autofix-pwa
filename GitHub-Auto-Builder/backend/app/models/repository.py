"""
نموذج المستودع
"""
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, JSON, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from . import Base


class Repository(Base):
    """نموذج المستودع"""
    
    __tablename__ = "repositories"
    
    id = Column(Integer, primary_key=True, index=True)
    owner = Column(String(255), index=True, nullable=False)
    name = Column(String(255), index=True, nullable=False)
    github_repo_id = Column(Integer, unique=True, index=True, nullable=False)
    full_name = Column(String(511), unique=True, index=True, nullable=False)
    
    # إعدادات المستودع
    auto_fix_enabled = Column(Boolean, default=False)
    auto_fix_safe_only = Column(Boolean, default=True)  # فقط الإصلاحات الآمنة
    auto_merge_enabled = Column(Boolean, default=False)
    primary_branch = Column(String(255), default="main")
    
    # روابط وإعدادات
    webhook_secret = Column(Text)
    settings_json = Column(Text)  # JSON string للمعلومات الإضافية
    
    # معلومات إضافية
    description = Column(Text)
    default_language = Column(String(100))
    is_private = Column(Boolean, default=False)
    
    # تواريخ
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    last_build_at = Column(DateTime)
    
    # العلاقات
    builds = relationship("Build", back_populates="repository")
    integrations = relationship("Integration", back_populates="repository")
    
    def __repr__(self):
        return f"<Repository(id={self.id}, full_name='{self.full_name}')>"
    
    @property
    def github_url(self) -> str:
        """رابط GitHub للمستودع"""
        return f"https://github.com/{self.full_name}"
    
    @property
    def settings(self) -> dict:
        """إعدادات المستودع كمكتبة"""
        if self.settings_json:
            import json
            try:
                return json.loads(self.settings_json)
            except json.JSONDecodeError:
                return {}
        return {}
    
    def update_settings(self, new_settings: dict):
        """تحديث الإعدادات"""
        import json
        self.settings_json = json.dumps(new_settings)
