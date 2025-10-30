"""
Rate Limiting Middleware
"""
from fastapi import Request, HTTPException
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from ..config import settings

# إنشاء limiter
limiter = Limiter(key_func=get_remote_address)


class RateLimitMiddleware:
    """Rate Limiting Middleware"""
    
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            # تطبيق limits حسب نوع الـ endpoint
            request = Request(scope, receive, send)
            
            # تطبيق rate limits مختلفة حسب المسار
            await self.apply_limits(request, send)
        
        return await self.app(scope, receive, send)
    
    async def apply_limits(self, request: Request, send):
        """تطبيق limits"""
        # يمكن تطبيق limits مختلفة حسب المسار
        path = request.url.path
        
        if path.startswith("/api/webhooks"):
            # webhooks - limits مرنة أكثر
            pass
        elif path.startswith("/api/builds"):
            # builds - limits متوسطة
            pass
        elif path.startswith("/api/health"):
            # health checks - no limits
            pass
        else:
            # باقي الـ endpoints
            pass


def setup_rate_limiting(app):
    """إعداد rate limiting للتطبيق"""
    if settings.env == "production":
        # إضافة handlers
        app.state.limiter = limiter
        app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
        
        # تطبيق limits على الـ endpoints
        app.add_api_route(
            "/api/webhooks/github",
            github_webhook,
            methods=["POST"],
            dependencies=[
                Depends(
                    limiter.limit(f"{settings.rate_limit_requests_per_hour}/hour")
                )
            ]
        )
