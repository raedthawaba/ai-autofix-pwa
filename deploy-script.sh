#!/bin/bash

# 🚀 Script سريع لرفع AI Auto-Fix PWA على GitHub

echo "🔧 تجهيز رفع AI Auto-Fix PWA على GitHub..."

# تنظيف المشروع
echo "🧹 تنظيف الملفات المؤقتة..."
find . -name "node_modules" -type d -exec rm -rf {} + 2>/dev/null || true
find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
find . -name ".git" -type d -exec rm -rf {} + 2>/dev/null || true
find . -name "*.pyc" -delete 2>/dev/null || true

# إنشاء .env
echo "⚙️ إنشاء ملف البيئة..."
cat > .env << 'EOF'
# AI Auto-Fix PWA Environment Configuration
# موقع البيانات
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/aiautofix
REDIS_URL=redis://localhost:6379/0

# GitHub Integration
GITHUB_TOKEN=ghp_your_github_token_here
GITHUB_WEBHOOK_SECRET=your_webhook_secret_here
GITHUB_APP_ID=your_github_app_id
GITHUB_CLIENT_SECRET=your_client_secret

# OpenAI API
OPENAI_API_KEY=sk-your-openai-api-key

# Security
JWT_SECRET_KEY=your-super-secret-jwt-key-here
SECRET_KEY=your-secret-key-here

# Notifications
SLACK_WEBHOOK_URL=https://hooks.slack.com/your-webhook
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password

# CI/CD Platforms
CODEMAGIC_API_TOKEN=your_codemagic_token
CIRCLECI_TOKEN=your_circleci_token
BITRISE_TOKEN=your_bitrise_token
EOF

echo "📦 إضافة ملفات المشروع..."
git init
git add .
git commit -m "Initial PWA commit - AI Auto-Fix"

# إعداد Remote
echo "🔗 ربط بـ GitHub..."
git remote add origin https://github.com/raedthawaba/ai-autofix-pwa.git
git branch -M main

echo "✅ تم تجهيز المشروع!"
echo ""
echo "🔑 للحصول على GitHub Personal Access Token:"
echo "1. اذهب إلى GitHub.com → Settings → Developer settings"
echo "2. اختر Personal access tokens → Tokens (classic)"
echo "3. اضغط Generate new token (classic)"
echo "4. اختر الصلاحيـات: repo, workflow, admin:repo_hook"
echo "5. انسخ التوكن واستخدمه كـ كلمة مرور"
echo ""
echo "🚀 لرفع الكود:"
echo "git push -u origin main"
echo ""
echo "📝 عند طلب كلمة المرور:"
echo "Username: raedthawaba"
echo "Password: [ضع التوكن هنا]"
echo ""
echo "🎉 بعدها رابط التطبيق سيكون:"
echo "https://ai-autofix-pwa.vercel.app (بعد ربط Vercel)"