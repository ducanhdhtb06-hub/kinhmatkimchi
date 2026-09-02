import os
import sys
from contextlib import asynccontextmanager

# Tự động nạp thư viện từ môi trường ảo .venv
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

try:
    from app.database import engine, Base, SessionLocal
    from app import seed
    from app.routes import api, web
except (ImportError, ModuleNotFoundError):
    from database import engine, Base, SessionLocal
    import seed
    from routes import api, web

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 1. Khởi tạo Database Tables (Categories, Frames, Lenses, Orders, OrderItems)
    try:
        Base.metadata.create_all(bind=engine)
        db = SessionLocal()
        try:
            seed.seed_eyewear_data(db)
        finally:
            db.close()
    except Exception as ex:
        print(f"⚠️ DB Init Notice: {ex}")

    # 2. Nạp trước mô hình OCR vào bộ nhớ RAM nếu khả dụng
    try:
        from app.ocr_service import _get_easyocr_reader
        _get_easyocr_reader()
    except Exception as ex:
        print(f"⚠️ Preload OCR: {ex}")

    yield

app = FastAPI(
    title="Kính Mắt Kim Chi - Eyewear E-commerce & Computer Vision",
    description="Nền tảng thương mại điện tử kính mắt thông minh tích hợp AR Virtual Try-On",
    version="2.0.0",
    lifespan=lifespan
)

# Static Files Directory
static_dir = os.path.join(current_dir, "static")
uploads_dir = os.path.join(static_dir, "uploads")
try:
    os.makedirs(uploads_dir, exist_ok=True)
except OSError:
    pass

if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Mount Routers
app.include_router(api.router)
app.include_router(web.router)

if __name__ == "__main__":
    import uvicorn
    print("=" * 70)
    print("🚀 Đang khởi động máy chủ Kính Mắt Kim Chi")
    print("👉 Mở trình duyệt và truy cập: http://localhost:8000")
    print("=" * 70)
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
