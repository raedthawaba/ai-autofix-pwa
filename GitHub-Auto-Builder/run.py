#!/usr/bin/env python3
"""
نص تشغيل GitHub Auto Builder
سهل الاستخدام لتشغيل النظام في وضع التطوير أو الإنتاج
"""
import os
import sys
import subprocess
import argparse
import time
import signal


class GitHubBuilderRunner:
    def __init__(self):
        self.docker_compose_file = "docker-compose.yml"
        self.project_name = "github-builder"
    
    def check_requirements(self):
        """فحص المتطلبات"""
        print("🔍 فحص المتطلبات...")
        
        # فحص Docker
        try:
            subprocess.run(["docker", "--version"], check=True, capture_output=True)
            print("✅ Docker متوفر")
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("❌ Docker غير مثبت أو غير متوفر")
            return False
        
        # فحص Docker Compose
        try:
            subprocess.run(["docker-compose", "--version"], check=True, capture_output=True)
            print("✅ Docker Compose متوفر")
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("❌ Docker Compose غير مثبت أو غير متوفر")
            return False
        
        # فحص ملف البيئة
        if not os.path.exists(".env"):
            print("⚠️  ملف .env غير موجود - سيتم نسخ .env.example")
            self.create_env_file()
        
        print("✅ جميع المتطلبات متوفرة")
        return True
    
    def create_env_file(self):
        """إنشاء ملف .env من النموذج"""
        if os.path.exists(".env.example"):
            import shutil
            shutil.copy(".env.example", ".env")
            print("📋 تم إنشاء ملف .env من النموذج")
            print("⚠️  يرجى تعديل ملف .env بإعداداتك")
        else:
            print("❌ ملف .env.example غير موجود")
    
    def start_services(self, detach=True):
        """تشغيل الخدمات"""
        print("🚀 بدء تشغيل الخدمات...")
        
        cmd = ["docker-compose", "-p", self.project_name, "up", "-d"]
        
        try:
            if detach:
                subprocess.run(cmd, check=True)
                print("✅ تم تشغيل جميع الخدمات")
            else:
                subprocess.run(cmd, check=True)
            
            self.wait_for_services()
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"❌ خطأ في تشغيل الخدمات: {e}")
            return False
    
    def stop_services(self):
        """إيقاف الخدمات"""
        print("🛑 إيقاف الخدمات...")
        
        try:
            subprocess.run([
                "docker-compose", "-p", self.project_name, "down"
            ], check=True)
            print("✅ تم إيقاف جميع الخدمات")
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"❌ خطأ في إيقاف الخدمات: {e}")
            return False
    
    def restart_services(self):
        """إعادة تشغيل الخدمات"""
        print("🔄 إعادة تشغيل الخدمات...")
        
        self.stop_services()
        time.sleep(2)
        return self.start_services()
    
    def show_logs(self, service=None, tail=100):
        """عرض اللوجات"""
        print("📋 عرض اللوجات...")
        
        cmd = ["docker-compose", "-p", self.project_name, "logs"]
        
        if service:
            cmd.append(service)
        
        if tail:
            cmd.extend(["--tail", str(tail)])
        
        cmd.append("-f")
        
        try:
            subprocess.run(cmd)
        except KeyboardInterrupt:
            print("\n🛑 تم إيقاف عرض اللوجات")
        except subprocess.CalledProcessError as e:
            print(f"❌ خطأ في عرض اللوجات: {e}")
    
    def check_health(self):
        """فحص صحة النظام"""
        print("🏥 فحص صحة النظام...")
        
        # فحص الخدمات
        try:
            result = subprocess.run([
                "docker-compose", "-p", self.project_name, "ps"
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                print("✅ حالة الخدمات:")
                print(result.stdout)
            else:
                print("❌ خطأ في فحص حالة الخدمات")
                return False
                
        except subprocess.CalledProcessError:
            print("❌ خطأ في تنفيذ أمر docker-compose")
            return False
        
        # فحص API
        try:
            import requests
            response = requests.get("http://localhost:8000/api/health", timeout=10)
            
            if response.status_code == 200:
                print("✅ API يعمل بشكل طبيعي")
                data = response.json()
                print(f"📊 حالة النظام: {data.get('status', 'unknown')}")
                return True
            else:
                print(f"⚠️  API يعطي رمز حالة: {response.status_code}")
                return False
                
        except requests.RequestException:
            print("❌ لا يمكن الوصول إلى API")
            return False
        except ImportError:
            print("⚠️  مكتبة requests غير متوفرة - تخطي فحص API")
            return True
    
    def wait_for_services(self, timeout=120):
        """انتظار جاهزية الخدمات"""
        print("⏳ انتظار جاهزية الخدمات...")
        
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                import requests
                response = requests.get("http://localhost:8000/api/health", timeout=5)
                
                if response.status_code == 200:
                    print("✅ الخدمات جاهزة")
                    return True
                    
            except requests.RequestException:
                pass
            
            print("⏳ الخدمات قيد التحضير...")
            time.sleep(5)
        
        print("⚠️  انتهت مهلة الانتظار - الخدمات قد تكون جاهزة")
        return False
    
    def run_tests(self):
        """تشغيل الاختبارات"""
        print("🧪 تشغيل الاختبارات...")
        
        try:
            # تشغيل اختبارات Backend
            os.chdir("backend")
            subprocess.run(["python", "-m", "pytest", "tests/", "-v"], check=True)
            os.chdir("..")
            
            print("✅ جميع الاختبارات نجحت")
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"❌ فشل في الاختبارات: {e}")
            return False
        except FileNotFoundError:
            print("⚠️  pytest غير متوفر - تخطي الاختبارات")
            return True
    
    def show_status(self):
        """عرض حالة النظام"""
        print("📊 حالة النظام:")
        
        # حالة Docker containers
        try:
            subprocess.run([
                "docker-compose", "-p", self.project_name, "ps"
            ])
        except subprocess.CalledProcessError:
            print("❌ خطأ في فحص حالة الحاويات")
    
    def show_urls(self):
        """عرض روابط النظام"""
        print("🔗 روابط النظام:")
        print("📚 API Documentation: http://localhost:8000/docs")
        print("🌐 Frontend Dashboard: http://localhost:3000")
        print("📊 Task Monitoring: http://localhost:5555")
        print("🏥 Health Check: http://localhost:8000/api/health")
        print("🔍 API Info: http://localhost:8000/api")


def main():
    parser = argparse.ArgumentParser(
        description="GitHub Auto Builder - Runner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
أمثلة الاستخدام:
  python run.py start        # تشغيل النظام
  python run.py stop         # إيقاف النظام
  python run.py restart      # إعادة تشغيل النظام
  python run.py logs         # عرض اللوجات
  python run.py health       # فحص صحة النظام
  python run.py test         # تشغيل الاختبارات
  python run.py status       # عرض حالة النظام
  python run.py urls         # عرض روابط النظام
        """
    )
    
    parser.add_argument(
        "command",
        choices=["start", "stop", "restart", "logs", "health", "test", "status", "urls"],
        help="الأمر المراد تنفيذه"
    )
    
    parser.add_argument(
        "--service",
        help="خدمة محددة للوجات"
    )
    
    parser.add_argument(
        "--tail",
        type=int,
        default=100,
        help="عدد أسطر اللوجات للعرض"
    )
    
    args = parser.parse_args()
    
    runner = GitHubBuilderRunner()
    
    # معالج Ctrl+C
    def signal_handler(sig, frame):
        print("\n🛑 تم إيقاف التشغيل")
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    
    if args.command == "start":
        if runner.check_requirements():
            if runner.start_services():
                runner.show_urls()
            else:
                sys.exit(1)
    
    elif args.command == "stop":
        runner.stop_services()
    
    elif args.command == "restart":
        runner.restart_services()
        runner.show_urls()
    
    elif args.command == "logs":
        runner.show_logs(args.service, args.tail)
    
    elif args.command == "health":
        runner.check_health()
    
    elif args.command == "test":
        if runner.check_requirements():
            runner.run_tests()
    
    elif args.command == "status":
        runner.show_status()
    
    elif args.command == "urls":
        runner.show_urls()


if __name__ == "__main__":
    main()
