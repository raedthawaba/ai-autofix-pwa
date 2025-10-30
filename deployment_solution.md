# حل مشكلة نشر المشروع على Vercel

## المشكلة الحالية
- اسم المشروع "ai-autofix-pwa" موجود بالفعل
- المستخدم يريد نشر مشروع PWA جديد

## الحل خطوة بخطوة

### الخطوة 1: حذف المشروع القديم
1. اذهب لـ Vercel Dashboard
2. ابحث عن مشروع "ai-autofix-pwa" 
3. اضغط على المشروع
4. اذهب لإعدادات المشروع (Settings)
5. احذف المشروع (Delete Project)

### الخطوة 2: إنشاء مشروع جديد
1. اضغط "New Project" 
2. اختر المستودع: raedthawaba/ai-autofix-pwa
3. اختر فرع: master
4. غير اسم المشروع إلى: ai-autofix-pwa-2025
5. Framework Preset: Other (اتركه كما هو)
6. Root Directory: (اتركه فارغاً - vercel.json سيتولى هذا)

### الخطوة 3: النشر
- اضغط "Deploy"
- انتظر حتى انتهاء عملية البناء
- ستظهر لك رابط الموقع المنشور

### لماذا هذا سيعمل؟
ملف vercel.json يحتوي على:
```json
{
  "buildCommand": "npm run build",
  "outputDirectory": "build", 
  "installCommand": "npm install",
  "rootDirectory": "frontend/",
  "framework": "react",
  "devCommand": "npm start",
  "functions": {"api/**": {"runtime": "nodejs18.x"}},
  "rewrites": [{"source": "/(.*)", "destination": "/index.html"}],
  "headers": [
    {"source": "/manifest.json", "headers": [{"key": "Content-Type", "value": "application/manifest+json"}]},
    {"source": "/sw.js", "headers": [{"key": "Content-Type", "value": "application/javascript"}]}
  ]
}
```

هذا الإعداد يخبر Vercel:
- مكان الكود: مجلد frontend/
- أمر البناء: npm run build
- نوع المشروع: React
- إعدادات PWA: ملفات Manifest و Service Worker

## النتيجة المتوقعة
- موقع PWA يعمل على الرابط: https://ai-autofix-pwa-2025.vercel.app
- إمكانية تثبيت التطبيق على الهاتف
- دعم العمل دون اتصال بالإنترنت
- راوتر React Router يعمل بشكل صحيح