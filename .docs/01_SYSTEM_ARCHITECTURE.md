# 🏗️ KIẾN TRÚC HỆ THỐNG & TECH STACK (OPTISTYLE PRO)

## 1. TỔNG QUAN HỆ THỐNG
* **Tên nền tảng:** Kính Mắt Kim Chi (OptiStyle Pro)
* **Mô hình:** E-commerce Kính mắt thông minh kết hợp Computer Vision & Trí tuệ nhân tạo (AI).
* **Mục tiêu:** Cung cấp trải nghiệm mua sắm kính mắt trực tuyến hoàn chỉnh: Thử kính AR 3D, Đo thị lực AI tương tác bằng cử chỉ ngón tay, Bóc tách phiếu khám mắt tự động, và Thanh toán tự động VietQR.

---

## 2. TECH STACK & CẤU TRÚC BACKEND

### 2.1. Backend Framework
* **Ngôn ngữ & Runtime:** Python 3.12+
* **Web Framework:** FastAPI (Asynchronous REST API + Jinja2 Templates)
* **Cơ sở dữ liệu:** SQLite (`eyewear.db`) với SQLAlchemy ORM
* **Xác thực dữ liệu:** Pydantic v2 Schemas

### 2.2. Tổ chức thư mục
```
/home/anh/PycharmProjects/PythonProject/
├── app/
│   ├── database.py         # Kết nối SQLite & SessionLocal
│   ├── models.py           # SQLAlchemy ORM Models (User, Frame, Lens, Order, Voucher...)
│   ├── schemas.py          # Pydantic validation schemas
│   ├── crud.py             # Database CRUD & Business Logic
│   ├── seed.py             # Dữ liệu mẫu (Gọng kính, tròng kính, voucher...)
│   ├── routes/
│   │   ├── api.py          # REST APIs (Sản phẩm, Đơn hàng, CV, VietQR, Khám mắt)
│   │   └── web.py          # Web Pages & Template Rendering (Jinja2)
│   ├── static/             # CSS, JS, Ảnh sản phẩm gọng kính trong suốt
│   └── templates/          # Giao diện người dùng Tailwind CSS & Alpine.js
├── main.py                 # Entrypoint khởi chạy máy chủ Uvicorn
├── test_deep_suite.py      # Bộ kiểm thử tự động chuyên sâu (27/27 Test Cases)
└── test_system_full.py     # Bộ kiểm thử tích hợp toàn diện hệ thống
```

---

## 3. CƠ CHẾ BẢO MẬT & PHÂN QUYỀN (RBAC)
* **Quản trị viên (Admin):**
  * Quyền hạn: Toàn quyền quản lý gọng kính, tròng kính, đơn hàng, tạo voucher, cấu hình tài khoản VietQR và Telegram Bot.
  * Tài khoản mặc định: `ducanh2006` | Mật khẩu: `ducanh2006@`
* **Khách hàng (Customer):**
  * Quyền hạn: Thử kính AR, Đo thị lực, Lưu đơn kính vào Hồ sơ cá nhân, Đặt hàng, Áp mã giảm giá, Quản lý lịch sử đơn hàng.
  * Tài khoản mẫu: `khachhang@gmail.com` | Mật khẩu: `123456`
* **Khách vãng lai (Guest):**
  * Xem sản phẩm, thử kính AR, đo thị lực trực tiếp không bị chặn màn hình đăng nhập.
