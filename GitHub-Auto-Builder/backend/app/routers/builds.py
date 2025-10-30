"""
Builds Router - إدارة عمليات البناء
"""
from datetime import datetime
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from fastapi import APIRouter, HTTPException, Depends, Query

from ..models import get_db, Build, Repository, Integration
from ..config import settings

router = APIRouter()


@router.get("/")
async def list_builds(
    repository_id: Optional[int] = Query(None, description="ID المستودع"),
    status: Optional[str] = Query(None, description="حالة البناء"),
    limit: int = Query(50, ge=1, le=100, description="عدد النتائج"),
    offset: int = Query(0, ge=0, description="رقم البداية"),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """قائمة عمليات البناء"""
    try:
        query = db.query(Build)
        
        # تطبيق الفلاتر
        if repository_id:
            query = query.filter(Build.repository_id == repository_id)
        
        if status:
            query = query.filter(Build.status == status)
        
        # الحصول على العدد الإجمالي
        total = query.count()
        
        # الحصول على النتائج
        builds = query.order_by(
            Build.created_at.desc()
        ).offset(offset).limit(limit).all()
        
        return {
            "builds": [
                {
                    "id": build.id,
                    "repository": build.repository.full_name,
                    "branch": build.branch,
                    "status": build.status_display,
                    "status_code": build.status,
                    "duration": build.duration_formatted,
                    "trigger_type": build.trigger_type,
                    "created_at": build.created_at.isoformat() + "Z" if build.created_at else None,
                    "started_at": build.started_at.isoformat() + "Z" if build.started_at else None,
                    "finished_at": build.finished_at.isoformat() + "Z" if build.finished_at else None,
                    "logs_summary": build.get_logs_summary(500)
                }
                for build in builds
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


@router.get("/{build_id}")
async def get_build(
    build_id: int,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """الحصول على تفاصيل عملية بناء"""
    try:
        build = db.query(Build).filter(Build.id == build_id).first()
        
        if not build:
            raise HTTPException(status_code=404, detail="عملية البناء غير موجودة")
        
        return {
            "id": build.id,
            "repository": {
                "id": build.repository.id,
                "full_name": build.repository.full_name
            },
            "integration": {
                "id": build.integration.id,
                "platform": build.integration.platform
            },
            "details": {
                "branch": build.branch,
                "commit_sha": build.commit_sha,
                "status": build.status_display,
                "status_code": build.status,
                "trigger_type": build.trigger_type,
                "pull_request_id": build.pull_request_id,
                "duration_seconds": build.duration_seconds,
                "duration_formatted": build.duration_formatted
            },
            "timing": {
                "created_at": build.created_at.isoformat() + "Z" if build.created_at else None,
                "started_at": build.started_at.isoformat() + "Z" if build.started_at else None,
                "finished_at": build.finished_at.isoformat() + "Z" if build.finished_at else None
            },
            "results": {
                "logs_url": build.logs_url,
                "logs_content": build.logs_content,
                "error_logs": build.error_logs,
                "test_results": build.test_results,
                "coverage_percentage": build.coverage_percentage,
                "artifacts_url": build.artifacts_url
            },
            "fix_attempts": [
                {
                    "id": attempt.id,
                    "type": attempt.fix_type_display,
                    "status": attempt.status_display,
                    "confidence_score": attempt.confidence_score,
                    "confidence_level": attempt.confidence_level,
                    "requires_approval": attempt.requires_approval,
                    "pull_request_url": attempt.pull_request_url,
                    "created_at": attempt.created_at.isoformat() + "Z" if attempt.created_at else None
                }
                for attempt in build.fix_attempts
            ]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{build_id}/logs")
async def update_build_logs(
    build_id: int,
    logs_data: Dict[str, Any],
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """تحديث لوجات عملية بناء"""
    try:
        build = db.query(Build).filter(Build.id == build_id).first()
        
        if not build:
            raise HTTPException(status_code=404, detail="عملية البناء غير موجودة")
        
        # تحديث اللوجات
        if "logs_url" in logs_data:
            build.logs_url = logs_data["logs_url"]
        
        if "logs_content" in logs_data:
            build.logs_content = logs_data["logs_content"]
        
        if "error_logs" in logs_data:
            build.error_logs = logs_data["error_logs"]
        
        # تحديث الحالة
        if "status" in logs_data:
            build.status = logs_data["status"]
            
            if logs_data["status"] in ["success", "failed", "cancelled", "timeout"]:
                build.finished_at = datetime.utcnow()
                if build.started_at:
                    build.calculate_duration()
        
        build.updated_at = datetime.utcnow()
        
        db.commit()
        
        return {
            "message": "تم تحديث اللوجات بنجاح",
            "build_id": build_id,
            "updated_fields": list(logs_data.keys())
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{build_id}/retry")
async def retry_build(
    build_id: int,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """إعادة تشغيل عملية بناء"""
    try:
        build = db.query(Build).filter(Build.id == build_id).first()
        
        if not build:
            raise HTTPException(status_code=404, detail="عملية البناء غير موجودة")
        
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
        
        # هنا يمكن إضافة مهمة لتشغيل البناء
        # await trigger_build.delay(new_build.id)
        
        return {
            "message": "تم إنشاء عملية بناء جديدة",
            "original_build_id": build_id,
            "new_build_id": new_build.id,
            "status": "created"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/statistics/summary")
async def build_statistics(
    repository_id: Optional[int] = Query(None, description="ID المستودع"),
    days: int = Query(7, ge=1, le=30, description="عدد الأيام"),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """إحصائيات البناء"""
    try:
        from datetime import timedelta
        from sqlalchemy import func, case
        
        # تحديد نطاق التاريخ
        start_date = datetime.utcnow() - timedelta(days=days)
        
        query = db.query(Build).filter(
            Build.created_at >= start_date
        )
        
        if repository_id:
            query = query.filter(Build.repository_id == repository_id)
        
        builds = query.all()
        
        # حساب الإحصائيات
        total_builds = len(builds)
        successful_builds = len([b for b in builds if b.status == "success"])
        failed_builds = len([b for b in builds if b.status == "failed"])
        running_builds = len([b for b in builds if b.status == "running"])
        pending_builds = len([b for b in builds if b.status == "pending"])
        
        # حساب معدل النجاح
        success_rate = (successful_builds / total_builds * 100) if total_builds > 0 else 0
        
        # حساب متوسط المدة
        completed_builds = [b for b in builds if b.duration_seconds]
        avg_duration = (
            sum(b.duration_seconds for b in completed_builds) / len(completed_builds)
            if completed_builds else 0
        )
        
        # إحصائيات حسب النوع
        trigger_types = {}
        for build in builds:
            trigger_type = build.trigger_type or "unknown"
            trigger_types[trigger_type] = trigger_types.get(trigger_type, 0) + 1
        
        return {
            "period": {
                "days": days,
                "start_date": start_date.isoformat() + "Z",
                "end_date": datetime.utcnow().isoformat() + "Z"
            },
            "totals": {
                "total_builds": total_builds,
                "successful_builds": successful_builds,
                "failed_builds": failed_builds,
                "running_builds": running_builds,
                "pending_builds": pending_builds
            },
            "rates": {
                "success_rate": round(success_rate, 2),
                "failure_rate": round(100 - success_rate, 2)
            },
            "timing": {
                "average_duration_seconds": round(avg_duration, 2),
                "average_duration_formatted": format_duration(avg_duration)
            },
            "triggers": trigger_types,
            "repository_id": repository_id
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def format_duration(seconds: int) -> str:
    """تنسيق المدة بالثواني"""
    if not seconds:
        return "0s"
    
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    
    if hours > 0:
        return f"{hours:02d}h {minutes:02d}m {secs:02d}s"
    elif minutes > 0:
        return f"{minutes:02d}m {secs:02d}s"
    else:
        return f"{secs:02d}s"
