"""
التطبيق الرئيسي - FastAPI REST API
"""
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager

from .config import settings, get_security_headers
from .models.database import create_tables, get_table_info
from .routers import github_webhooks, builds, repositories, integrations, health
from .middleware.rate_limiter import RateLimitMiddleware
from .middleware.auth import AuthenticationMiddleware
from .middleware.logging import LoggingMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    """إدارة دورة حياة التطبيق"""
    # Startup
    print("🚀 بدء تشغيل GitHub Auto Builder...")
    print(f"🔧 البيئة: {settings.env}")
    print(f"🐍 Python: 3.11+")
    
    # إنشاء الجداول
    try:
        create_tables()
        print("✅ تم إنشاء جداول قاعدة البيانات بنجاح")
        
        # فحص الاتصال
        info = get_table_info()
        if info['connected']:
            print(f"📊 قاعدة البيانات: {info['total_tables']} جدول")
        else:
            print(f"❌ خطأ في قاعدة البيانات: {info.get('error', 'غير محدد')}")
            
    except Exception as e:
        print(f"❌ خطأ في إعداد قاعدة البيانات: {e}")
    
    yield
    
    # Shutdown
    print("🔄 إيقاف GitHub Auto Builder...")


# إنشاء تطبيق FastAPI
app = FastAPI(
    title="GitHub Auto Builder API",
    description="أداة ذكية لأتمتة الربط مع GitHub وتشغيل البناء وإصلاح الأخطاء تلقائياً",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# إضافة Middleware
app.add_middleware(GZipMiddleware, minimum_size=1000)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.env == "development" else ["https://yourdomain.com"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# Rate Limiting
if settings.env == "production":
    app.add_middleware(RateLimitMiddleware)

# Authentication
app.add_middleware(AuthenticationMiddleware)

# Logging
app.add_middleware(LoggingMiddleware)


# إضافة Security Headers
@app.middleware("http")
async def add_security_headers(request, call_next):
    response = await call_next(request)
    for header, value in get_security_headers().items():
        response.headers[header] = value
    return response


# إضافة Routers
app.include_router(health.router, prefix="/api/health", tags=["Health"])
app.include_router(github_webhooks.router, prefix="/api/webhooks", tags=["GitHub Webhooks"])
app.include_router(builds.router, prefix="/api/builds", tags=["Builds"])
app.include_router(repositories.router, prefix="/api/repositories", tags=["Repositories"])
app.include_router(integrations.router, prefix="/api/integrations", tags=["Integrations"])


# Global Exception Handler
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.status_code,
                "message": exc.detail,
                "type": "HTTPException"
            },
            "timestamp": "2025-10-30T23:03:52Z",
            "path": str(request.url.path)
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "code": 500,
                "message": "خطأ داخلي في الخادم" if settings.env == "production" else str(exc),
                "type": "InternalServerError"
            },
            "timestamp": "2025-10-30T23:03:52Z",
            "path": str(request.url.path)
        }
    )


# Root Endpoint
@app.get("/", tags=["Root"])
async def root():
    """الصفحة الرئيسية"""
    return {
        "message": "مرحباً بك في GitHub Auto Builder API",
        "version": "0.1.0",
        "status": "active",
        "docs_url": "/docs",
        "health_check": "/api/health"
    }


# API Info Endpoint
@app.get("/api", tags=["API"])
async def api_info():
    """معلومات API"""
    return {
        "name": "GitHub Auto Builder API",
        "version": "0.1.0",
        "description": "أداة ذكية لأتمتة البناء وإصلاح الأخطاء",
        "endpoints": {
            "health": "/api/health",
            "webhooks": "/api/webhooks",
            "builds": "/api/builds",
            "repositories": "/api/repositories",
            "integrations": "/api/integrations"
        },
        "documentation": "/docs"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    )
