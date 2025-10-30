"""
Logging Middleware - تسجيل جميع الطلبات
"""
import time
import json
from typing import Dict, Any
from fastapi import Request
from starlette.middleware.base import RequestResponseEndpoint
from starlette.types import ASGIApp
from starlette.responses import Response

from ..models.database import SessionLocal
from ..models.audit_log import AuditLog


class LoggingMiddleware:
    """Logging Middleware"""
    
    def __init__(self, app: ASGIApp):
        self.app = app
    
    async def __call__(self, scope: Dict[str, Any], receive, send):
        if scope["type"] == "http":
            request = Request(scope)
            start_time = time.time()
            
            # حفظ البيانات الأولية
            scope["start_time"] = start_time
            scope["request_id"] = self.generate_request_id()
            
            # معالجة الطلب
            response = await self.app(scope, receive, send)
            
            # تسجيل العملية
            await self.log_request(request, start_time, response)
            
            return response
        else:
            return await self.app(scope, receive, send)
    
    def generate_request_id(self) -> str:
        """إنشاء معرف فريد للطلب"""
        import uuid
        return str(uuid.uuid4())
    
    async def log_request(self, request: Request, start_time: float, response: Response):
        """تسجيل تفاصيل الطلب"""
        try:
            end_time = time.time()
            duration = end_time - start_time
            
            # إنشاء سجل مراجعة
            log_entry = AuditLog()
            log_entry.record_action(
                actor_type="api",
                actor_name="api_client",
                action="api_request",
                description=f"{request.method} {request.url.path}",
                resource_type="api_endpoint",
                resource_name=request.url.path,
                details={
                    "method": request.method,
                    "path": request.url.path,
                    "query_params": dict(request.query_params),
                    "client_ip": self.get_client_ip(request),
                    "user_agent": request.headers.get("user-agent"),
                    "status_code": response.status_code,
                    "duration_seconds": round(duration, 3),
                    "request_id": request.scope.get("request_id")
                },
                success=response.status_code < 400,
                error_message=None if response.status_code < 400 else f"HTTP {response.status_code}"
            )
            
            # حفظ في قاعدة البيانات (في background)
            await self.save_log_async(log_entry)
            
        except Exception as e:
            # لا نريد أن يفشل الطلب بسبب خطأ في logging
            print(f"خطأ في تسجيل الطلب: {e}")
    
    def get_client_ip(self, request: Request) -> str:
        """الحصول على IP الحقيقي للعميل"""
        # البحث عن IP في headers مختلفة
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        return request.client.host if request.client else "unknown"
    
    async def save_log_async(self, log_entry: AuditLog):
        """حفظ السجل بشكل غير متزامن"""
        try:
            import asyncio
            loop = asyncio.get_event_loop()
            
            # تشغيل في thread منفصل لتجنب blocking
            await loop.run_in_executor(
                None,
                self._save_log_sync,
                log_entry
            )
            
        except Exception as e:
            print(f"خطأ في حفظ السجل: {e}")
    
    def _save_log_sync(self, log_entry: AuditLog):
        """حفظ السجل بشكل متزامن"""
        try:
            db = SessionLocal()
            db.add(log_entry)
            db.commit()
        except Exception as e:
            print(f"خطأ في حفظ السجل في قاعدة البيانات: {e}")
            db.rollback()
        finally:
            db.close()
