import os
import sys

# Tự động nạp thư viện từ môi trường ảo .venv
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

venv_lib_dir = os.path.join(project_root, ".venv", "lib")
if os.path.exists(venv_lib_dir):
    for item in os.listdir(venv_lib_dir):
        if item.startswith("python"):
            sp = os.path.join(venv_lib_dir, item, "site-packages")
            if os.path.exists(sp) and sp not in sys.path:
                sys.path.insert(0, sp)

snap_sp = "/home/anh/snap/antigravity-cli/common/lib/python3.12/site-packages"
if os.path.exists(snap_sp) and snap_sp not in sys.path:
    sys.path.insert(0, snap_sp)

from contextlib import asynccontextmanager
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
    Base.metadata.create_all(bind=engine)
    
    # 2. Khởi tạo dữ liệu mẫu nếu DB trống
    db = SessionLocal()
    try:
        seed.seed_eyewear_data(db)
    finally:
        db.close()

    # 3. Nạp trước mô hình OCR vào bộ nhớ RAM (Preload OCR Engine) để phản hồi tức thì
    try:
        from app.ocr_service import _get_easyocr_reader
        _get_easyocr_reader()
        print("⚡ Mô hình OCR Pre-trained đã sẵn sàng phản hồi siêu tốc (< 1.5s)!")
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
os.makedirs(uploads_dir, exist_ok=True)

if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Mount Routers
app.include_router(api.router)
app.include_router(web.router)

if __name__ == "__main__":
    import uvicorn
    print("=" * 70)
    print("🚀 Đang khởi động máy chủ Kính Mắt Kim Chi từ app/main.py")
    print("👉 Mở trình duyệt và truy cập: http://localhost:8000")
    print("👉 Phòng Thử Kính AR Ảo:       http://localhost:8000/tryon")
    print("👉 Bảng Quản Trị Hệ Thống:     http://localhost:8000/admin")
    print("=" * 70)
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
