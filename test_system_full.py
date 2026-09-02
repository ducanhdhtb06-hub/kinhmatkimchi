import urllib.request
import urllib.parse
import json
import http.cookiejar
import sys

BASE_URL = "http://localhost:8000"

def run_tests():
    print("=" * 75)
    print("🧪 BẮT ĐẦU CHẠY BỘ TEST KIỂM THỬ TOÀN DIỆN HỆ THỐNG KÍNH MẮT KIM CHI")
    print("=" * 75)

    test_count = 0
    passed_count = 0

    def assert_test(name, condition, extra=""):
        nonlocal test_count, passed_count
        test_count += 1
        if condition:
            passed_count += 1
            print(f"  ✅ [PASS] {name} {extra}")
        else:
            print(f"  ❌ [FAIL] {name} {extra}")
            sys.exit(1)

    # -------------------------------------------------------------
    # 1. TEST BẢO MẬT & XÁC THỰC PHÂN QUYỀN (AUTH BARRIER & ROLES)
    # -------------------------------------------------------------
    print("\n[1/9] KIỂM TRA BẢO MẬT, ĐĂNG NHẬP & PHÂN QUYỀN:")

    # 1.1 Khách chưa đăng nhập vào trang chủ -> redirect đến /login
    unauth_req = urllib.request.Request(f"{BASE_URL}/", headers={"User-Agent": "TestClient"})
    unauth_res = urllib.request.urlopen(unauth_req)
    assert_test("Chặn khách vãng lai chưa đăng nhập", "/login" in unauth_res.url)

    # 1.2 Đăng nhập tài khoản Khách hàng (khachhang@gmail.com)
    cj_customer = http.cookiejar.CookieJar()
    client_customer = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj_customer))
    login_cust_data = urllib.parse.urlencode({
        "identifier": "khachhang@gmail.com",
        "password": "123456",
        "next_url": "/"
    }).encode("utf-8")
    res_cust_login = client_customer.open(f"{BASE_URL}/login", data=login_cust_data)
    assert_test("Đăng nhập Khách hàng thành công", res_cust_login.status == 200)

    # 1.3 Khách hàng vào /admin -> Phải bị chặn (HTTP 403 hoặc thông báo chặn)
    try:
        res_cust_admin = client_customer.open(f"{BASE_URL}/admin")
        cust_admin_html = res_cust_admin.read().decode("utf-8")
        assert_test("Chặn khách thường truy cập /admin", "Đăng Nhập Quản Trị Viên" in cust_admin_html or res_cust_admin.status == 403)
    except urllib.error.HTTPError as e:
        assert_test("Chặn khách thường truy cập /admin (403 Forbidden)", e.code == 403)

    # 1.4 Đăng nhập tài khoản Quản trị viên mới (ducanh2006 / ducanh2006@)
    cj_admin = http.cookiejar.CookieJar()
    client_admin = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj_admin))
    login_admin_data = urllib.parse.urlencode({
        "identifier": "ducanh2006",
        "password": "ducanh2006@",
        "next_url": "/admin"
    }).encode("utf-8")
    res_admin_login = client_admin.open(f"{BASE_URL}/login", data=login_admin_data)
    assert_test("Đăng nhập Admin (ducanh2006) thành công", res_admin_login.status == 200)

    # 1.5 Admin vào /admin -> Phải trả về HTTP 200 và giao diện Bảng quản trị
    res_admin_page = client_admin.open(f"{BASE_URL}/admin")
    admin_html = res_admin_page.read().decode("utf-8")
    assert_test("Admin truy cập /admin thành công", "Bảng Quản Trị - Kính Mắt Kim Chi" in admin_html)

    # -------------------------------------------------------------
    # 2. TEST DANH MỤC, GỌNG KÍNH & BỘ LỌC TÌM KIẾM (CATALOG & FRAMES)
    # -------------------------------------------------------------
    print("\n[2/9] KIỂM TRA BỘ SƯU TẬP GỌNG KÍNH & API:")

    # 2.1 Lấy danh mục qua API
    cats_res = client_customer.open(f"{BASE_URL}/api/categories")
    cats_data = json.loads(cats_res.read().decode("utf-8"))
    assert_test("API /api/categories hoạt động", len(cats_data) > 0, f"({len(cats_data)} danh mục)")

    # 2.2 Lấy danh sách gọng kính & lọc theo shape
    shape_param = urllib.parse.quote("Vuông")
    frames_res = client_customer.open(f"{BASE_URL}/api/frames?shape={shape_param}")
    frames_data = json.loads(frames_res.read().decode("utf-8"))
    assert_test("API /api/frames lọc theo dáng Vuông", len(frames_data) > 0, f"({len(frames_data)} sản phẩm)")

    # 2.3 Lấy danh sách loại tròng kính
    lenses_res = client_customer.open(f"{BASE_URL}/api/lenses")
    lenses_data = json.loads(lenses_res.read().decode("utf-8"))
    assert_test("API /api/lenses lấy danh sách tròng", len(lenses_data) > 0, f"({len(lenses_data)} loại tròng)")

    # 2.4 Chi tiết sản phẩm gọng kính
    detail_res = client_customer.open(f"{BASE_URL}/products/1")
    detail_html = detail_res.read().decode("utf-8")
    assert_test("Trang chi tiết sản phẩm /products/1", "Cấu Hình Tròng Kính Quang Học" in detail_html)

    # -------------------------------------------------------------
    # 3. TEST COMPUTER VISION & PHÒNG THỬ KÍNH AR (VIRTUAL TRY-ON)
    # -------------------------------------------------------------
    print("\n[3/9] KIỂM TRA PHÒNG THỬ KÍNH AR & THỊ GIÁC MÁY TÍNH:")

    # 3.1 Trang /tryon hoạt động
    tryon_res = client_customer.open(f"{BASE_URL}/tryon")
    tryon_html = tryon_res.read().decode("utf-8")
    assert_test("Trang thử kính AR /tryon", "Phòng Thử Kính AR" in tryon_html and "So Sánh Lưới (2x2)" in tryon_html)

    # 3.2 API gợi ý dáng kính theo dáng mặt
    face_req = urllib.request.Request(
        f"{BASE_URL}/api/cv/face-analysis",
        data=json.dumps({"face_shape": "Tròn"}).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    face_res = client_customer.open(face_req)
    face_data = json.loads(face_res.read().decode("utf-8"))
    assert_test("API /api/cv/face-analysis phân tích mặt", face_data.get("face_shape") == "Tròn")

    # -------------------------------------------------------------
    # 4. TEST AI OCR ĐỌC PHIẾU KHÁM MẮT (PRESCRIPTION OCR AI)
    # -------------------------------------------------------------
    print("\n[4/9] KIỂM TRA AI OCR BÓC TÁCH PHIẾU KHÁM MẮT:")
    from app.ocr_service import parse_prescription_text
    rx_sample = """
    BỆNH VIỆN MẮT TRUNG ƯƠNG
    PHIẾU ĐO KHÚC XẠ MẮT
    Bệnh nhân: Trần Thị Mai - Tuổi: 24
    MẮT PHẢI (OD): SPH -2.25 | CYL -0.50 | AXIS 180
    MẮT TRÁI (OS): SPH -3.00 | CYL -0.75 | AXIS 170
    KHOẢNG CÁCH ĐỒNG TỬ (PD): 64.0 mm
    """
    rx_parsed = parse_prescription_text(rx_sample)
    assert_test("AI OCR bóc tách SPH Mắt Phải", rx_parsed["right_sph"] == -2.25)
    assert_test("AI OCR bóc tách CYL Mắt Phải", rx_parsed["right_cyl"] == -0.50)
    assert_test("AI OCR bóc tách Trục Mắt Phải", rx_parsed["right_axis"] == 180)
    assert_test("AI OCR bóc tách SPH Mắt Trái", rx_parsed["left_sph"] == -3.00)
    assert_test("AI OCR bóc tách CYL Mắt Trái", rx_parsed["left_cyl"] == -0.75)
    assert_test("AI OCR bóc tách Trục Mắt Trái", rx_parsed["left_axis"] == 170)
    assert_test("AI OCR bóc tách Khoảng cách đồng tử PD", rx_parsed["pd"] == 64.0)

    # -------------------------------------------------------------
    # 5. TEST HỆ THỐNG MÃ GIẢM GIÁ (VOUCHER ENGINE)
    # -------------------------------------------------------------
    print("\n[5/9] KIỂM TRA HỆ THỐNG VOUCHER & MÃ KHUYẾN MÃI:")

    # 5.1 Áp mã giảm 50k (KIMCHI50K) cho đơn 800k
    v_req1 = urllib.request.Request(
        f"{BASE_URL}/api/vouchers/apply",
        data=json.dumps({"code": "KIMCHI50K", "cart_total": 800000}).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    v_res1 = client_customer.open(v_req1)
    v_data1 = json.loads(v_res1.read().decode("utf-8"))
    assert_test("Áp dụng mã KIMCHI50K (Giảm 50.000đ)", v_data1["discount_amount"] == 50000 and v_data1["final_total"] == 750000)

    # 5.2 Áp mã giảm 10% (KIMCHI10) cho đơn 1.000.000đ -> Giảm 100.000đ
    v_req2 = urllib.request.Request(
        f"{BASE_URL}/api/vouchers/apply",
        data=json.dumps({"code": "KIMCHI10", "cart_total": 1000000}).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    v_res2 = client_customer.open(v_req2)
    v_data2 = json.loads(v_res2.read().decode("utf-8"))
    assert_test("Áp dụng mã KIMCHI10 (Giảm 10% = 100.000đ)", v_data2["discount_amount"] == 100000 and v_data2["final_total"] == 900000)

    # 5.3 Mã không tồn tại phải báo lỗi 400
    try:
        v_bad = urllib.request.Request(
            f"{BASE_URL}/api/vouchers/apply",
            data=json.dumps({"code": "MA_KHONG_TON_TAI", "cart_total": 500000}).encode("utf-8"),
            headers={"Content-Type": "application/json"}
        )
        client_customer.open(v_bad)
        assert_test("Từ chối mã không hợp lệ", False)
    except urllib.error.HTTPError as e:
        assert_test("Từ chối mã không hợp lệ (400 Bad Request)", e.code == 400)

    # -------------------------------------------------------------
    # 6. TEST ĐẶT HÀNG, TẠO ĐƠN & VIETQR AUTO PAYMENT
    # -------------------------------------------------------------
    print("\n[6/9] KIỂM TRA TẠO ĐƠN HÀNG, VIETQR & THANH TOÁN TỰ ĐỘNG:")

    # 6.1 Tạo đơn hàng mới có gắn tròng + áp mã voucher KIMCHI50K
    order_create_payload = {
        "user_id": 2,
        "customer_name": "Nguyễn Văn An",
        "phone": "0912345678",
        "email": "khachhang@gmail.com",
        "shipping_address": "88 Phố Huế, Quận Hai Bà Trưng, Hà Nội",
        "payment_method": "Chuyển khoản QR",
        "voucher_code": "KIMCHI50K",
        "notes": "Lắp tròng vát mỏng cạnh kính",
        "items": [{
            "frame_id": 1,
            "lens_id": 1,
            "quantity": 1,
            "right_sph": -2.25,
            "right_cyl": -0.50,
            "right_axis": 180,
            "left_sph": -3.00,
            "left_cyl": -0.75,
            "left_axis": 170,
            "pd": 64.0,
            "prescription_image_url": "/static/uploads/rx_test.jpg"
        }]
    }
    ord_req = urllib.request.Request(
        f"{BASE_URL}/api/orders",
        data=json.dumps(order_create_payload).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    ord_res = client_customer.open(ord_req)
    ord_data = json.loads(ord_res.read().decode("utf-8"))
    order_code = ord_data["order_code"]
    order_id = ord_data["order_id"]
    assert_test("Tạo đơn hàng thành công", ord_data.get("order_code") is not None, f"(Mã đơn: #{order_code})")
    assert_test("Áp dụng giảm giá vào đơn hàng", ord_data["discount_amount"] == 50000)

    # 6.2 Tra cứu trạng thái đơn hàng vừa tạo qua API
    track_res = client_customer.open(f"{BASE_URL}/api/orders/{order_code}")
    track_data = json.loads(track_res.read().decode("utf-8"))
    assert_test("Tra cứu thông tin đơn hàng", track_data["payment_status"] == "Chờ thanh toán")

    # 6.3 Giả lập Webhook tiền về VietQR (Simulate Instant Bank Transfer)
    pay_req = urllib.request.Request(
        f"{BASE_URL}/api/payment/simulate-transfer",
        data=json.dumps({
            "order_code": order_code,
            "amount": ord_data["total_amount"]
        }).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    pay_res = client_customer.open(pay_req)
    pay_data = json.loads(pay_res.read().decode("utf-8"))
    assert_test("Webhook VietQR tự động khớp tiền", pay_data.get("success") is True)

    # 6.4 Kiểm tra lại trạng thái đơn hàng -> Phải chuyển sang 'Đã thanh toán' & 'Đang mài tròng'
    track_res2 = client_customer.open(f"{BASE_URL}/api/orders/{order_code}")
    track_data2 = json.loads(track_res2.read().decode("utf-8"))
    assert_test("Đơn hàng tự chuyển 'Đã thanh toán'", track_data2["payment_status"] == "Đã thanh toán")
    assert_test("Đơn hàng tự chuyển 'Đang mài tròng'", track_data2["order_status"] == "Đang mài tròng")

    # -------------------------------------------------------------
    # 7. TEST HỒ SƠ KHÁCH HÀNG & LỊCH SỬ ĐƠN HÀNG (CUSTOMER PROFILE)
    # -------------------------------------------------------------
    print("\n[7/9] KIỂM TRA TRANG HỒ SƠ KHÁCH HÀNG & LƯU THỊ LỰC:")

    # 7.1 Lưu thông số thị lực vào Profile
    specs_req = urllib.request.Request(
        f"{BASE_URL}/api/profile/prescription",
        data=json.dumps({
            "user_id": 2,
            "right_sph": -2.25,
            "right_cyl": -0.50,
            "right_axis": 180,
            "left_sph": -3.00,
            "left_cyl": -0.75,
            "left_axis": 170,
            "pd": 64.0
        }).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    specs_res = client_customer.open(specs_req)
    assert_test("Lưu thông số mắt vào Hồ sơ cá nhân", specs_res.status == 200)

    # 7.2 Truy cập trang /profile và kiểm tra đơn hàng hiển thị
    prof_res = client_customer.open(f"{BASE_URL}/profile")
    prof_html = prof_res.read().decode("utf-8")
    assert_test("Trang /profile hiển thị lịch sử đơn hàng", order_code in prof_html and "Hồ Sơ Thị Lực Của Tôi" in prof_html)

    # -------------------------------------------------------------
    # 8. TEST CẤU HÌNH TELEGRAM BOT & THÔNG BÁO TỨC THÌ
    # -------------------------------------------------------------
    print("\n[8/9] KIỂM TRA CẤU HÌNH TELEGRAM BOT:")
    tg_req = urllib.request.Request(
        f"{BASE_URL}/api/telegram-config",
        data=json.dumps({
            "bot_token": "6888888888:TEST_TOKEN_KIMCHI",
            "chat_id": "123456789",
            "is_active": True,
            "notify_on_order": True,
            "notify_on_payment": True
        }).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    tg_res = client_admin.open(tg_req)
    assert_test("Lưu cấu hình Telegram Bot", tg_res.status == 200)

    # -------------------------------------------------------------
    # 9. TEST BẢNG QUẢN TRỊ ADMIN (ADMIN OPERATIONS)
    # -------------------------------------------------------------
    print("\n[9/9] KIỂM TRA THAO TÁC QUẢN TRỊ VIÊN:")

    # 9.1 Cập nhật trạng thái đơn hàng trong Admin (Chuyển sang 'Đang giao')
    st_req = urllib.request.Request(
        f"{BASE_URL}/api/orders/{order_id}/status",
        data=json.dumps({"order_status": "Đang giao"}).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    st_req.get_method = lambda: "PUT"
    st_res = client_admin.open(st_req)
    assert_test("Admin cập nhật trạng thái đơn sang 'Đang giao'", st_res.status == 200)

    # 9.2 Lấy danh sách Voucher trong Admin
    v_list_res = client_admin.open(f"{BASE_URL}/api/vouchers")
    v_list = json.loads(v_list_res.read().decode("utf-8"))
    assert_test("Admin xem danh sách Voucher", len(v_list) >= 3, f"({len(v_list)} voucher)")

    # 9.3 Cấu hình STK ngân hàng VietQR trong Admin
    bank_req = urllib.request.Request(
        f"{BASE_URL}/api/payment/bank-config",
        data=json.dumps({
            "bank_id": "MB",
            "bank_name": "MBBank (Ngân hàng Quân Đội)",
            "account_number": "0988888888",
            "account_name": "KINH MAT KIM CHI"
        }).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    bank_res = client_admin.open(bank_req)
    assert_test("Admin cập nhật STK VietQR", bank_res.status == 200)

    print("\n" + "=" * 75)
    print(f"🎉 HOÀN THÀNH TẤT CẢ TEST: {passed_count}/{test_count} TÍNH NĂNG ĐẠT CHUẨN 100%!")
    print("=" * 75)

if __name__ == "__main__":
    run_tests()
