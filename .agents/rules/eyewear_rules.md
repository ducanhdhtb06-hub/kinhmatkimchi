# 👓 QUY TẮC DỰ ÁN & TIÊU CHUẨN PHÁT TRIỂN (AGENTS.MD)
# DỰ ÁN: NỀN TẢNG THƯƠNG MẠI ĐIỆN TỬ BÁN KÍNH MẮT & COMPUTER VISION (OPTISTYLE PRO)

Tài liệu này định nghĩa toàn bộ quy tắc, tiêu chuẩn kiến trúc, phong cách lập trình và bảo mật mà mọi Agent / Lập trình viên phải tuân thủ khi phát triển và bảo trì dự án này.

---

## 1. TỔNG QUAN DỰ ÁN & MỤC TIÊU CỐT LÕI
* **Tên dự án:** OptiStyle Pro / Eyewear E-commerce & Computer Vision Platform.
* **Mục tiêu:** Xây dựng website bán kính mắt thông minh (gọng kính, kính râm, tròng kính cận/viễn/loạn/đổi màu) tích hợp các công nghệ Computer Vision tiên tiến (Thử kính ảo AR Virtual Try-On, Nhận diện dáng mặt, Đo khoảng cách đồng tử PD và Trích xuất phiếu khám mắt).
* **Trải nghiệm khách hàng:** Tối giản, sang trọng (Minimalist Luxury), chuẩn xác về mặt quang học và mượt mà trên cả thiết bị di động lẫn máy tính.

---

## 2. KIẾN TRÚC HỆ THỐNG & TECH STACK

### 2.1. Backend (Python / FastAPI)
* **Framework:** FastAPI (Python 3.12+).
* **Database:** SQLite với SQLAlchemy ORM (dễ triển khai, nhẹ, tự động sinh bảng và lưu trữ file `eyewear.db`).
* **Validation:** Pydantic Schemas cho toàn bộ request/response APIs.
* **Tổ chức thư mục chuẩn:**
  ```
  app/
  ├── database.py       # Kết nối DB & Session Management
  ├── models.py         # SQLAlchemy ORM Models (Product, Lens, Order, Customer, etc.)
  ├── schemas.py        # Pydantic Schemas xác thực dữ liệu
  ├── crud.py           # Database queries & Business Logic
  ├── seed.py           # Dữ liệu mẫu (Gọng kính, tròng kính, danh mục)
  ├── routes/
  │   ├── api.py        # REST API endpoints (Sản phẩm, Đơn hàng, CV tools)
  │   └── web.py        # Giao diện HTML (Jinja2 Templates)
  ├── static/           # CSS, JS, ảnh sản phẩm, assets gọng kính trong suốt
  └── templates/        # Giao diện người dùng (Storefront, Try-On, Admin, Cart)
  ```

### 2.2. Frontend & Giao diện (UI/UX)
* **CSS Framework:** Tailwind CSS (qua CDN hoặc build gọn nhẹ).
* **Typography:** Font chữ tiếng Việt hiện đại (`Be Vietnam Pro` hoặc `Inter`), hỗ trợ dấu tiếng Việt hoàn hảo.
* **Icons:** Lucide Icons & FontAwesome 6.
* **State & Reactive UI:** Alpine.js (nhẹ, trực quan, không cần build nặng).
* **Thông báo & Popup:** SweetAlert2.

### 2.3. Computer Vision & AR Architecture
* **AR Virtual Try-On:** Sử dụng **Google MediaPipe Face Mesh** chạy trực tiếp trên Client-side (trình duyệt).
  * **Quy tắc tuyệt đối:** Không gửi luồng video liên tục về server; toàn bộ việc bắt 468 điểm mốc khuôn mặt, tính toán tọa độ sống mũi và góc quay (Yaw, Pitch, Roll) thực hiện tại Client để đạt tốc độ 60 FPS và bảo mật quyền riêng tư cho khách hàng.
* **Mô hình Gọng kính:** Ưu tiên ảnh 2D PNG trong suốt độ nét cao (nhẹ, tải tức thì) và sẵn sàng mở rộng mô hình 3D (`.glb`/`Three.js`).
* **Đo khoảng cách đồng tử (PD) & Dáng mặt:** Áp dụng thuật toán tỷ lệ hình học trên các điểm landmark mắt và khung xương mặt.

---

## 3. QUY TẮC LẬP TRÌNH & CHẤT LƯỢNG CODE (CODE STANDARDS)

1. **Độc lập và Module hóa (Separation of Concerns):**
   - Logic truy vấn cơ sở dữ liệu phải nằm trong `crud.py`, không viết truy vấn thô trong route handlers.
   - Các API phải có schema Pydantic rõ ràng, không nhận dữ liệu không xác định.
2. **Xử lý lỗi & Thông báo thân thiện (Error Handling):**
   - Mọi lỗi ngoại lệ phải được bắt và trả về mã HTTP chuẩn (400, 404, 500) kèm thông điệp tiếng Việt dễ hiểu.
3. **Responsive Mobile-First:**
   - Người mua kính online sử dụng điện thoại chiếm >80%. Mọi màn hình (đặc biệt là giao diện Camera Thử Kính và Giỏ Hàng) bắt buộc phải hiển thị hoàn hảo trên màn hình cảm ứng dọc của smartphone.
4. **Hiệu năng & Tối ưu tải trang:**
   - Ảnh sản phẩm phải được tối ưu dung lượng.
   - MediaPipe scripts chỉ tải khi người dùng chủ động mở tính năng Thử kính / Phân tích khuôn mặt để tránh làm chậm trang chủ.

---

## 4. QUY TẮC BẢO MẬT & QUYỀN RIÊNG TƯ (SECURITY & PRIVACY)

1. **Quyền riêng tư Camera:**
   - Luôn xin phép người dùng rõ ràng trước khi truy cập Webcam/Camera.
   - Cung cấp phương án thay thế: Khách có thể chọn ảnh chân dung có sẵn hoặc chọn người mẫu mẫu nếu không muốn bật camera.
2. **Dữ liệu phiếu khám mắt (Prescription Data):**
   - Ảnh phiếu khám mắt và thông số cận/loạn của khách hàng phải được lưu trữ bảo mật và chỉ phục vụ mục đích gia công tròng kính cho đơn hàng đó.

---

## 5. QUY TRÌNH KIỂM THỬ TRƯỚC KHI BÀN GIAO (VERIFICATION CHECKLIST)
* [ ] Kiểm tra toàn bộ các routes API và trang web trả về HTTP 200 OK.
* [ ] Kiểm tra tính năng chọn gọng + chọn tròng + nhập số độ + tạo đơn hàng thành công.
* [ ] Kiểm tra tính năng Thử kính ảo (Virtual Try-On) căn chỉnh đúng sống mũi và co giãn theo kích thước mặt.
* [ ] Kiểm tra giao diện Admin quản lý đơn hàng và cập nhật trạng thái tròng kính.
