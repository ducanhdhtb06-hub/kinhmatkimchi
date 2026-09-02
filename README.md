# 👓 OptiStyle Pro - Nền Tảng Bán Kính Mắt Thông Minh & AR Virtual Try-On

Hệ thống thương mại điện tử chuyên biệt cho ngành kính mắt (Gọng kính, Kính mát, Tròng kính cận/viễn/loạn/đổi màu) tích hợp các công nghệ **Computer Vision & AR** tiên tiến.

---

## 🌟 Tính Năng Nổi Bật

### 1. 📸 Phòng Thử Kính Thực Tế Ảo (AR Virtual Try-On Studio)
* **Google MediaPipe Face Mesh (468 điểm mốc):** Chạy trực tiếp trên trình duyệt Client-side đạt tốc độ **60 FPS** mượt mà, bảo mật tuyệt đối, không cần GPU server đắt đỏ.
* **Tự động căn chỉnh quang học:** Tự động nhận diện sống mũi, xoay theo góc nghiêng đầu (Yaw, Pitch, Roll) và co giãn tỉ lệ gọng kính theo khoảng cách mắt.
* **Thử mẫu có sẵn hoặc tải ảnh:** Hỗ trợ cả Webcam trực tiếp, ảnh người mẫu mẫu (Nam/Nữ) hoặc tải ảnh chân dung cá nhân.

### 2. 👤 AI Nhận Diện Dáng Khuôn Mặt & Đo Khoảng Cách Đồng Tử (PD)
* **Phân tích hình học khuôn mặt:** Tự động phân loại dáng mặt (*Mặt Tròn, Vuông, Trái xoan, Dài, Kim Cương*) và đưa ra lời khuyên chọn gọng tương phản tôn dáng.
* **Đo khoảng cách đồng tử (PD - mm):** Hỗ trợ tính toán khoảng cách tâm 2 mắt để thợ quang học mài đúng tâm tròng kính.

### 3. 🔍 Bộ Cấu Hình Tròng Kính Chuyên Nghiệp (Lens Configurator)
* **Chọn loại tròng đa dạng:** Tròng 0 độ, Tròng chống ánh sáng xanh (Chemi 1.56), Tròng siêu mỏng (1.60 / 1.67 / 1.74 Essilor Pháp), Tròng đổi màu Transitions.
* **Nhập số độ chi tiết:** Mắt Phải (SPH, CYL, AXIS), Mắt Trái (SPH, CYL, AXIS), Khoảng cách đồng tử (PD).
* **Đính kèm phiếu khám:** Hỗ trợ tải ảnh chụp phiếu đo mắt của bác sĩ.

### 4. 🛒 Giỏ Hàng & Quy Trình Mua Kính Chuyên Biệt
* Tự động tổng hợp chi phí: `Giá gọng + Giá tròng = Tổng đơn`.
* Hỗ trợ thanh toán COD hoặc Chuyển khoản QR ngân hàng tự động.
* Mã theo dõi đơn hàng thời gian thực (ví dụ: `OPT-260901-XXXX`).

### 5. 🛡️ Trang Quản Trị Hệ Thống (Admin Dashboard)
* Thống kê KPI doanh thu, tổng số đơn, đơn chờ gia công mài tròng.
* Quản lý trạng thái đơn hàng: *Đang xử lý $\rightarrow$ Đang mài tròng $\rightarrow$ Đang giao $\rightarrow$ Hoàn tất*.
* Xem chi tiết thông số độ mắt và ảnh phiếu khám của khách hàng.
* Thêm / Xóa mẫu gọng kính mới trong kho.

---

## 🚀 Hướng Dẫn Khởi Chạy

### Khởi động từ PyCharm hoặc Terminal:
```bash
python main.py
```

### Các đường dẫn trải nghiệm chính:
* 🏠 **Trang chủ Cửa hàng:** [http://localhost:8000](http://localhost:8000)
* 📸 **Phòng Thử Kính AR Ảo & Phân Tích Dáng Mặt:** [http://localhost:8000/tryon](http://localhost:8000/tryon)
* 👓 **Bộ Sưu Tập Gọng Kính:** [http://localhost:8000/products](http://localhost:8000/products)
* 📦 **Tra Cứu Đơn Hàng:** [http://localhost:8000/orders/track](http://localhost:8000/orders/track)
* 🛡️ **Bảng Quản Trị Admin:** [http://localhost:8000/admin](http://localhost:8000/admin)

---

## 📁 Cấu Trúc Mã Nguồn (Clean Architecture)
```
.
├── app/
│   ├── database.py       # Cấu hình SQLite & Session factory
│   ├── models.py         # SQLAlchemy Models (Category, FrameProduct, LensProduct, Order, OrderItem)
│   ├── schemas.py        # Pydantic Schemas xác thực dữ liệu & CV payload
│   ├── crud.py           # Repository layer & Face shape recommendation logic
│   ├── seed.py           # Dữ liệu mẫu (Gọng kính, tròng kính chính hãng, đơn hàng)
│   ├── routes/
│   │   ├── api.py        # REST API endpoints
│   │   └── web.py        # Giao diện Web (Jinja2 Templates)
│   ├── static/
│   │   ├── js/tryon.js   # Computer Vision AR Engine (MediaPipe Face Mesh + Canvas)
│   │   ├── img/frames/   # Vector transparent glasses assets (Square, Round, Aviator, Cat-Eye, Browline)
│   │   └── uploads/      # Thư mục lưu trữ ảnh phiếu khám của khách
│   └── templates/        # Giao diện người dùng (Tailwind CSS, Alpine.js)
│       ├── base.html
│       ├── index.html
│       ├── products.html
│       ├── product_detail.html
│       ├── tryon.html
│       ├── cart.html
│       ├── checkout.html
│       ├── order_success.html
│       ├── order_track.html
│       └── admin.html
├── AGENTS.md             # Quy tắc dự án & tiêu chuẩn phát triển
├── main.py               # File chạy ứng dụng
└── eyewear.db            # Cơ sở dữ liệu SQLite
```
