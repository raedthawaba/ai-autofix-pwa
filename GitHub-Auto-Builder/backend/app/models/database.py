"""
إنشاء وإعداد قاعدة البيانات
"""
from . import Base, engine
from .user import User
from .repository import Repository
from .integration import Integration
from .build import Build
from .fix_attempt import FixAttempt
from .audit_log import AuditLog


def create_tables():
    """إنشاء جميع الجداول في قاعدة البيانات"""
    Base.metadata.create_all(bind=engine)


def drop_tables():
    """حذف جميع الجداول (للاختبار فقط)"""
    Base.metadata.drop_all(bind=engine)


def reset_database():
    """إعادة تعيين قاعدة البيانات (حذف ثم إنشاء)"""
    drop_tables()
    create_tables()


def check_tables_exist() -> bool:
    """التحقق من وجود الجداول"""
    try:
        from sqlalchemy import inspect
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        expected_tables = [
            'users', 'repositories', 'integrations', 
            'builds', 'fix_attempts', 'audit_logs'
        ]
        return all(table in tables for table in expected_tables)
    except Exception:
        return False


def get_table_info() -> dict:
    """الحصول على معلومات الجداول"""
    try:
        from sqlalchemy import inspect, text
        inspector = inspect(engine)
        
        info = {
            "tables": {},
            "total_tables": 0,
            "connected": True
        }
        
        for table_name in inspector.get_table_names():
            columns = inspector.get_columns(table_name)
            indexes = inspector.get_indexes(table_name)
            
            info["tables"][table_name] = {
                "columns": [
                    {
                        "name": col["name"],
                        "type": str(col["type"]),
                        "nullable": col.get("nullable", True),
                        "primary_key": col.get("primary_key", False)
                    }
                    for col in columns
                ],
                "indexes": [
                    {
                        "name": idx["name"],
                        "columns": idx["column_names"]
                    }
                    for idx in indexes
                ],
                "column_count": len(columns)
            }
        
        info["total_tables"] = len(info["tables"])
        return info
        
    except Exception as e:
        return {
            "connected": False,
            "error": str(e),
            "tables": {},
            "total_tables": 0
        }


# إنشاء الجداول عند استيراد الملف
if __name__ == "__main__":
    print("إنشاء جداول قاعدة البيانات...")
    create_tables()
    print("تم إنشاء الجداول بنجاح!")
    
    # عرض معلومات الجداول
    info = get_table_info()
    print(f"\nمعلومات قاعدة البيانات:")
    print(f"- الاتصال: {'نجح' if info['connected'] else 'فشل'}")
    print(f"- عدد الجداول: {info['total_tables']}")
    
    if info['connected']:
        print("\nالجداول الموجودة:")
        for table_name, table_info in info['tables'].items():
            print(f"- {table_name}: {table_info['column_count']} عمود")
