# 🔐 دليل إنشاء Personal Access Token في GitHub

## الخطوة 1: الدخول لإعدادات GitHub

1. **افتح GitHub.com**
2. **انقر على صورة البروفايل** (أعلى يمين)
3. **اختر "Settings"**

## الخطوة 2: إنشاء Token

1. **في القائمة الجانبية، اختر:** `Developer settings`
2. **اختر:** `Personal access tokens`
3. **اختر:** `Tokens (classic)`
4. **انقر:** `Generate new token`
5. **اختر:** `Generate new token (classic)`

## الخطوة 3: إعدادات Token

```
Token name: AI Auto-Fix PWA Deploy
Expiration: 30 days (أو اختر المدة التي تريد)
```

## الخطوة 4: تحديد الصلاحيات (Scopes)

حدد هذه الصلاحيـات:
- ☑️ **repo** (Full control of private repositories)
- ☑️ **workflow** (Update GitHub Action workflows)
- ☑️ **admin:repo_hook** (Admin repo hooks)
- ☑️ **user** (Update ALL user data)
- ☑️ **delete_repo** (Delete repositories)
- ☑️ **write:discussion** (Write team discussions)
- ☑️ **write:enterprise** (Write enterprise data)

## الخطوة 5: إنشاء Token

1. **انقر:** `Generate token`
2. **انسخ Token فوراً** (لن يظهر مرة أخرى!)
3. **احفظه في مكان آمن**

## الخطوة 6: استخدام Token

```bash
# بدلاً من كلمة المرور، استخدم Token:
git clone https://github.com/raedthawaba/ai-autofix-pwa.git
cd ai-autofix-pwa

# انسخ جميع ملفات المشروع إلى هذا المجلد
# ثم:
git add .
git commit -m "Complete AI Auto-Fix PWA"
git push -u origin main

# عندما يطلب كلمة المرور:
# Username: raedthawaba
# Password: [ضع التوكن هنا]
```

## ✅ بهذه الطريقة:

- لا حاجة لتحميل ZIP
- لا حاجة لكلمة مرور GitHub
- رفع مباشر وسريع
- أكثر أماناً

**⚠️Important:** لا تشارك Token مع أحد!