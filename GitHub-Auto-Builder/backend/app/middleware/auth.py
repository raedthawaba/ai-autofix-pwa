"""
Authentication Middleware
"""
from fastapi import Request, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

# موقت للـ token البسيط (في الإنتاج يجب استخدام JWT أو OAuth)
BEARER_TOKEN = "demo-token-2025"


class AuthenticationMiddleware:
    """Authentication Middleware - بسيط للـ MVP"""
    
    def __init__(self, app):
        self.app = app
        self.security = HTTPBearer(auto_error=False)
    
    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            request = Request(scope, receive, send)
            
            # تجاوز authentication للـ webhooks و health checks
            if self.should_skip_auth(request):
                return await self.app(scope, receive, send)
            
            # التحقق من authentication للـ admin endpoints
            if self.requires_auth(request):
                await self.authenticate_request(request, send)
        
        return await self.app(scope, receive, send)
    
    def should_skip_auth(self, request: Request) -> bool:
        """التحقق من ضرورة تخطي authentication"""
        skip_paths = [
            "/",
            "/docs",
            "/redoc",
            "/openapi.json",
            "/api/health",
            "/api/webhooks"
        ]
        
        return any(request.url.path.startswith(path) for path in skip_paths)
    
    def requires_auth(self, request: Request) -> bool:
        """التحقق من ضرورة authentication"""
        # admin endpoints تحتاج authentication
        admin_paths = [
            "/api/repositories",
            "/api/integrations",
            "/api/admin"
        ]
        
        return any(request.url.path.startswith(path) for path in admin_paths)
    
    async def authenticate_request(self, request: Request, send):
        """المصادقة على الطلب"""
        try:
            from fastapi import Depends
            from fastapi.security import HTTPBearer
            
            # في هذا المكان يمكن إضافة منطق المصادقة الحقيقي
            # مثل JWT validation أو API key checking
            
            pass
            
        except Exception:
            await self.send_unauthorized_response(send)
    
    async def send_unauthorized_response(self, send):
        """إرسال رد غير مصرح"""
        response_data = {
            "error": {
                "code": 401,
                "message": "غير مصرح - مطلوب تسجيل دخول",
                "type": "Unauthorized"
            },
            "timestamp": "2025-10-30T23:03:52Z"
        }
        
        # إرسال response
        await send({
            "type": "http.response.start",
            "status": 401,
            "headers": [
                [b"content-type", b"application/json"],
                [b"www-authenticate", b"Bearer"]
            ]
        })
        
        await send({
            "type": "http.response.body",
            "body": str(response_data).encode()
        })
