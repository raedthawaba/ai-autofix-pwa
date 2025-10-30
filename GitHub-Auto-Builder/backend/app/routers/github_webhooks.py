"""
GitHub Webhooks Router - معالجة إشعارات GitHub
"""
import hmac
import hashlib
import json
from datetime import datetime
from typing import Dict, Any, Optional

from fastapi import APIRouter, HTTPException, Header, Request, Depends
from sqlalchemy.orm import Session

from ..config import settings
from ..models import get_db, AuditLog
from ..tasks.github_handlers import process_github_event
from ..models.repository import Repository

router = APIRouter()


@router.post("/github")
async def github_webhook(
    request: Request,
    x_hub_signature_256: Optional[str] = Header(None),
    x_github_event: Optional[str] = Header(None),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    استقبال ومعالجة webhooks من GitHub
    """
    try:
        # الحصول على body
        body = await request.body()
        
        # التحقق من التوقيع
        if not verify_github_signature(body, x_hub_signature_256):
            raise HTTPException(
                status_code=401,
                detail="توقيع GitHub غير صحيح"
            )
        
        # تحليل payload
        try:
            payload = json.loads(body)
        except json.JSONDecodeError:
            raise HTTPException(
                status_code=400,
                detail="Payload غير صالح"
            )
        
        # الحصول على معلومات GitHub
        event_type = x_github_event or payload.get("action", "unknown")
        repository = payload.get("repository", {})
        sender = payload.get("sender", {})
        
        # تسجيل العملية
        log_action(
            db=db,
            actor_type="github",
            actor_name=sender.get("login", "unknown"),
            action="webhook_received",
            resource_type="repository",
            resource_name=repository.get("full_name"),
            details={
                "event_type": event_type,
                "repository": repository,
                "sender": sender,
                "payload_keys": list(payload.keys())
            }
        )
        
        # تحديد نوع العملية
        if event_type == "push":
            await handle_push_event(payload, db)
        elif event_type == "pull_request":
            await handle_pull_request_event(payload, db)
        elif event_type == "issues":
            await handle_issues_event(payload, db)
        else:
            # إشعار عام
            await process_github_event.delay({
                "event_type": event_type,
                "payload": payload,
                "repository": repository,
                "sender": sender
            })
        
        return {
            "status": "received",
            "event_type": event_type,
            "repository": repository.get("full_name"),
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        # تسجيل الخطأ
        log_action(
            db=db,
            actor_type="system",
            action="webhook_error",
            description=f"خطأ في معالجة webhook: {str(e)}",
            success=False,
            error_message=str(e)
        )
        
        raise HTTPException(
            status_code=500,
            detail=f"خطأ في معالجة webhook: {str(e)}"
        )


def verify_github_signature(body: bytes, signature: str) -> bool:
    """التحقق من توقيع GitHub"""
    if not settings.github_webhook_secret:
        return True  # في حالة عدم وجود secret (للاختبار)
    
    if not signature:
        return False
    
    # حساب التوقيع المتوقع
    expected_signature = "sha256=" + hmac.new(
        settings.github_webhook_secret.encode(),
        body,
        hashlib.sha256
    ).hexdigest()
    
    # مقارنة التوقيعات
    return hmac.compare_digest(signature, expected_signature)


async def handle_push_event(payload: Dict[str, Any], db: Session) -> None:
    """معالجة حدث push"""
    repository = payload.get("repository", {})
    ref = payload.get("ref", "")
    commits = payload.get("commits", [])
    
    # البحث عن المستودع في قاعدة البيانات
    repo = db.query(Repository).filter(
        Repository.full_name == repository.get("full_name")
    ).first()
    
    if repo:
        # تسجيل العملية
        log_action(
            db=db,
            actor_type="github",
            actor_name=payload.get("pusher", {}).get("name", "unknown"),
            action="push_received",
            resource_type="repository",
            resource_id=repo.id,
            resource_name=repo.full_name,
            details={
                "ref": ref,
                "commits_count": len(commits),
                "after_commit": payload.get("after")
            }
        )
        
        # إضافة مهمة لتشغيل البناء
        if repo.auto_fix_enabled:
            await process_github_event.delay({
                "event_type": "push",
                "repository_id": repo.id,
                "branch": ref.replace("refs/heads/", ""),
                "commits": commits,
                "action": "trigger_build"
            })
    else:
        # مستودع غير مسجل
        log_action(
            db=db,
            actor_type="system",
            action="push_received_unregistered_repo",
            resource_type="repository",
            resource_name=repository.get("full_name"),
            details={
                "ref": ref,
                "commits_count": len(commits)
            },
            success=False,
            error_message="المستودع غير مسجل في النظام"
        )


async def handle_pull_request_event(payload: Dict[str, Any], db: Session) -> None:
    """معالجة حدث pull request"""
    action = payload.get("action", "opened")
    pull_request = payload.get("pull_request", {})
    repository = payload.get("repository", {})
    
    if action in ["opened", "synchronize", "reopened"]:
        # البحث عن المستودع
        repo = db.query(Repository).filter(
            Repository.full_name == repository.get("full_name")
        ).first()
        
        if repo and repo.auto_fix_enabled:
            # تسجيل العملية
            log_action(
                db=db,
                actor_type="github",
                actor_name=payload.get("sender", {}).get("login", "unknown"),
                action="pull_request_received",
                resource_type="repository",
                resource_id=repo.id,
                resource_name=repo.full_name,
                details={
                    "action": action,
                    "pr_number": pull_request.get("number"),
                    "pr_title": pull_request.get("title"),
                    "branch": pull_request.get("head", {}).get("ref")
                }
            )
            
            # إضافة مهمة لتشغيل البناء
            await process_github_event.delay({
                "event_type": "pull_request",
                "repository_id": repo.id,
                "pr_number": pull_request.get("number"),
                "action": action,
                "branch": pull_request.get("head", {}).get("ref"),
                "base_branch": pull_request.get("base", {}).get("ref")
            })


async def handle_issues_event(payload: Dict[str, Any], db: Session) -> None:
    """معالجة حدث issues"""
    action = payload.get("action", "opened")
    issue = payload.get("issue", {})
    repository = payload.get("repository", {})
    
    # تسجيل العملية فقط للأخطاء
    log_action(
        db=db,
        actor_type="github",
        actor_name=payload.get("sender", {}).get("login", "unknown"),
        action="issue_received",
        resource_type="repository",
        resource_name=repository.get("full_name"),
        details={
            "action": action,
            "issue_number": issue.get("number"),
            "issue_title": issue.get("title"),
            "labels": [label.get("name") for label in issue.get("labels", [])]
        }
    )


def log_action(
    db: Session,
    actor_type: str,
    action: str,
    description: str = "",
    resource_type: str = None,
    resource_id: int = None,
    resource_name: str = None,
    details: dict = None,
    success: bool = True,
    error_message: str = None
) -> None:
    """تسجيل عملية في سجل المراجعة"""
    try:
        log_entry = AuditLog()
        log_entry.record_action(
            actor_type=actor_type,
            action=action,
            description=description,
            resource_type=resource_type,
            resource_id=resource_id,
            resource_name=resource_name,
            details=details,
            success=success,
            error_message=error_message
        )
        
        db.add(log_entry)
        db.commit()
        
    except Exception as e:
        print(f"خطأ في تسجيل العملية: {e}")
        db.rollback()


@router.get("/events")
async def list_webhook_events(
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """قائمة أحداث Webhook الأخيرة"""
    try:
        logs = db.query(AuditLog).filter(
            AuditLog.action.like("%webhook%")
        ).order_by(
            AuditLog.timestamp.desc()
        ).offset(offset).limit(limit).all()
        
        return {
            "events": [
                {
                    "id": log.id,
                    "action": log.action_display,
                    "actor": log.actor_name,
                    "resource": log.resource_name,
                    "success": log.success,
                    "timestamp": log.timestamp.isoformat() + "Z",
                    "details": log.details
                }
                for log in logs
            ],
            "total": len(logs),
            "limit": limit,
            "offset": offset
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
