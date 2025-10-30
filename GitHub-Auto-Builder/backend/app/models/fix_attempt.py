"""
نموذج محاولات الإصلاح التلقائي
"""
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, JSON, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from . import Base


class FixAttempt(Base):
    """نموذج محاولات الإصلاح التلقائي"""
    
    __tablename__ = "fix_attempts"
    
    # أنواع الإصلاحات
    FIX_TYPE_CHOICES = [
        ("dependency_update", "تحديث التبعية"),
        ("config_fix", "إصلاح الإعدادات"),
        ("code_formatting", "تنسيق الكود"),
        ("syntax_fix", "إصلاح النحو"),
        ("missing_file", "إضافة ملف مفقود"),
        ("environment_fix", "إصلاح البيئة"),
        ("permission_fix", "إصلاح الأذونات"),
        ("llm_suggestion", "اقتراح ذكي"),
    ]
    
    # حالات المحاولة
    STATUS_CHOICES = [
        ("pending", "في الانتظار"),
        ("applied", "تم التطبيق"),
        ("failed", "فشل"),
        ("reverted", "تم التراجع"),
        ("cancelled", "ملغي"),
    ]
    
    id = Column(Integer, primary_key=True, index=True)
    build_id = Column(Integer, ForeignKey("builds.id"), nullable=False)
    
    # معلومات المحاولة
    attempt_number = Column(Integer, nullable=False, default=1)
    fix_type = Column(String(50), nullable=False, index=True)
    status = Column(String(20), default="pending", index=True)
    
    # التحليل والأخطاء
    error_pattern = Column(Text)  # نمط الخطأ المكتشف
    error_message = Column(Text)  # رسالة الخطأ
    analysis_result = Column(JSON)  # نتيجة التحليل
    fix_suggestion = Column(Text)  # اقتراح الإصلاح
    
    # التغييرات المطبقة
    files_changed = Column(JSON)  # قائمة الملفات المعدلة
    changes_summary = Column(Text)  # ملخص التغييرات
    diff_content = Column(Text)  # محتوى الـ diff
    
    # GitHub Integration
    branch_name = Column(String(255))
    commit_sha = Column(String(40))
    pull_request_url = Column(Text)
    pull_request_number = Column(Integer)
    
    # التقييم والنتائج
    confidence_score = Column(Integer)  # درجة الثقة (0-100)
    requires_approval = Column(Boolean, default=False)  # يتطلب موافقة
    was_successful = Column(Boolean, default=False)  # نجح الإصلاح
    
    # معلومات إضافية
    metadata = Column(JSON)
    notes = Column(Text)  # ملاحظات إضافية
    
    # تواريخ
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    applied_at = Column(DateTime)
    reverted_at = Column(DateTime)
    
    # العلاقات
    build = relationship("Build", back_populates="fix_attempts")
    
    def __repr__(self):
        return f"<FixAttempt(id={self.id}, build_id={self.build_id}, type='{self.fix_type}', status='{self.status}')>"
    
    @property
    def fix_type_display(self) -> str:
        """نوع الإصلاح منسق للعرض"""
        type_names = dict(self.FIX_TYPE_CHOICES)
        return type_names.get(self.fix_type, self.fix_type.title())
    
    @property
    def status_display(self) -> str:
        """الحالة منسقة للعرض"""
        status_names = dict(self.STATUS_CHOICES)
        return status_names.get(self.status, self.status.title())
    
    @property
    def is_applied(self) -> bool:
        """التحقق من تطبيق الإصلاح"""
        return self.status == "applied"
    
    @property
    def is_failed(self) -> bool:
        """التحقق من فشل الإصلاح"""
        return self.status == "failed"
    
    @property
    def confidence_level(self) -> str:
        """مستوى الثقة منسق"""
        if self.confidence_score >= 80:
            return "عالي"
        elif self.confidence_score >= 60:
            return "متوسط"
        elif self.confidence_score >= 40:
            return "منخفض"
        else:
            return "ضعيف جداً"
    
    def get_changed_files_list(self) -> list:
        """الحصول على قائمة الملفات المعدلة"""
        if not self.files_changed:
            return []
        
        if isinstance(self.files_changed, str):
            try:
                import json
                return json.loads(self.files_changed)
            except (json.JSONDecodeError, TypeError):
                return []
        
        return self.files_changed if isinstance(self.files_changed, list) else []
    
    def mark_as_applied(self):
        """تطبيق الإصلاح"""
        self.status = "applied"
        self.applied_at = func.now()
    
    def mark_as_failed(self, reason: str = ""):
        """فشل الإصلاح"""
        self.status = "failed"
        if reason:
            if self.notes:
                self.notes += f"\nسبب الفشل: {reason}"
            else:
                self.notes = f"سبب الفشل: {reason}"
    
    def mark_as_reverted(self):
        """التراجع عن الإصلاح"""
        self.status = "reverted"
        self.reverted_at = func.now()
