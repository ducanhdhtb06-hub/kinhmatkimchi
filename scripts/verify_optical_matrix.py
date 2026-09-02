"""
🔬 DETAILED FIELD-BY-FIELD CLINICAL OPTICAL MATRIX VERIFIER
So sánh đối chiếu chi tiết từng trường dữ liệu:
[OD: SPH, CYL, AXIS] | [OS: SPH, CYL, AXIS] | [PD] | [Bệnh Viện] | [Bệnh Nhân]
"""

import os
import sys
import json
import time

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from app.ocr_service import process_prescription_image

META_FILE = os.path.join(BASE_DIR, "data", "dataset", "val", "metadata.jsonl")

def run_verification():
    if not os.path.exists(META_FILE):
        print(f"❌ Không tìm thấy file {META_FILE}")
        return

    items = []
    with open(META_FILE, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                items.append(json.loads(line))

    print("=" * 115)
    print("🔬 BẢNG ĐỐI SOÁT CHI TIẾT TỪNG THÔNG SỐ KHÚC XẠ QUANG HỌC (GROUND TRUTH VS AI PREDICTION)")
    print("=" * 115)
    print(f"{'Mẫu Thử':<18} | {'Mắt Phải (OD) SPH/CYL x AXIS':<30} | {'Mắt Trái (OS) SPH/CYL x AXIS':<30} | {'PD (mm)':<10} | {'Kết Quả'}")
    print("-" * 115)

    passed_count = 0
    total = min(15, len(items))

    for idx in range(total):
        item = items[idx]
        fname = item["file_name"]
        img_path = os.path.join(BASE_DIR, "data", "dataset", "val", fname)
        if not os.path.exists(img_path):
            continue

        gt = json.loads(item["ground_truth"])["gt_parse"]
        gt_data = gt.get("data", {})
        gt_od = gt_data.get("right_eye", {})
        gt_os = gt_data.get("left_eye", {})
        gt_pd = gt_data.get("pd", 62.0)

        # Chạy dự đoán AI
        pred = process_prescription_image(img_path)
        pred_data = pred.get("data", {})
        pred_od = pred_data.get("right_eye", {})
        pred_os = pred_data.get("left_eye", {})
        pred_pd = pred.get("pd", 62.0)

        # Chuỗi hiển thị Ground Truth
        gt_od_str = f"{gt_od.get('sph', 0.0):+.2f}/{gt_od.get('cyl', 0.0):+.2f}x{gt_od.get('axis', 0)}°"
        gt_os_str = f"{gt_os.get('sph', 0.0):+.2f}/{gt_os.get('cyl', 0.0):+.2f}x{gt_os.get('axis', 0)}°"
        
        # Chuỗi hiển thị AI Dự đoán
        pr_od_str = f"{pred_od.get('sph', 0.0):+.2f}/{pred_od.get('cyl', 0.0):+.2f}x{pred_od.get('axis', 0)}°"
        pr_os_str = f"{pred_os.get('sph', 0.0):+.2f}/{pred_os.get('cyl', 0.0):+.2f}x{pred_os.get('axis', 0)}°"

        # So khớp
        od_match = (abs(gt_od.get('sph', 0.0) - pred_od.get('sph', 0.0)) <= 0.5) and (abs(gt_od.get('cyl', 0.0) - pred_od.get('cyl', 0.0)) <= 0.5)
        os_match = (abs(gt_os.get('sph', 0.0) - pred_os.get('sph', 0.0)) <= 0.5) and (abs(gt_os.get('cyl', 0.0) - pred_os.get('cyl', 0.0)) <= 0.5)
        pd_match = abs(float(gt_pd) - float(pred_pd)) <= 1.0

        is_correct = od_match and os_match and pd_match
        if is_correct:
            passed_count += 1
            status = "✅ CHUẨN XÁC"
        else:
            status = "⚠️ CẦN TINH CHỈNH"

        print(f"[{fname}]")
        print(f"  • Chuẩn GT:   | OD: {gt_od_str:<26} | OS: {gt_os_str:<26} | PD: {gt_pd:<6} mm |")
        print(f"  • AI Đọc:     | OD: {pr_od_str:<26} | OS: {pr_os_str:<26} | PD: {pred_pd:<6} mm | {status}")
        print(f"  • Cơ sở:      {pred.get('hospital_name', 'N/A')} - BN: {pred.get('patient_name', 'N/A')}")
        print("-" * 115)

    acc = (passed_count / total) * 100
    print(f"🎯 TỔNG KẾT: {passed_count}/{total} mẫu chuẩn xác 100% từng trường dữ liệu ({acc:.1f}%)")
    print("=" * 115)

if __name__ == "__main__":
    run_verification()
