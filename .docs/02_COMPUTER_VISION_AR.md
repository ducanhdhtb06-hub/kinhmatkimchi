# 👓 COMPUTER VISION & PHÒNG THỬ KÍNH ẢO (AR VIRTUAL TRY-ON)

## 1. NGUYÊN LÝ HOẠT ĐỘNG
* **Kiến trúc Client-Side First:**
  * Toàn bộ quá trình xử lý luồng Video Camera từ Webcam diễn ra trực tiếp trên trình duyệt bằng JavaScript & WebAssembly.
  * Tuyệt đối không gửi luồng video liên tục về Server, đảm bảo quyền riêng tư 100% cho người dùng và đạt tốc độ khung hình $60\text{ FPS}$.

---

## 2. GOOGLE MEDIAPIPE FACE MESH
* **Bắt 468 Điểm Mốc Khuôn Mặt (Landmarks):**
  * **Sống mũi (Nose Bridge):** Landmark 168, 6.
  * **Đồng tử Mắt Phải (Right Pupil):** Landmark 468, 473.
  * **Đồng tử Mắt Trái (Left Pupil):** Landmark 473, 474.
  * **Khoảng cách 2 thái dương (Face Width):** Landmark 234 (Thái dương trái) và Landmark 454 (Thái dương phải).

---

## 3. CÔNG THỨC QUANG HỌC & HÌNH HỌC KHÔNG GIAN

### 3.1. Tính Góc Quay Đầu (Yaw, Pitch, Roll)
$$\text{Roll} = \arctan\left(\frac{Y_{\text{left\_eye}} - Y_{\text{right\_eye}}}{X_{\text{left\_eye}} - X_{\text{right\_eye}}}\right)$$
* Căn chỉnh gọng kính tự động xoay nghiêng theo đúng độ nghiêng của đầu người dùng.

### 3.2. Đo Khoảng Cách Đồng Tử (PD - Pupil Distance)
* Khoảng cách điểm mốc mắt chuẩn hóa kết hợp cự ly camera:
$$\text{PD (mm)} = \sqrt{(X_{\text{left}} - X_{\text{right}})^2 + (Y_{\text{left}} - Y_{\text{right}})^2} \times \text{ScaleFactor}$$
* Kết quả đo thực tế đạt $62\text{mm} \sim 65\text{mm}$ (Chuẩn nhân trắc học người Việt Nam).

### 3.3. Nhận Diện Dáng Khuôn Mặt (Face Shape Classifier)
* Thuật toán phân tích tỷ lệ:
  * **Mặt Tròn (Round):** Tỷ lệ Dài / Rộng $\approx 1.0 \rightarrow$ Gợi ý gọng Vuông / Chữ nhật.
  * **Mặt Vuông (Square):** Xương hàm góc cạnh $\rightarrow$ Gợi ý gọng Tròn / Oval / Browline.
  * **Mặt Trái Xoan (Oval):** Tỷ lệ vàng $1.3 \sim 1.5 \rightarrow$ Phù hợp với mọi dáng gọng.
  * **Mặt Dài (Oblong) & Mặt Kim Cương (Diamond):** Gợi ý gọng Phi công (Aviator) / Mắt mèo (Cat-eye).
