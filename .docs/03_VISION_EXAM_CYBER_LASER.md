# ⚡ BÁC SĨ MẮT AI & CYBER LASER TRACKING ENGINE v5.0

## 1. NGUYÊN LÝ KHÁM THỊ LỰC QUANG HỌC
* **Chuẩn Y Khoa:** Bảng thị lực Snellen Tumbling E tương đương LogMAR ở cự ly **1.0 Mét**.
* **Quy trình 4 Bước:**
  1. **Bước 1 (Căn chỉnh cự ly):** Thước đo cự ly $1.0\text{m}$ và độ cao ngang tầm mắt.
  2. **Bước 2 (Đo độ sắc nét Tumbling E):** 6 cấp độ thị lực ($2/10, 4/10, 6/10, 8/10, 10/10, 12/10$) với kích thước chữ E thu nhỏ từ $140\text{px} \rightarrow 22\text{px}$.
  3. **Bước 3 (Kiểm tra Loạn thị):** Biểu đồ Nan quạt tỏa tròn (Astigmatism Fan Chart).
  4. **Bước 4 (Báo cáo & Đơn kính AI):** Tính toán độ cầu $SPH$, độ loạn $CYL$, trục $AXIS$, khoảng cách đồng tử $PD$ và tự động đồng bộ vào Hồ sơ cá nhân.

---

## 2. CYBER LASER FINGERTIP TRACKING (60 FPS)

### 2.1. Đa Tầng Nhận Diện (Tri-Engine Architecture)
1. **Engine 1 - AI Landmark Tracking:** Bắt điểm đỉnh ngón trỏ (`Landmark 8`).
2. **Engine 2 - Dense Optical Fingertip Extrema:**
   * Quét ma trận điểm ảnh độ phân giải $160 \times 120$ ngoài vùng khuôn mặt.
   * Lọc sắc độ da (Skin Chrominance) và tìm đỉnh cực trị ngón tay trỏ trong $<1\text{ms}$.
3. **Bộ lọc làm mượt (EMA Smoother):**
   $$P_{\text{smooth}}(t) = P_{\text{smooth}}(t-1) + \alpha \cdot (P_{\text{raw}}(t) - P_{\text{smooth}}(t-1)) \quad (\alpha = 0.65)$$
   * Loại bỏ hoàn toàn độ rung giật, cho chuyển động êm ái như con trỏ Laser quang học thực tế.

### 2.2. Hiệu Ứng Thị Giác Hologram (Visual Laser FX)
* **Tâm ngắm Radar Hologram:** Vòng tròn Neon phát sáng bám chặt đỉnh ngón tay trỏ.
* **Vệt hạt sáng (Particle Sparks Trail):** Hiển thị vệt hạt mờ dần theo quỹ đạo di chuyển của ngón tay.
* **Tia Laser Đa Lớp (Laser Cannon):** Lõi Laser trắng sáng + quầng sáng vàng hổ phách phóng từ ngón tay đến 4 cổng mục tiêu (👈 **TRÁI**, 👉 **PHẢI**, ☝️ **LÊN**, 👇 **XUỐNG**).
* **Khóa mục tiêu (Magnetic Lock-On):** Giữ hướng ngón tay trong $280\text{ms}$ $\rightarrow$ Thanh năng lượng sạc đầy $100\%$ và kích hoạt âm thanh xác nhận!

### 2.3. Âm Thanh Tổng Hợp Web Audio Synth
* **Tiếng sạc Laser:** Tần số sóng Sine quét từ $400\text{Hz} \rightarrow 880\text{Hz}$.
* **Tiếng kích nổ Plasma ("Zaaap-Ding"):** Tần số quét tức thì từ $587\text{Hz} \rightarrow 1174\text{Hz}$.
