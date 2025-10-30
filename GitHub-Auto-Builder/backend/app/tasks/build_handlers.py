"""
Build Handlers - معالجة عمليات البناء
"""
from celery import current_task
from sqlalchemy.orm import Session
from datetime import datetime
import time
import json

from ..models.database import SessionLocal
from ..models.build import Build
from ..models.integration import Integration
from ..models.repository import Repository
from ..config import settings
from . import celery_app


@celery_app.task(bind=True, name="app.tasks.build_handlers.trigger_build")
def trigger_build(self, build_id: int):
    """
    تشغيل عملية بناء
    """
    try:
        db = SessionLocal()
        
        # الحصول على تفاصيل البناء
        build = db.query(Build).filter(Build.id == build_id).first()
        if not build:
            self.update_state(
                state="FAILURE",
                meta="عملية البناء غير موجودة"
            )
            return
        
        # تحديث الحالة إلى "قيد التشغيل"
        build.status = "running"
        build.started_at = datetime.utcnow()
        db.commit()
        
        # تشغيل البناء حسب المنصة
        integration = build.integration
        
        if integration.platform == "github_actions":
            result = trigger_github_actions_build(build, integration)
        elif integration.platform == "codemagic":
            result = trigger_codemagic_build(build, integration)
        else:
            result = {
                "status": "error",
                "message": f"المنصة غير مدعومة: {integration.platform}"
            }
        
        # تحديث حالة البناء
        if result["status"] == "success":
            build.status = "success"
            build.build_id_platform = result.get("platform_build_id")
            build.logs_url = result.get("logs_url")
        else:
            build.status = "failed"
            build.error_logs = result.get("error_message", "")
        
        build.finished_at = datetime.utcnow()
        
        if build.started_at:
            build.calculate_duration()
        
        # تحديث آخر بناء للمستودع
        repository = build.repository
        repository.last_build_at = datetime.utcnow()
        
        db.commit()
        db.close()
        
        # بدء تحليل الأخطاء إذا فشل البناء
        if build.status == "failed":
            analyze_build_failure.delay(build_id)
        
        self.update_state(
            state="SUCCESS",
            meta=f"انتهت عملية البناء: {result['status']}"
        )
        
        return result
        
    except Exception as e:
        # تحديث حالة البناء إلى فشل
        try:
            db = SessionLocal()
            build = db.query(Build).filter(Build.id == build_id).first()
            if build:
                build.status = "failed"
                build.error_logs = str(e)
                build.finished_at = datetime.utcnow()
                
                if build.started_at:
                    build.calculate_duration()
                
                db.commit()
            db.close()
        except:
            pass
        
        self.update_state(
            state="FAILURE",
            meta=f"خطأ في تشغيل البناء: {str(e)}"
        )
        raise


def trigger_github_actions_build(build: Build, integration: Integration) -> dict:
    """
    تشغيل بناء GitHub Actions
    """
    try:
        # هنا يمكن إضافة منطق GitHub Actions API
        # مثل إنشاء workflow dispatch event
        
        # محاكاة بناء ناجح
        time.sleep(2)  # محاكاة وقت البناء
        
        return {
            "status": "success",
            "platform_build_id": f"gh-{build.id}-{int(time.time())}",
            "logs_url": f"https://github.com/{build.repository.full_name}/actions/runs/{build.id}",
            "message": "تم تشغيل GitHub Actions بنجاح"
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error_message": f"خطأ في GitHub Actions: {str(e)}"
        }


def trigger_codemagic_build(build: Build, integration: Integration) -> dict:
    """
    تشغيل بناء Codemagic
    """
    try:
        # هنا يمكن إضافة منطق Codemagic API
        
        # محاكاة بناء
        time.sleep(3)
        
        return {
            "status": "success",
            "platform_build_id": f"cm-{build.id}-{int(time.time())}",
            "logs_url": f"https://codemagic.io/app/{build.id}/build/latest",
            "message": "تم تشغيل Codemagic بنجاح"
        }
        
    except Exception as e:
        return {
            "status": "error", 
            "error_message": f"خطأ في Codemagic: {str(e)}"
        }


@celery_app.task(bind=True, name="app.tasks.build_handlers.monitor_build_status")
def monitor_build_status(self, build_id: int):
    """
    مراقبة حالة البناء
    """
    try:
        db = SessionLocal()
        
        build = db.query(Build).filter(Build.id == build_id).first()
        if not build:
            self.update_state(
                state="FAILURE",
                meta="عملية البناء غير موجودة"
            )
            return
        
        integration = build.integration
        
        # مراقبة حالة البناء حسب المنصة
        if integration.platform == "github_actions":
            status = check_github_actions_status(build)
        elif integration.platform == "codemagic":
            status = check_codemagic_status(build)
        else:
            status = {"status": "unknown"}
        
        # تحديث حالة البناء
        if status["status"] in ["success", "failed", "cancelled"]:
            build.status = status["status"]
            build.finished_at = datetime.utcnow()
            
            if build.started_at:
                build.calculate_duration()
            
            # حفظ اللوجات
            if "logs" in status:
                build.logs_content = status["logs"]
            
            db.commit()
            
            # بدء تحليل الأخطاء إذا فشل البناء
            if build.status == "failed":
                analyze_build_failure.delay(build_id)
        
        db.close()
        
        return status
        
    except Exception as e:
        self.update_state(
            state="FAILURE",
            meta=f"خطأ في مراقبة البناء: {str(e)}"
        )
        raise


def check_github_actions_status(build: Build) -> dict:
    """
    فحص حالة GitHub Actions
    """
    # محاكاة فحص الحالة
    import random
    
    statuses = ["running", "success", "failed"]
    status = random.choices(statuses, weights=[0.7, 0.2, 0.1])[0]
    
    return {
        "status": status,
        "logs": f"GitHub Actions logs for build {build.id}" if status in ["success", "failed"] else None
    }


def check_codemagic_status(build: Build) -> dict:
    """
    فحص حالة Codemagic
    """
    # محاكاة فحص الحالة
    import random
    
    statuses = ["running", "success", "failed"]
    status = random.choices(statuses, weights=[0.6, 0.3, 0.1])[0]
    
    return {
        "status": status,
        "logs": f"Codemagic logs for build {build.id}" if status in ["success", "failed"] else None
    }


@celery_app.task(bind=True, name="app.tasks.build_handlers.collect_build_logs")
def collect_build_logs(self, build_id: int):
    """
    جمع لوجات البناء
    """
    try:
        db = SessionLocal()
        
        build = db.query(Build).filter(Build.id == build_id).first()
        if not build:
            return
        
        # جمع اللوجات من المنصة
        logs_content = get_build_logs_from_platform(build)
        
        if logs_content:
            build.logs_content = logs_content
            db.commit()
        
        db.close()
        
        return {"status": "collected", "log_length": len(logs_content) if logs_content else 0}
        
    except Exception as e:
        self.update_state(
            state="FAILURE",
            meta=f"خطأ في جمع اللوجات: {str(e)}"
        )
        raise


def get_build_logs_from_platform(build: Build) -> str:
    """
    الحصول على لوجات البناء من المنصة
    """
    # محاكاة لوجات
    logs = f"""
=== Build Logs for {build.repository.full_name} ===
Branch: {build.branch}
Trigger: {build.trigger_type}
Status: {build.status}

Build started at: {build.started_at}
Build finished at: {build.finished_at}

[INFO] Starting build process...
[INFO] Checking dependencies...
[INFO] Running tests...
[INFO] Build completed successfully!
"""
    return logs


@celery_app.task(bind=True, name="app.tasks.build_handlers.retry_failed_builds")
def retry_failed_builds(self, repository_id: int = None):
    """
    إعادة تشغيل العمليات الفاشلة
    """
    try:
        db = SessionLocal()
        
        query = db.query(Build).filter(Build.status == "failed")
        
        if repository_id:
            query = query.filter(Build.repository_id == repository_id)
        
        failed_builds = query.all()
        
        retried_count = 0
        
        for build in failed_builds:
            # إنشاء عملية بناء جديدة
            new_build = Build(
                repository_id=build.repository_id,
                integration_id=build.integration_id,
                branch=build.branch,
                commit_sha=build.commit_sha,
                trigger_type="retry",
                status="pending"
            )
            
            db.add(new_build)
            db.commit()
            db.refresh(new_build)
            
            # تشغيل البناء الجديد
            trigger_build.delay(new_build.id)
            retried_count += 1
        
        db.close()
        
        return {
            "status": "completed",
            "message": f"تم إعادة تشغيل {retried_count} عملية بناء",
            "retried_count": retried_count
        }
        
    except Exception as e:
        self.update_state(
            state="FAILURE",
            meta=f"خطأ في إعادة التشغيل: {str(e)}"
        )
        raise


@celery_app.task(bind=True, name="app.tasks.build_handlers.cleanup_old_builds")
def cleanup_old_builds(self, days_to_keep: int = 30):
    """
    تنظيف العمليات القديمة
    """
    try:
        from datetime import timedelta
        
        db = SessionLocal()
        
        cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
        
        # حذف العمليات القديمة والناجحة فقط
        old_builds = db.query(Build).filter(
            Build.status == "success",
            Build.created_at < cutoff_date
        ).all()
        
        deleted_count = len(old_builds)
        
        for build in old_builds:
            db.delete(build)
        
        db.commit()
        db.close()
        
        return {
            "status": "completed",
            "message": f"تم حذف {deleted_count} عملية بناء قديمة",
            "deleted_count": deleted_count
        }
        
    except Exception as e:
        self.update_state(
            state="FAILURE",
            meta=f"خطأ في التنظيف: {str(e)}"
        )
        raise
