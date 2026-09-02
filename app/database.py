import os
import shutil
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# Môi trường Serverless (Vercel) có hệ thống tệp chỉ đọc (Read-only) ngoại trừ /tmp
if os.environ.get("VERCEL") or os.environ.get("AWS_LAMBDA_FUNCTION_NAME"):
    db_path = "/tmp/eyewear.db"
    orig_db = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "eyewear.db")
    if os.path.exists(orig_db) and not os.path.exists(db_path):
        try:
            shutil.copyfile(orig_db, db_path)
        except Exception:
            pass
    DATABASE_URL = f"sqlite:///{db_path}"
else:
    DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./eyewear.db")

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=False
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
