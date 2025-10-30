"""
نموذج المستخدم
"""
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text
from sqlalchemy.sql import func
from . import Base


class User(Base):
    """نموذج المستخدم"""
    
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    github_id = Column(Integer, unique=True, index=True, nullable=False)
    username = Column(String(255), index=True, nullable=False)
    name = Column(String(255))
    email = Column(String(255), index=True)
    avatar_url = Column(Text)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}')>"
    
    @property
    def display_name(self) -> str:
        """الاسم المعروض للمستخدم"""
        return self.name or self.username
