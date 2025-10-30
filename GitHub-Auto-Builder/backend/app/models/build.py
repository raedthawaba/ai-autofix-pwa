"""
نموذج عمليات البناء
"""
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, JSON, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from . import Base


class Build(Base):
    """نموذج عمليات البناء"""
    
    __tablename__ = "builds"
    
    # حالات البناء
    STATUS_CHOICES = [
        ("pending", "في الانتظار"),
        ("running", "قيد التشغيل"),
        ("success", "نجح"),
        ("failed", "فشل"),
        ("cancelled", "ملغي"),
        ("timeout", "انتهت المهلة"),
    ]
    
    id = Column(Integer, primary_key=True, index=True)
    repository_id = Column(Integer, ForeignKey("repositories.id"), nullable=False)
    integration_id = Column(Integer, ForeignKey("integrations.id"), nullable=False)
    
    # معلومات البناء
    branch = Column(String(255), index=True, nullable=False)
    commit_sha = Column(String(40), index=True)
    build_id_platform = Column(String(255), index=True)  # ID في منصة CI
    
    # معلومات GitHub
    pull_request_id = Column(Integer)  # رقم PR إذا كان من PR
    trigger_type = Column(String(50))  # push, pull_request, manual, etc.
    
    # حالة البناء
    status = Column(String(20), default="pending", index=True)
    started_at = Column(DateTime)
    finished_at = Column(DateTime)
    duration_seconds = Column(Integer)
    
    # اللوجات والنتائج
    logs_url = Column(Text)
    logs_content = Column(Text)
    error_logs = Column(Text)
    
    # النتائج والإحصائيات
    test_results = Column(JSON)  # نتائج الاختبارات
    coverage_percentage = Column(Integer)
    artifacts_url = Column(Text)
    
    # معلومات إضافية
    build_data = Column(JSON)  # بيانات إضافية
    metadata = Column(JSON)
    
    # تواريخ
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # العلاقات
    repository = relationship("Repository", back_populates="builds")
    integration = relationship("Integration", back_populates="builds")
    fix_attempts = relationship("FixAttempt", back_populates="build")
    
    def __repr__(self):
        return f"<Build(id={self.id}, repo='{self.repository.full_name}', status='{self.status}')>"
    
    @property
    def is_success(self) -> bool:
        """التحقق من نجاح البناء"""
        return self.status == "success"
    
    @property
    def is_failed(self) -> bool:
        """التحقق من فشل البناء"""
        return self.status == "failed"
    
    @property
    def duration_formatted(self) -> str:
        """المدة منسقة"""
        if not self.duration_seconds:
            return "غير محدد"
        
        hours = self.duration_seconds // 3600
        minutes = (self.duration_seconds % 3600) // 60
        seconds = self.duration_seconds % 60
        
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        else:
            return f"{minutes:02d}:{seconds:02d}"
    
    @property
    def status_display(self) -> str:
        """الحالة منسقة للعرض"""
        status_names = dict(self.STATUS_CHOICES)
        return status_names.get(self.status, self.status.title())
    
    def calculate_duration(self):
        """حساب مدة البناء"""
        if self.started_at and self.finished_at:
            delta = self.finished_at - self.started_at
            self.duration_seconds = int(delta.total_seconds())
    
    def get_logs_summary(self, max_length: int = 1000) -> str:
        """الحصول على ملخص اللوجات"""
        if not self.logs_content:
            return ""
        
        # إزالة الأسطر الطويلة جداً
        lines = self.logs_content.split('\n')
        summary_lines = []
        current_length = 0
        
        for line in lines:
            if current_length + len(line) > max_length:
                summary_lines.append(f"... [تم اقتطاع اللوجات]")
                break
            summary_lines.append(line)
            current_length += len(line)
        
        return '\n'.join(summary_lines)
