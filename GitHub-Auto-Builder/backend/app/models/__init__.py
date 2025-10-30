"""
نماذج قاعدة البيانات
"""
from sqlalchemy import create_engine, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from ..config import settings

# إنشاء engine قاعدة البيانات
engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    pool_recycle=300,
    echo=settings.debug
)

# إنشاء SessionLocal
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# إنشاء Base للنماذج
Base = declarative_base()

# إنشاء metadata
metadata = MetaData()


def get_db():
    """الحصول على session قاعدة البيانات"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
