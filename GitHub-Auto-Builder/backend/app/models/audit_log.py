"""
نموذج سجل المراجعة لتتبع جميع العمليات
"""
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, JSON, ForeignKey
from sqlalchemy.sql import func
from . import Base


class AuditLog(Base):
    """نموذج سجل المراجعة"""
    
    __tablename__ = "audit_logs"
    
    # أنواع العمليات
    ACTION_CHOICES = [
        ("user_login", "تسجيل دخول المستخدم"),
        ("repository_linked", "ربط مستودع"),
        ("repository_updated", "تحديث المستودع"),
        ("build_triggered", "تشغيل بناء"),
        ("build_completed", "انتهاء بناء"),
        ("fix_attempted", "محاولة إصلاح"),
        ("fix_applied", "تطبيق إصلاح"),
        ("fix_reverted", "تراجع إصلاح"),
        ("pr_created", "إنشاء PR"),
        ("pr_merged", "دمج PR"),
        ("settings_updated", "تحديث الإعدادات"),
        ("integration_added", "إضافة تكامل"),
        ("integration_updated", "تحديث تكامل"),
        ("user_action", "إجراء مستخدم"),
        ("system_action", "إجراء نظام"),
        ("error_occurred", "حدث خطأ"),
    ]
    
    id = Column(Integer, primary_key=True, index=True)
    
    # معلومات العملية
    actor_type = Column(String(20), nullable=False)  # user, system, integration
    actor_id = Column(Integer)  # معرف الفاعل (اختياري)
    actor_name = Column(String(255))  # اسم الفاعل
    
    # تفاصيل العملية
    action = Column(String(50), nullable=False, index=True)
    resource_type = Column(String(50))  # repository, build, fix_attempt, etc.
    resource_id = Column(Integer)  # معرف المورد
    resource_name = Column(String(255))  # اسم المورد
    
    # التفاصيل والبيانات
    details_json = Column(Text)  # JSON للتفاصيل الإضافية
    description = Column(Text)  # وصف مختصر للعملية
    ip_address = Column(String(45))  # عنوان IP
    user_agent = Column(Text)  # معلومات المتصفح
    
    # النتائج
    success = Column(Boolean, default=True)
    error_message = Column(Text)  # رسالة الخطأ في حالة الفشل
    
    # معلومات إضافية
    metadata = Column(JSON)
    
    # الطوابع الزمنية
    timestamp = Column(DateTime, server_default=func.now(), index=True)
    
    def __repr__(self):
        return f"<AuditLog(id={self.id}, action='{self.action}', actor='{self.actor_name}')>"
    
    @property
    def action_display(self) -> str:
        """العملية منسقة للعرض"""
        action_names = dict(self.ACTION_CHOICES)
        return action_names.get(self.action, self.action.title())
    
    @property
    def details(self) -> dict:
        """تفاصيل العملية كمكتبة"""
        if self.details_json:
            try:
                import json
                return json.loads(self.details_json)
            except json.JSONDecodeError:
                return {}
        return {}
    
    def set_details(self, details: dict):
        """تعيين تفاصيل العملية"""
        import json
        self.details_json = json.dumps(details)
    
    def record_action(
        self,
        actor_type: str,
        action: str,
        description: str = "",
        resource_type: str = None,
        resource_id: int = None,
        resource_name: str = None,
        details: dict = None,
        success: bool = True,
        error_message: str = None,
        ip_address: str = None,
        user_agent: str = None,
        metadata: dict = None
    ):
        """تسجيل عملية جديدة"""
        self.actor_type = actor_type
        self.action = action
        self.description = description
        self.resource_type = resource_type
        self.resource_id = resource_id
        self.resource_name = resource_name
        self.success = success
        self.error_message = error_message
        self.ip_address = ip_address
        self.user_agent = user_agent
        
        if details:
            self.set_details(details)
        
        if metadata:
            self.metadata = metadata
    
    @classmethod
    def log_user_action(
        cls,
        actor_id: int,
        actor_name: str,
        action: str,
        description: str = "",
        resource_type: str = None,
        resource_id: int = None,
        resource_name: str = None,
        details: dict = None,
        ip_address: str = None,
        user_agent: str = None
    ):
        """تسجيل عملية مستخدم"""
        return cls(
            actor_type="user",
            actor_id=actor_id,
            actor_name=actor_name,
            action=action,
            description=description,
            resource_type=resource_type,
            resource_id=resource_id,
            resource_name=resource_name,
            details=details,
            ip_address=ip_address,
            user_agent=user_agent
        )
    
    @classmethod
    def log_system_action(
        cls,
        action: str,
        description: str = "",
        resource_type: str = None,
        resource_id: int = None,
        resource_name: str = None,
        details: dict = None,
        success: bool = True,
        error_message: str = None
    ):
        """تسجيل عملية نظام"""
        return cls(
            actor_type="system",
            action=action,
            description=description,
            resource_type=resource_type,
            resource_id=resource_id,
            resource_name=resource_name,
            details=details,
            success=success,
            error_message=error_message
        )
