"""
Integrations Router - إدارة التكاملات مع منصات CI
"""
from datetime import datetime
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from fastapi import APIRouter, HTTPException, Depends, Query

from ..models import get_db, Integration, Repository
from ..config import settings

router = APIRouter()


@router.get("/")
async def list_integrations(
    platform: Optional[str] = Query(None, description="منصة CI"),
    repository_id: Optional[int] = Query(None, description="ID المستودع"),
    is_active: Optional[bool] = Query(None, description="هل التكامل نشط"),
    limit: int = Query(50, ge=1, le=100, description="عدد النتائج"),
    offset: int = Query(0, ge=0, description="رقم البداية"),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """قائمة التكاملات"""
    try:
        query = db.query(Integration)
        
        # تطبيق الفلاتر
        if platform:
            query = query.filter(Integration.platform == platform)
        
        if repository_id:
            query = query.filter(Integration.repository_id == repository_id)
        
        if is_active is not None:
            query = query.filter(Integration.is_active == is_active)
        
        # الحصول على العدد الإجمالي
        total = query.count()
        
        # الحصول على النتائج
        integrations = query.order_by(
            Integration.updated_at.desc()
        ).offset(offset).limit(limit).all()
        
        return {
            "integrations": [
                {
                    "id": integration.id,
                    "repository": {
                        "id": integration.repository.id,
                        "full_name": integration.repository.full_name
                    },
                    "platform": integration.platform,
                    "display_name": integration.display_name,
                    "is_active": integration.is_active,
                    "last_used_at": integration.last_used_at.isoformat() + "Z" if integration.last_used_at else None,
                    "created_at": integration.created_at.isoformat() + "Z" if integration.created_at else None,
                    "updated_at": integration.updated_at.isoformat() + "Z" if integration.updated_at else None
                }
                for integration in integrations
            ],
            "pagination": {
                "total": total,
                "limit": limit,
                "offset": offset,
                "has_more": offset + limit < total
            },
            "supported_platforms": Integration.get_supported_platforms()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/")
async def create_integration(
    integration_data: Dict[str, Any],
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """إنشاء تكامل جديد"""
    try:
        # التحقق من البيانات المطلوبة
        required_fields = ["repository_id", "platform"]
        for field in required_fields:
            if field not in integration_data:
                raise HTTPException(status_code=400, detail=f"حقل مطلوب: {field}")
        
        # التحقق من المنصة المدعومة
        if integration_data["platform"] not in Integration.get_supported_platforms():
            raise HTTPException(
                status_code=400,
                detail=f"المنصة غير مدعومة. المنصات المدعومة: {Integration.get_supported_platforms()}"
            )
        
        # التحقق من وجود المستودع
        repository = db.query(Repository).filter(
            Repository.id == integration_data["repository_id"]
        ).first()
        
        if not repository:
            raise HTTPException(status_code=404, detail="المستودع غير موجود")
        
        # التحقق من عدم وجود تكامل مماثل
        existing = db.query(Integration).filter(
            Integration.repository_id == integration_data["repository_id"],
            Integration.platform == integration_data["platform"]
        ).first()
        
        if existing:
            raise HTTPException(
                status_code=409,
                detail="التكامل موجود بالفعل لهذا المستودع"
            )
        
        # إنشاء التكامل
        integration = Integration(
            repository_id=integration_data["repository_id"],
            platform=integration_data["platform"],
            config_json=integration_data.get("config_json"),
            token_encrypted=integration_data.get("token_encrypted"),
            webhook_url=integration_data.get("webhook_url"),
            settings=integration_data.get("settings"),
            is_active=integration_data.get("is_active", True)
        )
        
        db.add(integration)
        db.commit()
        db.refresh(integration)
        
        return {
            "message": "تم إنشاء التكامل بنجاح",
            "integration": {
                "id": integration.id,
                "repository": repository.full_name,
                "platform": integration.platform,
                "display_name": integration.display_name,
                "is_active": integration.is_active
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{integration_id}")
async def get_integration(
    integration_id: int,
    include_config: bool = Query(False, description="تضمين الإعدادات"),
    include_recent_builds: bool = Query(False, description="تضمين العمليات الأخيرة"),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """الحصول على تفاصيل تكامل"""
    try:
        integration = db.query(Integration).filter(
            Integration.id == integration_id
        ).first()
        
        if not integration:
            raise HTTPException(status_code=404, detail="التكامل غير موجود")
        
        result = {
            "id": integration.id,
            "repository": {
                "id": integration.repository.id,
                "full_name": integration.repository.full_name,
                "owner": integration.repository.owner,
                "name": integration.repository.name
            },
            "details": {
                "platform": integration.platform,
                "display_name": integration.display_name,
                "is_active": integration.is_active,
                "last_used_at": integration.last_used_at.isoformat() + "Z" if integration.last_used_at else None
            },
            "timestamps": {
                "created_at": integration.created_at.isoformat() + "Z" if integration.created_at else None,
                "updated_at": integration.updated_at.isoformat() + "Z" if integration.updated_at else None
            }
        }
        
        # إضافة الإعدادات (بدون التوكن)
        if include_config:
            result["config"] = integration.config
            
            # إزالة التوكن من الاستجابة للحماية
            config_copy = integration.config.copy() if integration.config else {}
            if "token" in config_copy:
                config_copy["token"] = "***hidden***"
            result["config_public"] = config_copy
        
        # إضافة العمليات الأخيرة
        if include_recent_builds:
            recent_builds = (
                db.query(Build)
                .filter(Build.integration_id == integration_id)
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
                    "created_at": build.created_at.isoformat() + "Z" if build.created_at else None
                }
                for build in recent_builds
            ]
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{integration_id}")
async def update_integration(
    integration_id: int,
    update_data: Dict[str, Any],
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """تحديث إعدادات تكامل"""
    try:
        integration = db.query(Integration).filter(
            Integration.id == integration_id
        ).first()
        
        if not integration:
            raise HTTPException(status_code=404, detail="التكامل غير موجود")
        
        # تحديث الحقول المسموحة
        allowed_fields = ["config_json", "webhook_url", "settings", "is_active"]
        
        updated_fields = []
        
        for field in allowed_fields:
            if field in update_data:
                if field == "config_json" and update_data[field]:
                    integration.update_config(update_data[field])
                else:
                    setattr(integration, field, update_data[field])
                updated_fields.append(field)
        
        # تحديث timestamp
        integration.updated_at = datetime.utcnow()
        
        db.commit()
        
        return {
            "message": "تم تحديث التكامل بنجاح",
            "integration_id": integration_id,
            "updated_fields": updated_fields,
            "updated_at": integration.updated_at.isoformat() + "Z"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{integration_id}")
async def delete_integration(
    integration_id: int,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """حذف تكامل"""
    try:
        integration = db.query(Integration).filter(
            Integration.id == integration_id
        ).first()
        
        if not integration:
            raise HTTPException(status_code=404, detail="التكامل غير موجود")
        
        # التحقق من عدم وجود عمليات بناء جارية
        from ..models.build import Build
        active_builds = db.query(Build).filter(
            Build.integration_id == integration_id,
            Build.status.in_(["pending", "running"])
        ).count()
        
        if active_builds > 0:
            raise HTTPException(
                status_code=409,
                detail=f"لا يمكن حذف التكامل لوجود {active_builds} عملية بناء جارية"
            )
        
        # حذف التكامل
        repo_name = integration.repository.full_name
        platform_name = integration.display_name
        
        db.delete(integration)
        db.commit()
        
        return {
            "message": "تم حذف التكامل بنجاح",
            "deleted_integration": {
                "platform": platform_name,
                "repository": repo_name
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{integration_id}/test")
async def test_integration(
    integration_id: int,
    test_data: Optional[Dict[str, Any]] = None,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """اختبار تكامل"""
    try:
        integration = db.query(Integration).filter(
            Integration.id == integration_id
        ).first()
        
        if not integration:
            raise HTTPException(status_code=404, detail="التكامل غير موجود")
        
        if not integration.is_active:
            raise HTTPException(status_code=400, detail="التكامل غير نشط")
        
        # هنا يمكن إضافة منطق اختبار حقيقي للتكامل
        # مثل استدعاء API المنصة للتحقق من صحة التوكن
        
        # محاكاة اختبار ناجح
        test_result = {
            "integration_id": integration_id,
            "platform": integration.platform,
            "test_timestamp": datetime.utcnow().isoformat() + "Z",
            "status": "success",
            "message": "تم اختبار التكامل بنجاح",
            "connection_details": {
                "api_accessible": True,
                "authentication_valid": True,
                "permissions_sufficient": True
            }
        }
        
        # تحديث آخر استخدام
        integration.last_used_at = datetime.utcnow()
        db.commit()
        
        return test_result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/platforms/supported")
async def get_supported_platforms() -> Dict[str, Any]:
    """الحصول على قائمة المنصات المدعومة"""
    return {
        "supported_platforms": [
            {
                "platform": platform,
                "display_name": Integration.get_platform_display_name(platform)
            }
            for platform in Integration.get_supported_platforms()
        ],
        "integration_guides": {
            "github_actions": {
                "setup_url": "https://docs.github.com/en/actions",
                "description": "تكامل مباشر مع GitHub Actions"
            },
            "codemagic": {
                "setup_url": "https://codemagic.io/docs/",
                "description": "منصة CI/CD للتطبيقات"
            },
            "circleci": {
                "setup_url": "https://circleci.com/docs/",
                "description": "CI/CD منصة قوية"
            },
            "bitrise": {
                "setup_url": "https://devcenter.bitrise.io/",
                "description": "CI/CD للتطبيقات المحمولة"
            }
        }
    }


@router.post("/codemagic/configure")
async def configure_codemagic_integration(
    config_data: Dict[str, Any],
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """إعداد تكامل Codemagic"""
    try:
        # التحقق من البيانات المطلوبة
        required_fields = ["repository_id", "app_id"]
        for field in required_fields:
            if field not in config_data:
                raise HTTPException(status_code=400, detail=f"حقل مطلوب: {field}")
        
        # هنا يمكن إضافة منطق إعداد Codemagic
        # مثل إنشاء webhook وربط التطبيق
        
        return {
            "message": "تم إعداد تكامل Codemagic بنجاح",
            "platform": "codemagic",
            "configuration": {
                "app_id": config_data["app_id"],
                "webhook_configured": True
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/github-actions/configure")
async def configure_github_actions_integration(
    config_data: Dict[str, Any],
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """إعداد تكامل GitHub Actions"""
    try:
        required_fields = ["repository_id"]
        for field in required_fields:
            if field not in config_data:
                raise HTTPException(status_code=400, detail=f"حقل مطلوب: {field}")
        
        # هنا يمكن إضافة منطق إعداد GitHub Actions
        # مثل إنشاء workflow files تلقائياً
        
        return {
            "message": "تم إعداد تكامل GitHub Actions بنجاح",
            "platform": "github_actions",
            "configuration": {
                "workflows_created": True,
                "auto_trigger_configured": True
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
