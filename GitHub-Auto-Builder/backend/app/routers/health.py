"""
مدقق الصحة العام للنظام
"""
from datetime import datetime
from typing import Dict, Any
from fastapi import APIRouter, HTTPException
from sqlalchemy import text

from ..config import settings
from ..models import SessionLocal, get_table_info

router = APIRouter()


@router.get("/")
async def health_check() -> Dict[str, Any]:
    """فحص صحة النظام العام"""
    try:
        # فحص قاعدة البيانات
        db_status = await check_database_health()
        
        # فحص Redis
        redis_status = await check_redis_health()
        
        # حالة عامة
        overall_status = "healthy"
        if not db_status["healthy"] or not redis_status["healthy"]:
            overall_status = "degraded"
        
        return {
            "status": overall_status,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "version": "0.1.0",
            "environment": settings.env,
            "components": {
                "database": db_status,
                "redis": redis_status,
                "api": {
                    "status": "healthy",
                    "uptime": "running"
                }
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail={
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
        )


@router.get("/database")
async def database_health() -> Dict[str, Any]:
    """فحص صحة قاعدة البيانات"""
    try:
        return await check_database_health()
    except Exception as e:
        raise HTTPException(status_code=503, detail=str(e))


@router.get("/redis")
async def redis_health() -> Dict[str, Any]:
    """فحص صحة Redis"""
    try:
        return await check_redis_health()
    except Exception as e:
        raise HTTPException(status_code=503, detail=str(e))


@router.get("/details")
async def detailed_health() -> Dict[str, Any]:
    """فحص تفصيلي للصحة"""
    try:
        # معلومات قاعدة البيانات
        db_info = get_table_info()
        
        # معلومات النظام
        import sys
        import platform
        
        return {
            "system": {
                "python_version": sys.version,
                "platform": platform.platform(),
                "architecture": platform.architecture(),
            },
            "database": db_info,
            "configuration": {
                "env": settings.env,
                "debug": settings.debug,
                "database_url_configured": bool(settings.database_url),
                "redis_url_configured": bool(settings.redis_url),
            },
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


async def check_database_health() -> Dict[str, Any]:
    """فحص صحة قاعدة البيانات"""
    try:
        db = SessionLocal()
        
        # اختبار بسيط للتأكد من الاتصال
        result = db.execute(text("SELECT 1")).scalar()
        
        if result != 1:
            raise Exception("Database query failed")
        
        # الحصول على معلومات الجداول
        table_info = get_table_info()
        
        db.close()
        
        return {
            "status": "healthy",
            "healthy": True,
            "connection": "active",
            "tables": table_info.get("total_tables", 0),
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        
    except Exception as e:
        return {
            "status": "unhealthy",
            "healthy": False,
            "connection": "failed",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }


async def check_redis_health() -> Dict[str, Any]:
    """فحص صحة Redis"""
    try:
        import redis
        from urllib.parse import urlparse
        
        # تحليل URL
        parsed = urlparse(settings.redis_url)
        
        # الاتصال بـ Redis
        r = redis.Redis(
            host=parsed.hostname or "localhost",
            port=parsed.port or 6379,
            password=parsed.password,
            decode_responses=True
        )
        
        # اختبار الاتصال
        r.ping()
        
        # الحصول على معلومات
        info = r.info()
        
        return {
            "status": "healthy",
            "healthy": True,
            "connection": "active",
            "version": info.get("redis_version", "unknown"),
            "uptime_in_seconds": info.get("uptime_in_seconds", 0),
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        
    except Exception as e:
        return {
            "status": "unhealthy",
            "healthy": False,
            "connection": "failed",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
