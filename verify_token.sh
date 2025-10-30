#!/bin/bash

# GitHub Token Verification Script
# هذا السكريبت يساعد في التحقق من صحة التوكن

echo "🔐 GitHub Token Verification Tool"
echo "=================================="
echo

# طلب التوكن من المستخدم
read -p "أدخل التوكن الجديد (سيكون مخفياً): " -s TOKEN
echo
echo "🔍 جاري التحقق من التوكن..."

# اختبار التوكن
RESPONSE=$(curl -s -w "\n%{http_code}" \
  -H "Authorization: token $TOKEN" \
  -H "Accept: application/vnd.github.v3+json" \
  https://api.github.com/user)

# استخراج HTTP code
HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
RESPONSE_BODY=$(echo "$RESPONSE" | head -n-1)

if [ "$HTTP_CODE" = "200" ]; then
    echo "✅ التوكن صحيح ويعمل بنجاح!"
    
    # عرض معلومات المستخدم
    USERNAME=$(echo "$RESPONSE_BODY" | grep '"login"' | cut -d'"' -f4)
    echo "👤 المستخدم: $USERNAME"
    echo
    
    # اختبار صلاحيات المستودع
    echo "🔍 جاري اختبار صلاحيات المستودع..."
    REPO_RESPONSE=$(curl -s -w "\n%{http_code}" \
      -H "Authorization: token $TOKEN" \
      -H "Accept: application/vnd.github.v3+json" \
      https://api.github.com/repos/raedthawaba/ai-autofix-pwa)
    
    REPO_HTTP_CODE=$(echo "$REPO_RESPONSE" | tail -n1)
    
    if [ "$REPO_HTTP_CODE" = "200" ]; then
        echo "✅ لديك صلاحيات للوصول للمستودع!"
        echo
        echo "🚀 جاهز للرفع! التوكن محفوظ ومتوفر."
        echo "الآن يمكن رفع الكود إلى GitHub."
        export GITHUB_TOKEN=$TOKEN
        echo "TOKEN_SAVED=true" > token_status.txt
    else
        echo "⚠️ لا يمكن الوصول للمستودع. تحقق من صلاحيات التوكن."
        echo "HTTP Code: $REPO_HTTP_CODE"
        exit 1
    fi
    
else
    echo "❌ التوكن غير صحيح أو منتهي الصلاحية!"
    echo "HTTP Code: $HTTP_CODE"
    echo "الرسالة: $RESPONSE_BODY"
    exit 1
fi