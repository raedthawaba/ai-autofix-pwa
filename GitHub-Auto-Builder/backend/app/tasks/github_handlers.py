"""
GitHub Event Handlers - معالجة أحداث GitHub
"""
from celery import current_task
from sqlalchemy.orm import Session
from datetime import datetime

from ..models.database import SessionLocal
from ..models.repository import Repository
from ..models.build import Build
from ..models.integration import Integration
from ..config import settings
from . import celery_app


@celery_app.task(bind=True, name="app.tasks.github_handlers.process_github_event")
def process_github_event(self, event_data: dict):
    """
    معالجة أحداث GitHub الرئيسية
    """
    try:
        db = SessionLocal()
        
        event_type = event_data.get("event_type")
        repository_id = event_data.get("repository_id")
        
        # البحث عن المستودع
        repository = db.query(Repository).filter(
            Repository.id == repository_id
        ).first()
        
        if not repository:
            self.update_state(
                state="FAILURE",
                meta=f"المستودع غير موجود: {repository_id}"
            )
            return
        
        # معالجة حسب نوع الحدث
        if event_type == "push":
            process_push_event(db, repository, event_data)
        elif event_type == "pull_request":
            process_pull_request_event(db, repository, event_data)
        else:
            # معالجة عامة
            self.update_state(
                state="PROGRESS",
                meta=f"معالجة حدث {event_type}"
            )
        
        db.close()
        
        return {
            "status": "success",
            "message": f"تم معالجة حدث {event_type} بنجاح",
            "repository": repository.full_name
        }
        
    except Exception as e:
        self.update_state(
            state="FAILURE",
            meta=f"خطأ في معالجة الحدث: {str(e)}"
        )
        raise


def process_push_event(db: Session, repository: Repository, event_data: dict):
    """
    معالجة حدث push
    """
    branch = event_data.get("branch")
    commits = event_data.get("commits", [])
    
    if not branch:
        return
    
    # البحث عن تكامل نشط
    integration = db.query(Integration).filter(
        Integration.repository_id == repository.id,
        Integration.is_active == True
    ).first()
    
    if not integration:
        # إنشاء تكامل تلقائي إذا لم يوجد
        integration = create_default_integration(db, repository)
    
    # إنشاء عملية بناء جديدة
    build = Build(
        repository_id=repository.id,
        integration_id=integration.id,
        branch=branch,
        trigger_type="push",
        status="pending"
    )
    
    db.add(build)
    db.commit()
    db.refresh(build)
    
    # تشغيل مهمة البناء
    trigger_build.delay(build.id)


def process_pull_request_event(db: Session, repository: Repository, event_data: dict):
    """
    معالجة حدث pull request
    """
    pr_number = event_data.get("pr_number")
    action = event_data.get("action")
    branch = event_data.get("branch")
    base_branch = event_data.get("base_branch")
    
    # إنشاء عملية بناء للـ PR
    integration = db.query(Integration).filter(
        Integration.repository_id == repository.id,
        Integration.is_active == True
    ).first()
    
    if not integration:
        integration = create_default_integration(db, repository)
    
    build = Build(
        repository_id=repository.id,
        integration_id=integration.id,
        branch=branch,
        trigger_type="pull_request",
        pull_request_id=pr_number,
        status="pending"
    )
    
    db.add(build)
    db.commit()
    db.refresh(build)
    
    # تشغيل مهمة البناء
    trigger_build.delay(build.id)


def create_default_integration(db: Session, repository: Repository) -> Integration:
    """
    إنشاء تكامل افتراضي
    """
    # إنشاء GitHub Actions كتكامل افتراضي
    integration = Integration(
        repository_id=repository.id,
        platform="github_actions",
        is_active=True
    )
    
    db.add(integration)
    db.commit()
    db.refresh(integration)
    
    return integration


@celery_app.task(bind=True, name="app.tasks.github_handlers.setup_repository_webhook")
def setup_repository_webhook(self, repository_id: int):
    """
    إعداد webhook للمستودع
    """
    try:
        from ..github.webhook_manager import WebhookManager
        
        db = SessionLocal()
        repository = db.query(Repository).filter(
            Repository.id == repository_id
        ).first()
        
        if not repository:
            self.update_state(
                state="FAILURE",
                meta="المستودع غير موجود"
            )
            return
        
        # إعداد webhook
        webhook_manager = WebhookManager()
        webhook_url = webhook_manager.setup_webhook(
            repository.full_name,
            repository.owner
        )
        
        if webhook_url:
            # تحديث المستودع برابط webhook
            repository.webhook_secret = webhook_manager.generate_webhook_secret()
            db.commit()
        
        db.close()
        
        self.update_state(
            state="SUCCESS",
            meta=f"تم إعداد webhook بنجاح: {webhook_url}"
        )
        
        return webhook_url
        
    except Exception as e:
        self.update_state(
            state="FAILURE", 
            meta=f"خطأ في إعداد webhook: {str(e)}"
        )
        raise


@celery_app.task(bind=True, name="app.tasks.github_handlers.sync_repository_data")
def sync_repository_data(self, repository_id: int):
    """
    مزامنة بيانات المستودع من GitHub
    """
    try:
        from ..github.repository_sync import RepositorySync
        
        db = SessionLocal()
        repository = db.query(Repository).filter(
            Repository.id == repository_id
        ).first()
        
        if not repository:
            self.update_state(
                state="FAILURE",
                meta="المستودع غير موجود"
            )
            return
        
        # مزامنة البيانات
        sync = RepositorySync()
        updated_data = sync.sync_repository(repository.full_name)
        
        if updated_data:
            # تحديث المستودع
            repository.description = updated_data.get("description")
            repository.default_language = updated_data.get("language")
            repository.is_private = updated_data.get("private", False)
            db.commit()
        
        db.close()
        
        self.update_state(
            state="SUCCESS",
            meta="تم مزامنة البيانات بنجاح"
        )
        
        return updated_data
        
    except Exception as e:
        self.update_state(
            state="FAILURE",
            meta=f"خطأ في المزامنة: {str(e)}"
        )
        raise
