"""
Celery Tasks - المهام الخلفية
"""
from celery import Celery
from ..config import settings

# إنشاء celery app
celery_app = Celery(
    "github_builder",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=[
        "app.tasks.github_handlers",
        "app.tasks.build_handlers",
        "app.tasks.fix_handlers"
    ]
)

# إعدادات Celery
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    worker_prefetch_multiplier=1,
    task_routes={
        "app.tasks.github_handlers.*": {"queue": "github"},
        "app.tasks.build_handlers.*": {"queue": "builds"},
        "app.tasks.fix_handlers.*": {"queue": "fixes"},
    },
    beat_schedule={
        "cleanup-old-logs": {
            "task": "app.tasks.cleanup.cleanup_old_logs",
            "schedule": 86400.0,  # كل 24 ساعة
        },
        "send-health-report": {
            "task": "app.tasks.monitoring.send_health_report",
            "schedule": 3600.0,  # كل ساعة
        }
    }
)

if __name__ == "__main__":
    celery_app.start()
