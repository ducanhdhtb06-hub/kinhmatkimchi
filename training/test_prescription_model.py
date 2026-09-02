"""
🔬 TEST THỬ NGHIỆM MÔ HÌNH ĐƠN KÍNH ĐÃ HUẤN LUYỆN TRÊN ẢNH BẤT KỲ
================================================================================
Chạy lệnh: python training/test_prescription_model.py --image_path <đường_dẫn_ảnh>
"""

import os
import sys
import argparse

# Thêm thư mục gốc vào sys.path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from app.ocr_service import process_prescription_image


def main():
    parser = argparse.ArgumentParser(description="Test mô hình đơn kính trên ảnh cụ thể")
    parser.add_argument("--image_path", type=str, default="data/dataset/val/sample_0090.jpg", help="Đường dẫn file ảnh đơn kính cần test")
    args = parser.parse_args()

    if not os.path.exists(args.image_path):
        print(f"❌ Không tìm thấy file ảnh: {args.image_path}")
        return

    print("=" * 75)
    print(f"🔬 ĐANG BÓC TÁCH ĐƠN KÍNH TỪ ẢNH: {args.image_path}")
    print("=" * 75)

    result = process_prescription_image(args.image_path)

    if result.get("success"):
        data = result.get("data", {})
        r = data.get("right_eye", {})
        l = data.get("left_eye", {})

        print(f"\n🎉 TRÍCH XUẤT THÀNH CÔNG! [Độ tin cậy: {result.get('confidence', 0.98)*100:.1f}%]")
        print("-" * 75)
        print(f"🏥 Bệnh Viện / Phòng Khám:  {result.get('hospital_name', 'N/A')}")
        print(f"👤 Bệnh Nhân:               {result.get('patient_name', 'N/A')}")
        print(f"📅 Ngày khám:               {result.get('date', 'N/A')}")
        print("-" * 75)
        print(f"👁️ Mắt Phải (OD):            SPH: {r.get('sph', 0.0):+.2f}D | CYL: {r.get('cyl', 0.0):+.2f}D | AXIS: {r.get('axis', 0)}° | VA: {r.get('va', '10/10')}")
        print(f"👁️ Mắt Trái (OS):             SPH: {l.get('sph', 0.0):+.2f}D | CYL: {l.get('cyl', 0.0):+.2f}D | AXIS: {l.get('axis', 0)}° | VA: {l.get('va', '10/10')}")
        print(f"📏 Khoảng cách đồng tử (PD): {result.get('pd', 63.0)} mm")
        print("-" * 75)
        print(f"🩺 Chẩn đoán:               {data.get('diagnosis', 'N/A')}")
        print(f"💎 Đề xuất Tròng kính:      {data.get('recommended_lens_name', 'N/A')} (Chiết suất {data.get('recommended_lens_index', 1.56)})")
        print("=" * 75)
    else:
        print(f"⚠️ Không nhận diện được: {result.get('message')}")
        print(f"💡 Hướng dẫn: {result.get('guide')}")


if __name__ == "__main__":
    main()
