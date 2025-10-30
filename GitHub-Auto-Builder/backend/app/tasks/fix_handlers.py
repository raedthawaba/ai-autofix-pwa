"""
Fix Handlers - تحليل وإصلاح الأخطاء تلقائياً
"""
from celery import current_task
from sqlalchemy.orm import Session
from datetime import datetime
import re
import json

from ..models.database import SessionLocal
from ..models.build import Build
from ..models.fix_attempt import FixAttempt
from ..models.repository import Repository
from ..config import settings
from . import celery_app


@celery_app.task(bind=True, name="app.tasks.fix_handlers.analyze_build_failure")
def analyze_build_failure(self, build_id: int):
    """
    تحليل فشل البناء ومحاولة الإصلاح
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
        
        # الحصول على اللوجات
        logs_content = build.logs_content or ""
        
        if not logs_content:
            self.update_state(
                state="FAILURE", 
                meta="لا توجد لوجات للتحليل"
            )
            return
        
        # تحليل الأخطاء
        error_patterns = analyze_error_patterns(logs_content)
        
        if not error_patterns:
            self.update_state(
                state="SUCCESS",
                meta="لم يتم العثور على أخطاء قابلة للإصلاح"
            )
            return
        
        # إنشاء محاولة إصلاح لكل خطأ
        fix_attempts_created = 0
        
        for pattern in error_patterns:
            fix_attempt = create_fix_attempt(db, build, pattern)
            if fix_attempt:
                fix_attempts_created += 1
        
        db.commit()
        db.close()
        
        # بدء محاولة الإصلاح إذا تم إنشاء محاولات
        if fix_attempts_created > 0:
            attempt_first_fix.delay(build_id)
        
        self.update_state(
            state="SUCCESS",
            meta=f"تم تحليل {len(error_patterns)} خطأ وإنشاء {fix_attempts_created} محاولة إصلاح"
        )
        
        return {
            "patterns_found": len(error_patterns),
            "attempts_created": fix_attempts_created
        }
        
    except Exception as e:
        self.update_state(
            state="FAILURE",
            meta=f"خطأ في تحليل البناء: {str(e)}"
        )
        raise


def analyze_error_patterns(logs_content: str) -> list:
    """
    تحليل أنماط الأخطاء في اللوجات
    """
    # قواعد الأخطاء الشائعة
    error_rules = [
        {
            "name": "missing_python_package",
            "pattern": r"ModuleNotFoundError: No module named '([^']+)'",
            "fix_type": "dependency_update",
            "confidence": 90,
            "description": "حزمة Python مفقودة"
        },
        {
            "name": "dependency_version_conflict",
            "pattern": r"ERROR:.*version.*conflict",
            "fix_type": "dependency_update", 
            "confidence": 80,
            "description": "تعارض في إصدارات التبعيات"
        },
        {
            "name": "gradle_sync_failed",
            "pattern": r"Gradle sync failed",
            "fix_type": "config_fix",
            "confidence": 85,
            "description": "فشل مزامنة Gradle"
        },
        {
            "name": "android_sdk_missing",
            "pattern": r"Android SDK.*not found",
            "fix_type": "environment_fix",
            "confidence": 90,
            "description": "Android SDK غير موجود"
        },
        {
            "name": "java_home_not_set",
            "pattern": r"JAVA_HOME.*not set",
            "fix_type": "environment_fix",
            "confidence": 95,
            "description": "متغير JAVA_HOME غير محدد"
        },
        {
            "name": "keystore_not_found",
            "pattern": r"keystore.*not found",
            "fix_type": "missing_file",
            "confidence": 85,
            "description": "ملف keystore مفقود"
        },
        {
            "name": "npm_package_missing",
            "pattern": r"npm ERR!.*not found",
            "fix_type": "dependency_update",
            "confidence": 80,
            "description": "حزمة NPM مفقودة"
        },
        {
            "name": "syntax_error",
            "pattern": r"SyntaxError.*",
            "fix_type": "syntax_fix",
            "confidence": 70,
            "description": "خطأ نحوي"
        }
    ]
    
    patterns_found = []
    
    for rule in error_rules:
        matches = re.finditer(rule["pattern"], logs_content, re.IGNORECASE)
        
        for match in matches:
            pattern_info = {
                "rule_name": rule["name"],
                "error_message": match.group(0),
                "matched_text": match.group(1) if match.groups() else "",
                "fix_type": rule["fix_type"],
                "confidence": rule["confidence"],
                "description": rule["description"],
                "line_number": logs_content[:match.start()].count('\n') + 1
            }
            
            patterns_found.append(pattern_info)
    
    return patterns_found


def create_fix_attempt(db: Session, build: Build, pattern: dict) -> FixAttempt:
    """
    إنشاء محاولة إصلاح جديدة
    """
    # التحقق من المحاولات السابقة
    existing_attempts = db.query(FixAttempt).filter(
        FixAttempt.build_id == build.id,
        FixAttempt.error_pattern == pattern["rule_name"],
        FixAttempt.status.in_(["pending", "applied"])
    ).count()
    
    if existing_attempts > 0:
        return None  # تخطي المحاولة المكررة
    
    # إنشاء المحاولة
    fix_attempt = FixAttempt(
        build_id=build.id,
        attempt_number=existing_attempts + 1,
        fix_type=pattern["fix_type"],
        status="pending",
        error_pattern=pattern["rule_name"],
        error_message=pattern["error_message"],
        confidence_score=pattern["confidence"],
        analysis_result=pattern,
        requires_approval=pattern["confidence"] < 80
    )
    
    # إنشاء اقتراح الإصلاح
    fix_suggestion = generate_fix_suggestion(pattern)
    fix_attempt.fix_suggestion = fix_suggestion
    
    db.add(fix_attempt)
    db.flush()  # للحصول على ID
    
    return fix_attempt


def generate_fix_suggestion(pattern: dict) -> str:
    """
    إنشاء اقتراح الإصلاح
    """
    suggestions = {
        "missing_python_package": f"إضافة الحزمة المفقودة: {pattern['matched_text']}",
        "dependency_version_conflict": "تحديث التبعيات لحل التعارض",
        "gradle_sync_failed": "تشغيل gradle clean build",
        "android_sdk_missing": "تثبيت وتكوين Android SDK",
        "java_home_not_set": "تعيين متغير JAVA_HOME",
        "keystore_not_found": "إنشاء ملف keystore أو تحديد المسار الصحيح",
        "npm_package_missing": f"تثبيت الحزمة: npm install {pattern['matched_text']}",
        "syntax_error": "مراجعة وتصحيح الكود النحوي"
    }
    
    return suggestions.get(pattern["rule_name"], "يحتاج إلى مراجعة يدوية")


@celery_app.task(bind=True, name="app.tasks.fix_handlers.attempt_first_fix")
def attempt_first_fix(self, build_id: int):
    """
    محاولة أول إصلاح
    """
    try:
        db = SessionLocal()
        
        # الحصول على المحاولة الأولى المعلقة
        fix_attempt = db.query(FixAttempt).filter(
            FixAttempt.build_id == build_id,
            FixAttempt.status == "pending"
        ).order_by(FixAttempt.attempt_number.asc()).first()
        
        if not fix_attempt:
            self.update_state(
                state="SUCCESS",
                meta="لا توجد محاولات إصلاح معلقة"
            )
            return
        
        # محاولة الإصلاح
        result = apply_fix_attempt(db, fix_attempt)
        
        db.commit()
        db.close()
        
        return result
        
    except Exception as e:
        self.update_state(
            state="FAILURE",
            meta=f"خطأ في محاولة الإصلاح: {str(e)}"
        )
        raise


def apply_fix_attempt(db: Session, fix_attempt: FixAttempt) -> dict:
    """
    تطبيق محاولة إصلاح
    """
    build = db.query(Build).filter(Build.id == fix_attempt.build_id).first()
    
    # حسب نوع الإصلاح
    if fix_attempt.fix_type == "dependency_update":
        result = apply_dependency_fix(db, build, fix_attempt)
    elif fix_attempt.fix_type == "config_fix":
        result = apply_config_fix(db, build, fix_attempt)
    elif fix_attempt.fix_type == "missing_file":
        result = apply_missing_file_fix(db, build, fix_attempt)
    else:
        result = {
            "status": "skipped",
            "message": f"نوع الإصلاح غير مدعوم: {fix_attempt.fix_type}"
        }
    
    # تحديث حالة المحاولة
    if result["status"] == "success":
        fix_attempt.mark_as_applied()
    else:
        fix_attempt.mark_as_failed(result.get("error", "خطأ في الإصلاح"))
    
    return result


def apply_dependency_fix(db: Session, build: Build, fix_attempt: FixAttempt) -> dict:
    """
    تطبيق إصلاح التبعية
    """
    try:
        # محاكاة إضافة requirement
        package_name = fix_attempt.analysis_result.get("matched_text", "")
        
        # إنشاء branch جديد
        branch_name = f"auto-fix/{build.id}/{fix_attempt.attempt_number}"
        
        # محاكاة إنشاء PR
        pr_url = f"https://github.com/{build.repository.full_name}/pull/{build.id}"
        
        # حفظ التغييرات
        fix_attempt.branch_name = branch_name
        fix_attempt.pull_request_url = pr_url
        fix_attempt.pull_request_number = build.id
        fix_attempt.changes_summary = f"إضافة حزمة {package_name}"
        
        return {
            "status": "success",
            "message": f"تم إنشاء PR لإضافة {package_name}",
            "branch": branch_name,
            "pr_url": pr_url
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }


def apply_config_fix(db: Session, build: Build, fix_attempt: FixAttempt) -> dict:
    """
    تطبيق إصلاح الإعدادات
    """
    try:
        # محاكاة إصلاح الإعدادات
        
        branch_name = f"auto-fix-config/{build.id}/{fix_attempt.attempt_number}"
        pr_url = f"https://github.com/{build.repository.full_name}/pull/{build.id}"
        
        fix_attempt.branch_name = branch_name
        fix_attempt.pull_request_url = pr_url
        fix_attempt.changes_summary = "إصلاح إعدادات البناء"
        
        return {
            "status": "success",
            "message": "تم إنشاء PR لإصلاح الإعدادات",
            "branch": branch_name,
            "pr_url": pr_url
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }


def apply_missing_file_fix(db: Session, build: Build, fix_attempt: FixAttempt) -> dict:
    """
    تطبيق إصلاح الملف المفقود
    """
    try:
        # محاكاة إنشاء الملف المفقود
        
        branch_name = f"auto-fix-file/{build.id}/{fix_attempt.attempt_number}"
        pr_url = f"https://github.com/{build.repository.full_name}/pull/{build.id}"
        
        fix_attempt.branch_name = branch_name
        fix_attempt.pull_request_url = pr_url
        fix_attempt.changes_summary = "إضافة ملف مفقود"
        
        return {
            "status": "success",
            "message": "تم إنشاء PR لإضافة الملف المفقود",
            "branch": branch_name,
            "pr_url": pr_url
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }


@celery_app.task(bind=True, name="app.tasks.fix_handlers.retry_build_after_fix")
def retry_build_after_fix(self, build_id: int):
    """
    إعادة تشغيل البناء بعد الإصلاح
    """
    try:
        from .build_handlers import trigger_build
        
        db = SessionLocal()
        
        build = db.query(Build).filter(Build.id == build_id).first()
        if not build:
            return
        
        # إنشاء عملية بناء جديدة للـ PR
        new_build = Build(
            repository_id=build.repository_id,
            integration_id=build.integration_id,
            branch=build.branch,
            trigger_type="auto_fix",
            status="pending"
        )
        
        db.add(new_build)
        db.commit()
        db.refresh(new_build)
        
        # تشغيل البناء الجديد
        trigger_build.delay(new_build.id)
        
        db.close()
        
        return {
            "status": "success",
            "new_build_id": new_build.id,
            "message": "تم إعادة تشغيل البناء بعد الإصلاح"
        }
        
    except Exception as e:
        self.update_state(
            state="FAILURE",
            meta=f"خطأ في إعادة التشغيل: {str(e)}"
        )
        raise


@celery_app.task(bind=True, name="app.tasks.fix_handlers.generate_fix_suggestions")
def generate_fix_suggestions(self, build_id: int):
    """
    توليد اقتراحات الإصلاح باستخدام LLM
    """
    try:
        db = SessionLocal()
        
        build = db.query(Build).filter(Build.id == build_id).first()
        if not build or not build.error_logs:
            return {"status": "no_errors", "suggestions": []}
        
        # هنا يمكن إضافة integration مع OpenAI أو نموذج محلي
        # للحصول على اقتراحات أكثر ذكاءً
        
        # محاكاة اقتراحات LLM
        suggestions = [
            {
                "type": "llm_suggestion",
                "title": "تحسين معالجة الأخطاء",
                "description": "إضافة error handling أفضل للكود",
                "confidence": 75
            },
            {
                "type": "code_refactor",
                "title": "إعادة هيكلة الكود",
                "description": "تحسين بنية المشروع",
                "confidence": 60
            }
        ]
        
        db.close()
        
        return {
            "status": "success",
            "suggestions": suggestions,
            "build_id": build_id
        }
        
    except Exception as e:
        self.update_state(
            state="FAILURE",
            meta=f"خطأ في توليد الاقتراحات: {str(e)}"
        )
        raise
