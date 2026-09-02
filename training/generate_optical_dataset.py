import os
import json
import random
import numpy as np
import cv2
from PIL import Image, ImageDraw, ImageFont

# Danh sách bệnh viện và phòng khám mắt tại Việt Nam
HOSPITALS = [
    {"name": "BỆNH VIỆN MẮT TRUNG ƯƠNG", "dept": "KHOA KHÚC XẠ & CHỈNH QUANG", "address": "85 Phố Bà Triệu, Q. Hai Bà Trưng, Hà Nội", "hotline": "1900 6868"},
    {"name": "BỆNH VIỆN MẮT SÀI GÒN", "dept": "KHOA KHÁM MẮT KỸ THUẬT CAO", "address": "100 Lê Thị Riêng, P. Bến Thành, Q.1, TP.HCM", "hotline": "1900 5555"},
    {"name": "BỆNH VIỆN MẮT QUỐC TẾ DND", "dept": "TRUNG TÂM KHÚC XẠ CHUYÊN SÂU", "address": "128 Bùi Thị Xuân, Q. Hai Bà Trưng, Hà Nội", "hotline": "0969 128 128"},
    {"name": "PHÒNG KHÁM CHUYÊN KHOA MẮT FSEC", "dept": "PHÒNG ĐO KHÚC XẠ TỰ ĐỘNG", "address": "Số 213 Khương Trung, Thanh Xuân, Hà Nội", "hotline": "0868 823 566"},
    {"name": "TRUNG TÂM KÍNH MẮT TÂM ĐỨC", "dept": "ĐƠN VỊ ĐO KHÁM THỊ LỰC", "address": "155 Cầu Giấy, Q. Cầu Giấy, Hà Nội", "hotline": "0988 999 888"},
    {"name": "BỆNH VIỆN ĐA KHOA BẠCH MAI", "dept": "KHOA MẮT - KHÚC XẠ BỆNH LÝ", "address": "78 Giải Phóng, Phương Mai, Đống Đa, Hà Nội", "hotline": "024 3869 3731"}
]

DOCTORS = [
    "ThS. BS. Nguyễn Mai Linh",
    "BS. CKI. Trần Quốc Dũng",
    "ThS. BS. Lê Thu Hà",
    "TS. BS. Hoàng Văn Nam",
    "BS. Nguyễn Đức Anh",
    "BS. Phạm Thị Kim Chi"
]

PATIENT_NAMES = [
    "Nguyễn Văn Hoàng", "Trần Thị Mai Phương", "Lê Quốc Bảo", "Phạm Thành Công",
    "Bùi Nguyệt Hà", "Phạm Duy Khánh", "Đỗ Minh Quân", "Vũ Hải Đăng",
    "Ngô Bảo Ngọc", "Hoàng Gia Huy", "Đặng Thùy Dương", "Trịnh Xuân Bách"
]

AUTOREF_MODELS = [
    "HUVITZ HRK-8000A", "TOPCON RM-800", "NIDEK AR-1", "CHAROPS CRK-7000", "CANON RK-F2"
]

FONT_BOLD_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT_REG_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
FONT_MONO_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"

def get_font(path: str, size: int):
    try:
        return ImageFont.truetype(path, size)
    except Exception:
        return ImageFont.load_default()


def generate_diopters():
    """Sinh cặp số độ thực tế theo tiêu chuẩn đo khúc xạ y khoa."""
    sph_step = random.choice([0.0, 0.25, 0.50, 0.75])
    sph_int = random.randint(-8, 3)
    sph = float(sph_int) + (sph_step if sph_int >= 0 else -sph_step)
    
    has_cyl = random.random() < 0.65
    cyl = 0.0
    axis = 0
    if has_cyl:
        cyl = -random.choice([0.25, 0.50, 0.75, 1.00, 1.25, 1.50, 1.75, 2.00, 2.50, 3.00])
        axis = random.choice([180, 175, 170, 165, 10, 15, 90, 85, 95, 127, 13, 0, 45, 135])
        
    return sph, cyl, axis


def generate_hospital_prescription(output_img_path: str) -> dict:
    """Sinh ảnh đơn kính chuẩn A4 Bệnh viện mắt với font rõ nét."""
    width, height = 900, 1200
    bg_color = (random.randint(248, 255), random.randint(248, 255), random.randint(245, 252))
    img = Image.new("RGB", (width, height), bg_color)
    draw = ImageDraw.Draw(img)

    f_title = get_font(FONT_BOLD_PATH, 24)
    f_sub = get_font(FONT_BOLD_PATH, 19)
    f_body = get_font(FONT_REG_PATH, 18)
    f_bold = get_font(FONT_BOLD_PATH, 18)
    f_small = get_font(FONT_REG_PATH, 15)

    hosp = random.choice(HOSPITALS)
    doc = random.choice(DOCTORS)
    p_name = random.choice(PATIENT_NAMES)
    p_age = random.randint(12, 65)
    p_code = f"BN-{random.randint(2026, 2027)}-{random.randint(1000, 9999)}"
    exam_date = f"{random.randint(1, 28):02d}/{random.randint(1, 12):02d}/2026"
    
    r_sph, r_cyl, r_axis = generate_diopters()
    l_sph = r_sph + random.choice([0.0, -0.25, 0.25, -0.50, 0.50, -0.75, 0.75])
    l_cyl, l_axis = (generate_diopters()[1], generate_diopters()[2]) if r_cyl != 0 else (0.0, 0)
    pd_val = round(random.uniform(59.0, 66.0) * 2) / 2

    # Header
    draw.text((60, 40), hosp["name"], fill=(15, 23, 42), font=f_title)
    draw.text((60, 75), hosp["dept"], fill=(30, 41, 59), font=f_body)
    draw.text((60, 105), f"Địa chỉ: {hosp['address']}", fill=(71, 85, 105), font=f_small)
    draw.text((60, 130), f"Hotline: {hosp['hotline']}", fill=(71, 85, 105), font=f_small)
    draw.line([(50, 160), (850, 160)], fill=(203, 213, 225), width=2)

    # Title
    draw.text((220, 185), "PHIẾU ĐO KHÚC XẠ & ĐƠN KÍNH MẮT", fill=(15, 23, 42), font=f_sub)
    draw.text((310, 215), "OPTICAL PRESCRIPTION", fill=(100, 116, 139), font=f_small)

    # Patient info
    draw.text((60, 260), f"Họ và tên: {p_name.upper()}", fill=(15, 23, 42), font=f_bold)
    draw.text((550, 260), f"Mã hồ sơ: #{p_code}", fill=(15, 23, 42), font=f_bold)
    draw.text((60, 300), f"Tuổi: {p_age} tuổi  |  Giới tính: {'Nam' if random.random() > 0.5 else 'Nữ'}", fill=(30, 41, 59), font=f_body)
    draw.text((550, 300), f"Ngày đo khám: {exam_date}", fill=(30, 41, 59), font=f_body)
    draw.text((60, 340), f"Bác sĩ chuyên khoa: {doc}", fill=(30, 41, 59), font=f_body)

    # Table Header
    draw.rectangle([(50, 390), (850, 440)], fill=(241, 245, 249), outline=(203, 213, 225), width=2)
    draw.text((70, 405), "MẮT (EYE)", fill=(15, 23, 42), font=f_bold)
    draw.text((250, 405), "ĐỘ CẦU (SPH)", fill=(15, 23, 42), font=f_bold)
    draw.text((430, 405), "ĐỘ LOẠN (CYL)", fill=(15, 23, 42), font=f_bold)
    draw.text((600, 405), "TRỤC (AXIS)", fill=(15, 23, 42), font=f_bold)
    draw.text((730, 405), "THỊ LỰC (VA)", fill=(15, 23, 42), font=f_bold)

    # OD Row
    draw.rectangle([(50, 440), (850, 500)], fill=(255, 255, 255), outline=(203, 213, 225), width=2)
    draw.text((70, 460), "Mắt Phải (OD)", fill=(15, 23, 42), font=f_bold)
    draw.text((250, 460), f"{r_sph:+.2f} D", fill=(15, 23, 42), font=f_bold)
    draw.text((430, 460), f"{r_cyl:+.2f} D" if r_cyl != 0 else "0.00 D", fill=(15, 23, 42), font=f_bold)
    draw.text((600, 460), f"{r_axis}" if r_axis > 0 else "0", fill=(15, 23, 42), font=f_bold)
    draw.text((740, 460), "10/10", fill=(15, 23, 42), font=f_body)

    # OS Row
    draw.rectangle([(50, 500), (850, 560)], fill=(255, 255, 255), outline=(203, 213, 225), width=2)
    draw.text((70, 520), "Mắt Trái (OS)", fill=(15, 23, 42), font=f_bold)
    draw.text((250, 520), f"{l_sph:+.2f} D", fill=(15, 23, 42), font=f_bold)
    draw.text((430, 520), f"{l_cyl:+.2f} D" if l_cyl != 0 else "0.00 D", fill=(15, 23, 42), font=f_bold)
    draw.text((600, 520), f"{l_axis}" if l_axis > 0 else "0", fill=(15, 23, 42), font=f_bold)
    draw.text((740, 520), "10/10", fill=(15, 23, 42), font=f_body)

    # PD & Notes
    draw.text((60, 595), f"KHOẢNG CÁCH ĐỒNG TỬ (PD): {pd_val:.1f} mm", fill=(15, 23, 42), font=f_bold)
    draw.text((60, 640), "MỤC ĐÍCH KÍNH: Nhìn xa & Chống ánh sáng xanh màn hình", fill=(51, 65, 85), font=f_body)
    draw.text((60, 690), "CHẨN ĐOÁN & LỜI DẶN CỦA BÁC SĨ:", fill=(15, 23, 42), font=f_bold)
    draw.text((60, 725), f"1. Tật khúc xạ: Cận thị ({r_sph:+.2f}D / {l_sph:+.2f}D) kèm loạn thị ({r_cyl:+.2f}D / {l_cyl:+.2f}D)", fill=(71, 85, 105), font=f_body)
    draw.text((60, 755), "2. Khuyên dùng tròng kính chiết suất 1.60 hoặc 1.67 chống tia UV400 & ánh sáng xanh.", fill=(71, 85, 105), font=f_body)
    draw.text((60, 785), "3. Tái khám kiểm tra đáy mắt định kỳ sau 6 tháng.", fill=(71, 85, 105), font=f_body)

    # Signatures
    draw.text((120, 890), "BỆNH NHÂN\n(Ký và ghi rõ họ tên)", fill=(100, 116, 139), font=f_body)
    draw.text((620, 890), "BÁC SĨ KHÁM\n(Ký, đóng dấu)", fill=(100, 116, 139), font=f_body)
    draw.text((610, 980), doc, fill=(15, 23, 42), font=f_bold)

    img.save(output_img_path)

    return {
        "hospital_name": hosp["name"],
        "patient_name": p_name,
        "date": exam_date,
        "document_type": "EYE_PRESCRIPTION",
        "data": {
            "right_eye": {"sph": r_sph, "cyl": r_cyl, "axis": r_axis, "va": "10/10"},
            "left_eye": {"sph": l_sph, "cyl": l_cyl, "axis": l_axis, "va": "10/10"},
            "pd": pd_val,
            "add": 0.0
        }
    }


def generate_thermal_slip(output_img_path: str) -> dict:
    """Sinh ảnh phiếu in nhiệt từ máy đo khúc xạ tự động với font máy in nhiệt rõ nét."""
    width, height = 500, 780
    bg_color = (random.randint(245, 252), random.randint(245, 252), random.randint(240, 248))
    img = Image.new("RGB", (width, height), bg_color)
    draw = ImageDraw.Draw(img)

    f_mono = get_font(FONT_MONO_PATH, 18)
    f_mono_lg = get_font(FONT_MONO_PATH, 20)
    f_mono_sm = get_font(FONT_MONO_PATH, 15)

    machine = random.choice(AUTOREF_MODELS)
    hosp = random.choice(HOSPITALS)
    slip_no = random.randint(1000, 9999)
    exam_date = f"{random.randint(1, 28):02d}/{random.randint(1, 12):02d}/2026"
    
    r_sph, r_cyl, r_axis = generate_diopters()
    l_sph = r_sph + random.choice([0.0, -0.25, 0.25, -0.50, 0.50])
    l_cyl, l_axis = (generate_diopters()[1], generate_diopters()[2]) if r_cyl != 0 else (0.0, 0)
    pd_val = float(random.choice([60, 61, 62, 63, 64, 65]))

    draw.text((40, 20), f"[REF]  VD: 12.00  CYL: (-)", fill=(20, 20, 20), font=f_mono_sm)
    draw.text((40, 45), hosp["name"], fill=(10, 10, 10), font=f_mono_sm)
    draw.text((40, 70), f"{machine}  #No.{slip_no}", fill=(30, 30, 30), font=f_mono)
    draw.text((40, 95), f"DATE: {exam_date}  {random.randint(8,17):02d}:{random.randint(10,59):02d}", fill=(30, 30, 30), font=f_mono_sm)
    draw.line([(30, 125), (470, 125)], fill=(80, 80, 80), width=2)

    # Right Eye Block <R>
    draw.text((40, 140), "<R>     SPH      CYL    AX", fill=(10, 10, 10), font=f_mono)
    for i in range(3):
        noise_sph = r_sph + random.choice([0.0, 0.0, -0.25, 0.25])
        noise_cyl = r_cyl + random.choice([0.0, 0.0, -0.25, 0.25]) if r_cyl != 0 else 0.0
        draw.text((80, 175 + i * 28), f"{noise_sph:+.2f}   {noise_cyl:+.2f}   {r_axis if r_axis > 0 else 0:3d}", fill=(30, 30, 30), font=f_mono)
    
    draw.line([(60, 265), (440, 265)], fill=(120, 120, 120), width=1)
    draw.text((40, 280), f"AVG   {r_sph:+.2f}   {r_cyl:+.2f}   {r_axis if r_axis > 0 else 0:3d}", fill=(10, 10, 10), font=f_mono_lg)
    draw.text((40, 310), f"S.E   {r_sph + (r_cyl/2.0):+.2f}", fill=(50, 50, 50), font=f_mono_sm)

    # Left Eye Block <L>
    draw.text((40, 350), "<L>     SPH      CYL    AX", fill=(10, 10, 10), font=f_mono)
    for i in range(3):
        noise_sph = l_sph + random.choice([0.0, 0.0, -0.25, 0.25])
        noise_cyl = l_cyl + random.choice([0.0, 0.0, -0.25, 0.25]) if l_cyl != 0 else 0.0
        draw.text((80, 385 + i * 28), f"{noise_sph:+.2f}   {noise_cyl:+.2f}   {l_axis if l_axis > 0 else 0:3d}", fill=(30, 30, 30), font=f_mono)
    
    draw.line([(60, 475), (440, 475)], fill=(120, 120, 120), width=1)
    draw.text((40, 490), f"AVG   {l_sph:+.2f}   {l_cyl:+.2f}   {l_axis if l_axis > 0 else 0:3d}", fill=(10, 10, 10), font=f_mono_lg)
    draw.text((40, 520), f"S.E   {l_sph + (l_cyl/2.0):+.2f}", fill=(50, 50, 50), font=f_mono_sm)

    # PD
    draw.line([(30, 560), (470, 560)], fill=(80, 80, 80), width=2)
    draw.text((40, 580), f"PD: {int(pd_val)} mm", fill=(10, 10, 10), font=f_mono_lg)
    draw.text((40, 630), f"OPTICAL EYE CLINIC - {hosp['hotline']}", fill=(60, 60, 60), font=f_mono_sm)

    img.save(output_img_path)

    return {
        "hospital_name": hosp["name"],
        "patient_name": f"Phiếu In Nhiệt (#{slip_no})",
        "date": exam_date,
        "document_type": "EYE_PRESCRIPTION",
        "data": {
            "right_eye": {"sph": r_sph, "cyl": r_cyl, "axis": r_axis, "va": "10/10"},
            "left_eye": {"sph": l_sph, "cyl": l_cyl, "axis": l_axis, "va": "10/10"},
            "pd": pd_val,
            "add": 0.0
        }
    }


def generate_general_health_checkup(output_img_path: str) -> dict:
    """Sinh ảnh Giấy khám sức khỏe tổng quát (Negative sample)."""
    width, height = 850, 1100
    img = Image.new("RGB", (width, height), (252, 252, 252))
    draw = ImageDraw.Draw(img)

    f_title = get_font(FONT_BOLD_PATH, 22)
    f_sub = get_font(FONT_BOLD_PATH, 18)
    f_body = get_font(FONT_REG_PATH, 17)
    f_bold = get_font(FONT_BOLD_PATH, 17)

    p_name = random.choice(PATIENT_NAMES)
    exam_date = f"{random.randint(1, 28):02d}/{random.randint(1, 12):02d}/2026"

    draw.text((60, 40), "SỞ Y TẾ TP. HÀ NỘI - BỆNH VIỆN ĐA KHOA", fill=(20, 20, 20), font=f_body)
    draw.text((220, 80), "GIẤY KHÁM SỨC KHỎE TỔNG QUÁT", fill=(10, 10, 10), font=f_title)
    draw.line([(50, 120), (800, 120)], fill=(180, 180, 180), width=2)

    draw.text((60, 150), f"Họ và tên người khám: {p_name.upper()}", fill=(20, 20, 20), font=f_bold)
    draw.text((60, 190), f"Mục đích khám: Tuyển dụng / Lái xe / Đi học", fill=(40, 40, 40), font=f_body)
    draw.text((60, 230), f"Ngày khám bệnh: {exam_date}", fill=(40, 40, 40), font=f_body)

    draw.text((60, 290), "I. KHÁM THỂ LỰC & NỘI KHOA:", fill=(10, 10, 10), font=f_sub)
    draw.text((80, 330), f"- Chiều cao: {random.randint(155, 180)} cm   - Cân nặng: {random.randint(48, 78)} kg", fill=(40, 40, 40), font=f_body)
    draw.text((80, 370), f"- Huyết áp: {random.choice(['110/70', '120/80', '115/75'])} mmHg   - Nhịp tim: 75 l/ph", fill=(40, 40, 40), font=f_body)
    draw.text((80, 410), "- Khám tuần hoàn, hô hấp, tiêu hóa: Bình thường không bệnh lý", fill=(40, 40, 40), font=f_body)

    draw.text((60, 470), "II. KHÁM CHUYÊN KHOA MẮT & TAI MŨI HỌNG:", fill=(10, 10, 10), font=f_sub)
    draw.text((80, 510), "- Thị lực không kính: Mắt phải 10/10, Mắt trái 10/10", fill=(40, 40, 40), font=f_body)
    draw.text((80, 550), "- Bệnh lý giác mạc, kết mạc: Âm tính", fill=(40, 40, 40), font=f_body)

    draw.text((60, 610), "III. XÉT NGHIỆM MÁU & NƯỚC TIỂU:", fill=(10, 10, 10), font=f_sub)
    draw.text((80, 650), "- Đường huyết, công thức máu trong giới hạn bình thường.", fill=(40, 40, 40), font=f_body)

    draw.text((60, 720), "KẾT LUẬN: ĐỦ ĐIỀU KIỆN SỨC KHỎE ĐỂ LÀM VIỆC / HỌC TẬP (LOẠI I)", fill=(15, 23, 42), font=f_bold)
    draw.text((520, 820), "BÁC SĨ KẾT LUẬN\n(Ký và đóng dấu)", fill=(100, 100, 100), font=f_body)

    img.save(output_img_path)

    return {
        "hospital_name": "Bệnh Viện Đa Khoa",
        "patient_name": p_name,
        "date": exam_date,
        "document_type": "GENERAL_HEALTH_CHECK",
        "data": {}
    }


def build_full_dataset(base_dir: str = "data/dataset", total_samples: int = 150):
    """Tạo bộ dataset hoàn chỉnh gồm train/val và file metadata.jsonl cho Donut/Transformer."""
    os.makedirs(f"{base_dir}/train", exist_ok=True)
    os.makedirs(f"{base_dir}/val", exist_ok=True)

    metadata_train = []
    metadata_val = []

    print(f"🚀 Đang khởi tạo bộ dataset gồm {total_samples} mẫu đơn kính và phiếu y tế...")

    for i in range(total_samples):
        is_val = (i % 5 == 0) # 80% train, 20% val
        split = "val" if is_val else "train"
        
        doc_type_choice = random.random()
        filename = f"sample_{i:04d}.jpg"
        img_path = f"{base_dir}/{split}/{filename}"

        if doc_type_choice < 0.55:
            gt = generate_hospital_prescription(img_path)
        elif doc_type_choice < 0.85:
            gt = generate_thermal_slip(img_path)
        else:
            gt = generate_general_health_checkup(img_path)

        item = {
            "file_name": filename,
            "ground_truth": json.dumps({"gt_parse": gt}, ensure_ascii=False)
        }

        if is_val:
            metadata_val.append(item)
        else:
            metadata_train.append(item)

    with open(f"{base_dir}/train/metadata.jsonl", "w", encoding="utf-8") as f:
        for item in metadata_train:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")

    with open(f"{base_dir}/val/metadata.jsonl", "w", encoding="utf-8") as f:
        for item in metadata_val:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")

    print(f"✅ Hoàn tất tạo dataset: {len(metadata_train)} mẫu Train, {len(metadata_val)} mẫu Val.")
    print(f"📂 Lưu tại: {base_dir}/")


if __name__ == "__main__":
    build_full_dataset("data/dataset", total_samples=120)
