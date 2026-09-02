import os
import sys
import json

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from app.ocr_service import process_prescription_image

def evaluate_on_dataset(val_metadata_path: str = "data/dataset/val/metadata.jsonl"):
    if not os.path.exists(val_metadata_path):
        print(f"❌ Không tìm thấy file {val_metadata_path}")
        return

    print("=" * 70)
    print("📊 BẮT ĐẦU ĐÁNH GIÁ ĐỘ CHÍNH XÁC MÔ HÌNH TRÊN TẬP VALIDATION DATASET")
    print("=" * 70)

    total_samples = 0
    correct_classification = 0
    correct_od_sph = 0
    correct_od_cyl = 0
    correct_os_sph = 0
    correct_os_cyl = 0
    correct_pd = 0

    val_dir = os.path.dirname(val_metadata_path)

    with open(val_metadata_path, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            item = json.loads(line.strip())
            total_samples += 1

            img_path = os.path.join(val_dir, item["file_name"])
            gt_parse = json.loads(item["ground_truth"])["gt_parse"]
            gt_type = gt_parse.get("document_type", "EYE_PRESCRIPTION")
            gt_data = gt_parse.get("data", {})

            # Chạy qua pipeline OCR & Document Understanding
            pred = process_prescription_image(img_path)
            pred_type = pred.get("classification")
            pred_data = pred.get("data") or {}

            # 1. Khớp loại tài liệu
            if pred_type == gt_type:
                correct_classification += 1

            # 2. Khớp các trường số độ nếu là đơn kính
            if gt_type == "EYE_PRESCRIPTION" and pred_type == "EYE_PRESCRIPTION":
                # OD SPH
                gt_r_sph = gt_data.get("right_eye", {}).get("sph", 0.0)
                pred_r_sph = pred_data.get("right_eye", {}).get("sph", 0.0)
                if abs(gt_r_sph - pred_r_sph) <= 0.25:
                    correct_od_sph += 1

                # OD CYL
                gt_r_cyl = gt_data.get("right_eye", {}).get("cyl", 0.0)
                pred_r_cyl = pred_data.get("right_eye", {}).get("cyl", 0.0)
                if abs(gt_r_cyl - pred_r_cyl) <= 0.25:
                    correct_od_cyl += 1

                # OS SPH
                gt_l_sph = gt_data.get("left_eye", {}).get("sph", 0.0)
                pred_l_sph = pred_data.get("left_eye", {}).get("sph", 0.0)
                if abs(gt_l_sph - pred_l_sph) <= 0.25:
                    correct_os_sph += 1

                # OS CYL
                gt_l_cyl = gt_data.get("left_eye", {}).get("cyl", 0.0)
                pred_l_cyl = pred_data.get("left_eye", {}).get("cyl", 0.0)
                if abs(gt_l_cyl - pred_l_cyl) <= 0.25:
                    correct_os_cyl += 1

                # PD
                gt_pd = gt_data.get("pd", 63.0)
                pred_pd = pred_data.get("pd", 63.0)
                if abs(gt_pd - pred_pd) <= 1.0:
                    correct_pd += 1

    # In báo cáo kết quả
    print(f"\n📈 KẾT QUẢ ĐÁNH GIÁ ({total_samples} mẫu kiểm thử):")
    print(f"  • Độ chính xác Phân loại tài liệu (Classification Accuracy): {correct_classification / total_samples * 100:.1f}% ({correct_classification}/{total_samples})")
    
    rx_samples = total_samples - (total_samples - correct_classification)
    if rx_samples > 0:
        print(f"  • Độ chính xác Độ cầu Mắt phải (OD SPH Accuracy):        {correct_od_sph / total_samples * 100:.1f}%")
        print(f"  • Độ chính xác Độ loạn Mắt phải (OD CYL Accuracy):        {correct_od_cyl / total_samples * 100:.1f}%")
        print(f"  • Độ chính xác Độ cầu Mắt trái (OS SPH Accuracy):         {correct_os_sph / total_samples * 100:.1f}%")
        print(f"  • Độ chính xác Độ loạn Mắt trái (OS CYL Accuracy):         {correct_os_cyl / total_samples * 100:.1f}%")
        print(f"  • Độ chính xác Khoảng cách đồng tử (PD Accuracy):         {correct_pd / total_samples * 100:.1f}%")
    print("=" * 70)

if __name__ == "__main__":
    evaluate_on_dataset("data/dataset/val/metadata.jsonl")
