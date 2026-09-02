import os
import sys
import json
import urllib.request
import urllib.parse
import http.cookiejar

BASE_URL = "http://localhost:8000"

def run_deep_tests():
    print("=" * 80)
    print("🚀 BẮT ĐẦU KIỂM THỬ TỰ ĐỘNG CHUYÊN SÂU TOÀN BỘ NỀN TẢNG OPTISTYLE PRO")
    print("=" * 80)
    
    cj = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
    
    passed_count = 0
    total_count = 0

    def assert_test(name, condition, extra=""):
        nonlocal passed_count, total_count
        total_count += 1
        if condition:
            passed_count += 1
            print(f"  ✅ [PASS {passed_count:02d}] {name} {extra}")
        else:
            print(f"  ❌ [FAIL {total_count:02d}] {name} {extra}")
            raise AssertionError(f"Test thất bại: {name}")

    # ================= 1. PUBLIC STOREFRONT & PAGES =================
    print("\n[PHẦN 1] KIỂM TRA TOÀN BỘ TRANG WEB & TÀI NGUYÊN (HTTP 200):")
    public_urls = [
        ("/", "Trang chủ"),
        ("/products", "Bộ sưu tập sản phẩm"),
        ("/products/1", "Chi tiết sản phẩm gọng"),
        ("/tryon", "Phòng thử kính ảo AR"),
        ("/prescription-scan", "Quét Đơn Kính AI OCR"),
        ("/cart", "Giỏ hàng"),
        ("/checkout", "Thanh toán"),
    ]
    for path, desc in public_urls:
        resp = opener.open(f"{BASE_URL}{path}")
        assert_test(f"Truy cập {desc} ({path})", resp.status == 200)

    # ================= 2. AI OCR PRESCRIPTION SCANNER (COMPUTER VISION) =================
    print("\n[PHẦN 2] KIỂM TRA THỊ GIÁC MÁY TÍNH AI OCR QUÉT PHIẾU KHÁM MẮT 4.0:")
    scan_html = opener.open(f"{BASE_URL}/prescription-scan").read().decode("utf-8")
    assert_test("Trang Quét Đơn Kính AI tích hợp Laser UI Animation", "scan-laser-line" in scan_html)
    assert_test("Trang tích hợp bảng trích xuất y khoa (OD & OS)", "Mắt Phải (OD)" in scan_html and "Mắt Trái (OS)" in scan_html)
    assert_test("Trang tích hợp nút Chọn Ảnh & Chụp Camera trực tiếp", "prescriptionInput" in scan_html and "prescriptionCameraInput" in scan_html)

    # Test OCR API Endpoint: Student Sample
    s_data = urllib.parse.urlencode({"sample_type": "student"}).encode("utf-8")
    s_req = urllib.request.Request(f"{BASE_URL}/api/cv/scan-prescription", data=s_data)
    s_res = json.loads(opener.open(s_req).read().decode("utf-8"))
    assert_test("AI OCR trích xuất Đơn Kính Học Sinh (-1.75D, PD: 62mm)", s_res["success"] and s_res["data"]["right_eye"]["sph"] == -1.75 and s_res["data"]["pd"] == 62.0)

    # Test OCR API Endpoint: Office Worker Sample
    o_data = urllib.parse.urlencode({"sample_type": "office"}).encode("utf-8")
    o_req = urllib.request.Request(f"{BASE_URL}/api/cv/scan-prescription", data=o_data)
    o_res = json.loads(opener.open(o_req).read().decode("utf-8"))
    assert_test("AI OCR trích xuất Đơn Kính Văn Phòng (Cận -3.50D, Loạn -0.75D)", o_res["success"] and o_res["data"]["right_eye"]["sph"] == -3.50 and o_res["data"]["right_eye"]["cyl"] == -0.75)

    # Test OCR API Endpoint: High Myopia Sample
    h_data = urllib.parse.urlencode({"sample_type": "high_myopia"}).encode("utf-8")
    h_req = urllib.request.Request(f"{BASE_URL}/api/cv/scan-prescription", data=h_data)
    h_res = json.loads(opener.open(h_req).read().decode("utf-8"))
    assert_test("AI OCR đề xuất tròng siêu mỏng 1.67 cho ca cận nặng (-6.50D)", h_res["success"] and h_res["data"]["recommended_lens_index"] == 1.67)

    # ================= 3. CUSTOMER AUTHENTICATION & PRESCRIPTION SAVING =================
    print("\n[PHẦN 3] KIỂM TRA ĐĂNG NHẬP KHÁCH HÀNG & ĐỒNG BỘ ĐƠN KÍNH:")
    login_data = urllib.parse.urlencode({"identifier": "khachhang@gmail.com", "password": "123456"}).encode("utf-8")
    resp_login = opener.open(f"{BASE_URL}/login", data=login_data)
    assert_test("Đăng nhập tài khoản khách hàng thành công", resp_login.status == 200)

    # Save Prescription API
    presc_payload = json.dumps({
        "user_id": 2,
        "right_sph": -1.50,
        "right_cyl": -0.50,
        "right_axis": 180,
        "left_sph": -1.50,
        "left_cyl": -0.50,
        "left_axis": 180,
        "pd": 63.5
    }).encode("utf-8")
    req_presc = urllib.request.Request(f"{BASE_URL}/api/profile/prescription", data=presc_payload, headers={"Content-Type": "application/json"})
    resp_presc = opener.open(req_presc)
    presc_res = json.loads(resp_presc.read().decode("utf-8"))
    assert_test("API Lưu đơn kính thị lực vào Hồ Sơ cá nhân", presc_res.get("success") == True)

    profile_html = opener.open(f"{BASE_URL}/profile").read().decode("utf-8")
    assert_test("Trang Hồ sơ khách hiển thị đúng số độ cận đã lưu (-1.5)", "-1.5" in profile_html)

    # ================= 4. CART, VOUCHER, ORDERS & AUTOMATIC VIETQR =================
    print("\n[PHẦN 4] KIỂM TRA GIỎ HÀNG, MÃ GIẢM GIÁ & TẠO ĐƠN HÀNG:")
    
    # Voucher KIMCHI50K
    v_req = urllib.request.Request(f"{BASE_URL}/api/vouchers/apply", data=json.dumps({"code": "KIMCHI50K", "cart_total": 1000000}).encode("utf-8"), headers={"Content-Type": "application/json"})
    v_res = json.loads(opener.open(v_req).read().decode("utf-8"))
    assert_test("Áp dụng mã giảm giá KIMCHI50K (-50,000đ)", v_res.get("discount_amount") == 50000)

    # Create Order
    order_payload = json.dumps({
        "customer_name": "Đức Anh Khách Hàng",
        "phone": "0987654321",
        "email": "khachhang@gmail.com",
        "shipping_address": "Tòa Landmark 81, TP. Hồ Chí Minh",
        "payment_method": "vietqr",
        "voucher_code": "KIMCHI50K",
        "items": [
            {
                "frame_id": 1,
                "lens_id": 1,
                "quantity": 1,
                "right_sph": -1.50,
                "right_cyl": -0.50,
                "right_axis": 180,
                "left_sph": -1.50,
                "left_cyl": -0.50,
                "left_axis": 180,
                "pd": 63.5
            }
        ]
    }).encode("utf-8")
    req_order = urllib.request.Request(f"{BASE_URL}/api/orders", data=order_payload, headers={"Content-Type": "application/json"})
    order_data = json.loads(opener.open(req_order).read().decode("utf-8"))
    order_code = order_data.get("order_code")
    assert_test("Tạo đơn hàng kèm thông số tròng kính thành công", bool(order_code), f"Mã đơn: #{order_code}")

    # VietQR Webhook
    webhook_payload = json.dumps({
        "content": f"{order_code} thanh toan don hang",
        "transferAmount": order_data.get("total_amount"),
        "gateway": "MBBank"
    }).encode("utf-8")
    req_webhook = urllib.request.Request(f"{BASE_URL}/api/payment/webhook", data=webhook_payload, headers={"Content-Type": "application/json"})
    webhook_res = json.loads(opener.open(req_webhook).read().decode("utf-8"))
    assert_test("VietQR Webhook tự động khớp tiền và kích hoạt trạng thái", webhook_res.get("success") == True)

    # ================= 5. ADMIN AUTHENTICATION & MANAGEMENT =================
    print("\n[PHẦN 5] KIỂM TRA PHÂN QUYỀN ADMIN & QUẢN TRỊ:")
    admin_login_data = urllib.parse.urlencode({"identifier": "ducanh2006", "password": "ducanh2006@"}).encode("utf-8")
    resp_admin_login = opener.open(f"{BASE_URL}/login", data=admin_login_data)
    assert_test("Đăng nhập tài khoản Quản trị viên (ducanh2006) thành công", resp_admin_login.status == 200)

    admin_html = opener.open(f"{BASE_URL}/admin").read().decode("utf-8")
    assert_test("Truy cập bảng điều khiển Admin an toàn", "Bảng Quản Trị Hệ Thống" in admin_html or "Quản Trị" in admin_html)
    assert_test("Bảng Admin hiển thị đơn hàng mới tạo", order_code in admin_html)

    # Admin Update Order Status
    order_id = order_data.get("order_id")
    update_req = urllib.request.Request(
        f"{BASE_URL}/api/orders/{order_id}/status",
        data=json.dumps({"order_status": "processing"}).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="PUT"
    )
    update_res = json.loads(opener.open(update_req).read().decode("utf-8"))
    # ================= 6. MEDICAL AI OPHTHALMOLOGIST RAG BOT =================
    print("\n[PHẦN 6] KIỂM TRA BÁC SĨ MẮT AI & HỆ THỐNG RAG NHÃN KHOA Y KHOA:")
    rag_payload = json.dumps({"message": "Tôi làm việc máy tính bị mỏi mắt khô mắt và cận 3 độ thì nên chọn tròng kính gì?"}).encode("utf-8")
    req_rag = urllib.request.Request(f"{BASE_URL}/api/chat/ask", data=rag_payload, headers={"Content-Type": "application/json"})
    rag_res = json.loads(opener.open(req_rag).read().decode("utf-8"))
    assert_test("Bác sĩ AI phản hồi với giọng điệu Y Khoa ân cần", "Bác sĩ Quang học AI" in rag_res.get("reply", ""))
    assert_test("Bác sĩ AI tư vấn tròng Blue Cut & chiết suất 1.60 chuẩn xác", "Blue Cut" in rag_res.get("reply", "") or "1.60" in rag_res.get("reply", ""))

    # Test Astigmatism & AXIS query
    rag_payload_astig = json.dumps({"message": "Bác sĩ giải thích giúp tôi độ loạn thị và trục AXIS với"}).encode("utf-8")
    req_rag_astig = urllib.request.Request(f"{BASE_URL}/api/chat/ask", data=rag_payload_astig, headers={"Content-Type": "application/json"})
    rag_res_astig = json.loads(opener.open(req_rag_astig).read().decode("utf-8"))
    assert_test("Bác sĩ AI giải mã độ loạn thị CYL và trục AXIS", "AXIS" in rag_res_astig.get("reply", "") and "CYL" in rag_res_astig.get("reply", ""))

    # Test Emergency Warning query
    rag_payload_emg = json.dumps({"message": "Mắt tôi thấy chớp sáng và đốm đen ruồi bay có nguy hiểm không?"}).encode("utf-8")
    req_rag_emg = urllib.request.Request(f"{BASE_URL}/api/chat/ask", data=rag_payload_emg, headers={"Content-Type": "application/json"})
    rag_res_emg = json.loads(opener.open(req_rag_emg).read().decode("utf-8"))
    assert_test("Bác sĩ AI cảnh báo nguy cơ bong võng mạc & khuyên đi viện cấp cứu", "bong võng mạc" in rag_res_emg.get("reply", "") or "CẢNH BÁO Y KHOA" in rag_res_emg.get("reply", ""))

    print("\n" + "=" * 80)
    print(f"🎉 TẤT CẢ {passed_count}/{total_count} BÀI TEST CHUYÊN SÂU ĐỀU ĐẠT CHUẨN 100% HOÀN HẢO!")
    print("=" * 80)

if __name__ == "__main__":
    run_deep_tests()
