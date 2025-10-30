# دليل التشغيل السريع

## 🚀 بدء التشغيل

### 1. الإعداد الأولي

```bash
# استنساخ المشروع
git clone <repository-url>
cd GitHub-Auto-Builder

# نسخ ملف الإعدادات
cp .env.example .env
```

### 2. تشغيل النظام

```bash
# تشغيل جميع الخدمات
docker-compose up -d

# فحص حالة الخدمات
docker-compose ps

# مراقبة اللوجات
docker-compose logs -f backend
```

### 3. اختبار النظام

```bash
# اختبار الصحة العامة
curl http://localhost:8000/api/health

# اختبار API
curl http://localhost:8000/api

# اختبار قاعدة البيانات
curl http://localhost:8000/api/health/database
```

### 4. الوصول للواجهات

- **API Documentation**: http://localhost:8000/docs
- **Frontend Dashboard**: http://localhost:3000
- **Flower (Task Monitoring)**: http://localhost:5555
- **Health Check**: http://localhost:8000/api/health

## 🔧 Development

### Backend Development

```bash
cd backend

# تثبيت المكتبات
pip install -r requirements.txt

# تشغيل migrations
alembic upgrade head

# تشغيل الخادم
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Development

```bash
cd frontend

# تثبيت المكتبات
npm install

# تشغيل التطوير
npm start
```

### Testing

```bash
# تشغيل جميع الاختبارات
pytest

# تشغيل اختبارات محددة
pytest tests/test_api.py -v

# اختبار التغطية
pytest --cov=app tests/
```

## 📁 هيكل المشروع

```
GitHub-Auto-Builder/
├── backend/              # FastAPI Backend
│   ├── app/
│   │   ├── main.py       # Main application
│   │   ├── config.py     # Settings
│   │   ├── models/       # Database models
│   │   ├── routers/      # API endpoints
│   │   ├── tasks/        # Celery tasks
│   │   ├── middleware/   # Custom middleware
│   │   └── github/       # GitHub integration
│   ├── requirements.txt
│   ├── Dockerfile
│   └── alembic.ini
├── frontend/             # React Frontend
│   ├── src/
│   │   ├── App.js
│   │   ├── components/
│   │   └── pages/
│   ├── package.json
│   └── Dockerfile
├── database/             # Database migrations
├── docker-compose.yml    # Docker services
├── .env.example          # Environment template
└── README.md
```

## 🔗 API Endpoints

### Health
- `GET /api/health/` - فحص الصحة العامة
- `GET /api/health/database` - فحص قاعدة البيانات
- `GET /api/health/redis` - فحص Redis

### Webhooks
- `POST /api/webhooks/github` - استقبال GitHub webhooks
- `GET /api/webhooks/events` - قائمة الأحداث

### Repositories
- `GET /api/repositories/` - قائمة المستودعات
- `POST /api/repositories/` - إنشاء مستودع
- `GET /api/repositories/{id}` - تفاصيل مستودع
- `PUT /api/repositories/{id}` - تحديث مستودع

### Builds
- `GET /api/builds/` - قائمة عمليات البناء
- `GET /api/builds/{id}` - تفاصيل عملية بناء
- `GET /api/builds/statistics/summary` - إحصائيات

### Integrations
- `GET /api/integrations/` - قائمة التكاملات
- `POST /api/integrations/` - إنشاء تكامل
- `GET /api/integrations/platforms/supported` - المنصات المدعومة

## ⚙️ Configuration

### متغيرات البيئة المهمة

```bash
# قاعدة البيانات
DATABASE_URL=postgresql://builder:password@localhost:5432/github_builder

# Redis
REDIS_URL=redis://:password@localhost:6379/0

# GitHub Integration
GITHUB_APP_ID=your_app_id
GITHUB_PRIVATE_KEY_PATH=/path/to/private-key.pem
GITHUB_CLIENT_SECRET=your_client_secret
GITHUB_WEBHOOK_SECRET=your_webhook_secret

# OpenAI (للبحث الذكي)
OPENAI_API_KEY=your_openai_key

# CI Platform Tokens
CODEMAGIC_API_TOKEN=your_codemagic_token
CIRCLECI_TOKEN=your_circleci_token
```

### إعدادات الإصلاح التلقائي

```bash
AUTO_FIX_MAX_ATTEMPTS=3
AUTO_FIX_SAFE_TYPES=requirements.txt,package.json,pipfile,composer.json
AUTO_FIX_PRIMARY_BRANCH=main
```

## 🐛 استكشاف الأخطاء

### مشاكل شائعة

1. **خطأ في قاعدة البيانات**
   ```bash
   # إعادة تشغيل قاعدة البيانات
   docker-compose restart postgres
   
   # فحص اللوجات
   docker-compose logs postgres
   ```

2. **مشاكل Redis**
   ```bash
   # فحص حالة Redis
   docker-compose exec redis redis-cli ping
   ```

3. **مشاكل GitHub Webhooks**
   - تأكد من صحة `GITHUB_WEBHOOK_SECRET`
   - تأكد من أن الخادم متاح من الإنترنت
   - فحص اللوجات: `docker-compose logs backend`

### مراقبة النظام

```bash
# مراقبة الخدمات
docker-compose ps

# مراقبة الموارد
docker stats

# مراقبة اللوجات
docker-compose logs -f --tail=100
```

## 📊 المراقبة

###Flower Dashboard
- URL: http://localhost:5555
- مراقبة مهام Celery

### Database
- الاتصال: localhost:5432
- المستخدم: builder
- قاعدة البيانات: github_builder

### Logs
- Backend logs: `docker-compose logs backend`
- Frontend logs: `docker-compose logs frontend`
- Database logs: `docker-compose logs postgres`

## 🔒 الأمان

### Production Checklist
- [ ] تغيير جميع كلمات المرور الافتراضية
- [ ] إعداد HTTPS
- [ ] تكوين Firewall
- [ ] إعداد backups
- [ ] مراجعة صلاحيات قاعدة البيانات
- [ ] إعداد monitoring و alerts

### GitHub App Setup
1. إنشاء GitHub App
2. رفع مفتاح خاص
3. تكوين webhook URL
4. إعطاء الصلاحيات المطلوبة
5. تثبيت التطبيق على المستودعات

## 📚 المزيد من المعلومات

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [React Documentation](https://reactjs.org/)
- [Docker Documentation](https://docs.docker.com/)
- [GitHub API Documentation](https://docs.github.com/en/rest)
