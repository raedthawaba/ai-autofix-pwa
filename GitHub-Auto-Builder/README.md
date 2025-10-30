# AI Auto-Fix - Progressive Web App 🚀

> **تطبيق ويب متقدم لأتمتة الربط مع GitHub وتشغيل البناء وإصلاح الأخطاء تلقائياً**

[![PWA](https://img.shields.io/badge/PWA-Ready-blue.svg)](https://developers.google.com/web/progressive-web-apps)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Arabic](https://img.shields.io/badge/Language-Arabic-blue.svg)](README.md)

## ✨ الميزات الرئيسية

### 🔗 **تكامل GitHub المتقدم**
- ربط تلقائي مع مستودعات GitHub
- مراقبة الأحداث في الوقت الفعلي
- إدارة الفروع والـ Pull Requests تلقائياً

### 🚀 **تشغيل البناء على منصات CI/CD**
- دعم GitHub Actions
- دعم Codemagic
- دعم CircleCI
- واجهة موحدة لإدارة جميع المنصات

### 🤖 **إصلاح الأخطاء بالذكاء الاصطناعي**
- تحليل الأخطاء تلقائياً
- اقتراح حلول ذكية
- إنشاء Pull Requests بالتصحيحات
- تعلم من الأخطاء السابقة

### 📱 **تطبيق PWA متقدم**
- قابل للتثبيت على جميع الأجهزة
- يعمل بدون اتصال إنترنت
- أداء سريع ومحسن للموبايل
- إشعارات push
- تحديثات تلقائية

## 🎯 التثبيت السريع

### المتطلبات
- Node.js 18+ 
- Python 3.11+
- Docker & Docker Compose
- GitHub Personal Access Token

### 1. تحميل المشروع
```bash
git clone https://github.com/YOUR_USERNAME/ai-autofix-pwa.git
cd ai-autofix-pwa
```

### 2. إعداد البيئة
```bash
# نسخ ملف البيئة
cp .env.example .env

# تحرير المفاتيح
nano .env
```

**المتغيرات المطلوبة في `.env`:**
```bash
# GitHub
GITHUB_TOKEN=ghp_your_github_token_here
GITHUB_WEBHOOK_SECRET=your_webhook_secret_here

# قاعدة البيانات
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/aiautofix
REDIS_URL=redis://localhost:6379/0

# الأمان
JWT_SECRET_KEY=your-super-secret-jwt-key

# OpenAI (اختياري)
OPENAI_API_KEY=sk-your-openai-api-key
```

### 3. تشغيل النظام
```bash
python run.py start
```

### 4. الوصول للتطبيق
- **الويب**: http://localhost:3000
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

## 📱 تثبيت PWA على الجهاز

### على الهاتف المحمول (Android/iOS)
1. افتح المتصفح واذهب إلى http://your-domain.com
2. اضغط على زر "تثبيت" في شريط العنوان
3. اضغط "تثبيت" لتأكيد العملية
4. ستجد التطبيق في قائمة التطبيقات

### على الكمبيوتر (Chrome/Edge)
1. اضغط على أيقونة التثبيت في شريط العنوان
2. أو اذهب إلى قائمة Chrome → "تثبيت AI Auto-Fix"
3. سيتم تثبيت التطبيق في قائمة التطبيقات

## 🏗️ بنية المشروع

```
ai-autofix-pwa/
├── 📁 frontend/                 # React PWA Frontend
│   ├── 📁 public/               # PWA Files
│   │   ├── manifest.json        # PWA Manifest
│   │   ├── sw.js               # Service Worker
│   │   ├── offline.html        # Offline Page
│   │   └── 📁 icons/           # PWA Icons
│   ├── 📁 src/                 # React Components
│   └── workbox-config.js       # PWA Configuration
├── 📁 backend/                 # FastAPI Backend
│   ├── 📁 app/                 # API Routes & Logic
│   ├── 📁 models/              # Database Models
│   └── 📁 tasks/               # Background Tasks
├── 📁 database/                # Database Migrations
├── 📁 tests/                   # Test Suite
├── 📄 docker-compose.yml       # Container Setup
├── 📄 .env.example            # Environment Template
└── 📄 run.py                  # Management Script
```

## 🔥 ميزات PWA المتقدمة

### 🏠 **الوضع المتصل/غير المتصل**
- يعمل بدون إنترنت للوظائف الأساسية
- تزامن تلقائي عند الاتصال
- عرض حالة الاتصال في الوقت الفعلي

### 📢 **الإشعارات الذكية**
- إشعارات بناء جديدة
- تذكيرات بـ Pull Requests
- تحديثات حالة الأخطاء

### ⚡ **الأداء المحسن**
- تخزين مؤقت ذكي
- تحميل فوري للصفحات
- تحديثات في الخلفية

### 🔒 **الأمان**
- تشفير البيانات المحلية
- تحقق من الصحة
- حماية ضد XSS

## 🎮 دليل الاستخدام

### 1. ربط مستودع GitHub
```javascript
// مثال على ربط مستودع جديد
const response = await fetch('/api/repositories', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${token}`
  },
  body: JSON.stringify({
    owner: 'username',
    name: 'repository-name'
  })
});
```

### 2. مراقبة البناء
```javascript
// الاشتراك في إشعارات البناء
navigator.serviceWorker.ready.then(registration => {
  registration.pushManager.subscribe({
    userVisibleOnly: true,
    applicationServerKey: yourVapidPublicKey
  });
});
```

### 3. عرض حالة الأخطاء
```javascript
// جلب الأخطاء المرتبطة بالمشروع
const response = await fetch('/api/builds?status=failed');
const builds = await response.json();
```

## 🛠️ التطوير والمساهمة

### تشغيل بيئة التطوير
```bash
# تشغيل الـ backend
cd backend
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# تشغيل الـ frontend (terminal آخر)
cd frontend
npm start
```

### بناء PWA للإنتاج
```bash
npm run build
npm run build:pwa
```

### تشغيل الاختبارات
```bash
python run.py test
```

## 📊 المراقبة والإحصائيات

- **API Health**: `GET /health`
- **Database Status**: `GET /health/database`
- **Queue Status**: `GET /health/queue`
- **PWA Status**: `GET /api/pwa/status`

## 🌐 النشر للإنتاج

### Docker Deployment
```bash
docker-compose -f docker-compose.prod.yml up -d
```

### مع AWS/Azure
```bash
# استخدام Docker registry
docker tag ai-autofix:latest your-registry/ai-autofix:latest
docker push your-registry/ai-autofix:latest
```

## 🔧 استكشاف الأخطاء

### مشاكل شائعة

**البوابة لا تفتح**
```bash
# تحقق من الخدمات
python run.py health

# تحقق من logs
python run.py logs
```

**PWA لا يظهر زر التثبيت**
- تأكد من تشغيل الموقع عبر HTTPS
- تحقق من صحة manifest.json
- تأكد من تسجيل service worker

**لا تعمل الإشعارات**
- تحقق من أذونات المتصفح
- تأكد من تسجيل service worker
- تحقق من service worker logs

## 📄 الترخيص

هذا المشروع مرخص تحت رخصة MIT - راجع ملف [LICENSE](LICENSE) للتفاصيل.

## 🤝 المساهمة

نرحب بمساهماتكم! يرجى مراجعة [دليل المساهمة](CONTRIBUTING.md) للتفاصيل.

## 📞 الدعم

- **الأسئلة**: [GitHub Issues](https://github.com/YOUR_USERNAME/ai-autofix-pwa/issues)
- **الوثائق**: [Wiki](https://github.com/YOUR_USERNAME/ai-autofix-pwa/wiki)
- **المجتمع**: [Discord](https://discord.gg/your-server)

## 🏆 الشكر والتقدير

- **React Team** - إطار العمل الرائع
- **FastAPI Team** - API Framework السريع
- **Workbox Team** - PWA Optimization
- **GitHub API** - التكامل الأساسي
- **OpenAI** - تحسينات الذكاء الاصطناعي

---

<div align="center">

**تم التطوير بـ ❤️ باستخدام أحدث التقنيات**

[ابدأ الآن](https://github.com/YOUR_USERNAME/ai-autofix-pwa) | [عرض التوثيق](docs/) | [ابلغ عن مشكلة](https://github.com/YOUR_USERNAME/ai-autofix-pwa/issues)

</div>
