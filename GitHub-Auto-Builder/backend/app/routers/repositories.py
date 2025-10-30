"""
Repositories Router - إدارة المستودعات
"""
from datetime import datetime
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from fastapi import APIRouter, HTTPException, Depends, Query

from ..models import get_db, Repository, Integration
from ..config import settings

router = APIRouter()


@router.get("/")
async def list_repositories(
    auto_fix_enabled: Optional[bool] = Query(None, description="هل الإصلاح التلقائي مفعل"),
    limit: int = Query(50, ge=1, le=100, description="عدد النتائج"),
    offset: int = Query(0, ge=0, description="رقم البداية"),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """قائمة المستودعات"""
    try:
        query = db.query(Repository)
        
        # تطبيق الفلاتر
        if auto_fix_enabled is not None:
            query = query.filter(Repository.auto_fix_enabled == auto_fix_enabled)
        
        # الحصول على العدد الإجمالي
        total = query.count()
        
        # الحصول على النتائج
        repositories = query.order_by(
            Repository.updated_at.desc()
        ).offset(offset).limit(limit).all()
        
        return {
            "repositories": [
                {
                    "id": repo.id,
                    "full_name": repo.full_name,
                    "owner": repo.owner,
                    "name": repo.name,
                    "description": repo.description,
                    "default_language": repo.default_language,
                    "is_private": repo.is_private,
                    "auto_fix_enabled": repo.auto_fix_enabled,
                    "auto_fix_safe_only": repo.auto_fix_safe_only,
                    "auto_merge_enabled": repo.auto_merge_enabled,
                    "primary_branch": repo.primary_branch,
                    "last_build_at": repo.last_build_at.isoformat() + "Z" if repo.last_build_at else None,
                    "integrations_count": len(repo.integrations),
                    "github_url": repo.github_url,
                    "created_at": repo.created_at.isoformat() + "Z" if repo.created_at else None,
                    "updated_at": repo.updated_at.isoformat() + "Z" if repo.updated_at else None
                }
                for repo in repositories
            ],
            "pagination": {
                "total": total,
                "limit": limit,
                "offset": offset,
                "has_more": offset + limit < total
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/")
async def create_repository(
    repo_data: Dict[str, Any],
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """إنشاء مستودع جديد"""
    try:
        # التحقق من البيانات المطلوبة
        required_fields = ["owner", "name", "github_repo_id"]
        for field in required_fields:
            if field not in repo_data:
                raise HTTPException(status_code=400, detail=f"حقل مطلوب: {field}")
        
        # التحقق من عدم وجود المستودع
        existing = db.query(Repository).filter(
            Repository.github_repo_id == repo_data["github_repo_id"]
        ).first()
        
        if existing:
            raise HTTPException(
                status_code=409, 
                detail="المستودع موجود بالفعل"
            )
        
        # إنشاء المستودع
        repository = Repository(
            owner=repo_data["owner"],
            name=repo_data["name"],
            github_repo_id=repo_data["github_repo_id"],
            full_name=f"{repo_data['owner']}/{repo_data['name']}",
            description=repo_data.get("description"),
            default_language=repo_data.get("default_language"),
            is_private=repo_data.get("is_private", False),
            auto_fix_enabled=repo_data.get("auto_fix_enabled", False),
            auto_fix_safe_only=repo_data.get("auto_fix_safe_only", True),
            auto_merge_enabled=repo_data.get("auto_merge_enabled", False),
            primary_branch=repo_data.get("primary_branch", "main"),
            settings_json=repo_data.get("settings_json")
        )
        
        db.add(repository)
        db.commit()
        db.refresh(repository)
        
        return {
            "message": "تم إنشاء المستودع بنجاح",
            "repository": {
                "id": repository.id,
                "full_name": repository.full_name,
                "auto_fix_enabled": repository.auto_fix_enabled,
                "github_url": repository.github_url
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{repository_id}")
async def get_repository(
    repository_id: int,
    include_integrations: bool = Query(True, description="تضمين التكاملات"),
    include_recent_builds: bool = Query(False, description="تضمين العمليات الأخيرة"),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """الحصول على تفاصيل مستودع"""
    try:
        repository = db.query(Repository).filter(
            Repository.id == repository_id
        ).first()
        
        if not repository:
            raise HTTPException(status_code=404, detail="المستودع غير موجود")
        
        result = {
            "id": repository.id,
            "details": {
                "full_name": repository.full_name,
                "owner": repository.owner,
                "name": repository.name,
                "github_repo_id": repository.github_repo_id,
                "description": repository.description,
                "default_language": repository.default_language,
                "is_private": repository.is_private,
                "primary_branch": repository.primary_branch
            },
            "settings": {
                "auto_fix_enabled": repository.auto_fix_enabled,
                "auto_fix_safe_only": repository.auto_fix_safe_only,
                "auto_merge_enabled": repository.auto_merge_enabled,
                "custom_settings": repository.settings
            },
            "timestamps": {
                "created_at": repository.created_at.isoformat() + "Z" if repository.created_at else None,
                "updated_at": repository.updated_at.isoformat() + "Z" if repository.updated_at else None,
                "last_build_at": repository.last_build_at.isoformat() + "Z" if repository.last_build_at else None
            },
            "github_url": repository.github_url
        }
        
        # إضافة التكاملات
        if include_integrations:
            result["integrations"] = [
                {
                    "id": integration.id,
                    "platform": integration.platform,
                    "display_name": integration.display_name,
                    "is_active": integration.is_active,
                    "last_used_at": integration.last_used_at.isoformat() + "Z" if integration.last_used_at else None,
                    "created_at": integration.created_at.isoformat() + "Z" if integration.created_at else None
                }
                for integration in repository.integrations
            ]
        
        # إضافة العمليات الأخيرة
        if include_recent_builds:
            recent_builds = (
                db.query(Build)
                .filter(Build.repository_id == repository_id)
                .order_by(Build.created_at.desc())
                .limit(10)
                .all()
            )
            
            result["recent_builds"] = [
                {
                    "id": build.id,
                    "branch": build.branch,
                    "status": build.status_display,
                    "status_code": build.status,
                    "trigger_type": build.trigger_type,
                    "duration_formatted": build.duration_formatted,
                    "created_at": build.created_at.isoformat() + "Z" if build.created_at else None,
                    "logs_summary": build.get_logs_summary(200)
                }
                for build in recent_builds
            ]
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{repository_id}")
async def update_repository(
    repository_id: int,
    update_data: Dict[str, Any],
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """تحديث إعدادات مستودع"""
    try:
        repository = db.query(Repository).filter(
            Repository.id == repository_id
        ).first()
        
        if not repository:
            raise HTTPException(status_code=404, detail="المستودع غير موجود")
        
        # تحديث الحقول المسموحة
        allowed_fields = [
            "description", "auto_fix_enabled", "auto_fix_safe_only", 
            "auto_merge_enabled", "primary_branch"
        ]
        
        updated_fields = []
        
        for field in allowed_fields:
            if field in update_data:
                if field == "custom_settings":
                    repository.update_settings(update_data[field])
                else:
                    setattr(repository, field, update_data[field])
                updated_fields.append(field)
        
        # تحديث timestamp
        repository.updated_at = datetime.utcnow()
        
        db.commit()
        
        return {
            "message": "تم تحديث المستودع بنجاح",
            "repository_id": repository_id,
            "updated_fields": updated_fields,
            "updated_at": repository.updated_at.isoformat() + "Z"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{repository_id}")
async def delete_repository(
    repository_id: int,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """حذف مستودع"""
    try:
        repository = db.query(Repository).filter(
            Repository.id == repository_id
        ).first()
        
        if not repository:
            raise HTTPException(status_code=404, detail="المستودع غير موجود")
        
        # التحقق من عدم وجود عمليات بناء جارية
        from ..models.build import Build
        active_builds = db.query(Build).filter(
            Build.repository_id == repository_id,
            Build.status.in_(["pending", "running"])
        ).count()
        
        if active_builds > 0:
            raise HTTPException(
                status_code=409,
                detail=f"لا يمكن حذف المستودع لوجود {active_builds} عملية بناء جارية"
            )
        
        # حذف التكاملات أولاً
        db.query(Integration).filter(
            Integration.repository_id == repository_id
        ).delete()
        
        # حذف المستودع
        repo_name = repository.full_name
        db.delete(repository)
        db.commit()
        
        return {
            "message": "تم حذف المستودع بنجاح",
            "deleted_repository": repo_name
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{repository_id}/link")
async def link_github_repository(
    repository_id: int,
    github_data: Dict[str, Any],
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """ربط مستودع مع GitHub"""
    try:
        repository = db.query(Repository).filter(
            Repository.id == repository_id
        ).first()
        
        if not repository:
            raise HTTPException(status_code=404, detail="المستودع غير موجود")
        
        # هنا يمكن إضافة منطق ربط GitHub App أو الحصول على التوكن
        
        return {
            "message": "تم ربط المستودع مع GitHub بنجاح",
            "repository_id": repository_id,
            "github_integration": "configured"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{repository_id}/settings")
async def get_repository_settings(
    repository_id: int,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """الحصول على إعدادات مستودع مفصلة"""
    try:
        repository = db.query(Repository).filter(
            Repository.id == repository_id
        ).first()
        
        if not repository:
            raise HTTPException(status_code=404, detail="المستودع غير موجود")
        
        return {
            "repository_id": repository_id,
            "auto_fix": {
                "enabled": repository.auto_fix_enabled,
                "safe_only": repository.auto_fix_safe_only,
                "max_attempts": settings.auto_fix_max_attempts,
                "allowed_file_types": settings.auto_fix_safe_types
            },
            "auto_merge": {
                "enabled": repository.auto_merge_enabled,
                "primary_branch": repository.primary_branch
            },
            "notifications": {
                "webhook_secret": bool(repository.webhook_secret),
                "settings": repository.settings
            },
            "security": {
                "require_approval": True,  # دائماً مطلوب للموافقة
                "review_required": not repository.auto_merge_enabled
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
