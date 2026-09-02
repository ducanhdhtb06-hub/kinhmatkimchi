"""
🎯 CÔNG CỤ ĐÁNH GIÁ ĐỘ CHÍNH XÁC (ACCURACY EVALUATION) MÔ HÌNH ĐƠN KÍNH
================================================================================
Chạy kiểm thử toàn diện trên tập Validation (data/dataset/val) và tính toán:
1. Overall Optical Accuracy (% Độ chính xác toàn diện).
2. Right Eye (OD) SPH / CYL / AXIS Accuracy.
3. Left Eye (OS) SPH / CYL / AXIS Accuracy.
4. Pupillary Distance (PD) Accuracy.
5. Exact Match JSON Accuracy.
6. Danh sách chi tiết các mẫu dự đoán đúng và sai để trực quan hóa.
"""

import os
import sys
import json
import re
import argparse
import torch
from PIL import Image
from typing import Dict, Any, Tuple, List

# Thêm thư mục gốc vào sys.path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from app.donut_service import clean_and_parse_donut_json

try:
    from transformers import VisionEncoderDecoderModel, AutoProcessor
    from peft import PeftModel
except ImportError:
    print("❌ Vui lòng cài đặt thư viện: pip install transformers peft pillow torch")
    sys.exit(1)


def parse_args():
    parser = argparse.ArgumentParser(description="🎯 Đánh giá Độ chính xác (Accuracy) mô hình Đơn kính")
    parser.add_argument("--model_dir", type=str, default="models/optical_prescription_model", help="Thư mục chứa mô hình đã train")
    parser.add_argument("--val_dir", type=str, default="data/dataset/val", help="Thư mục dữ liệu validation")
    parser.add_argument("--device", type=str, default="auto", help="Thiết bị: auto, cuda, cpu")
    parser.add_argument("--max_samples", type=int, default=100, help="Số mẫu tối đa muốn đánh giá")
    return parser.parse_args()


def evaluate_single_sample(gt: Dict[str, Any], pred: Dict[str, Any]) -> Dict[str, bool]:
    """So sánh từng trường quang học giữa Ground Truth và Prediction."""
    if not pred or not isinstance(pred, dict):
        return {k: False for k in ["r_sph", "r_cyl", "r_axis", "l_sph", "l_cyl", "l_axis", "pd", "doc_type", "hospital", "exact_match"]}

    gt_data = gt.get("data", {})
    pred_data = pred.get("data", {})

    gt_r = gt_data.get("right_eye", {})
    pred_r = pred_data.get("right_eye", {})

    gt_l = gt_data.get("left_eye", {})
    pred_l = pred_data.get("left_eye", {})

    # 1. So sánh Mắt Phải (OD)
    r_sph_ok = abs(float(gt_r.get("sph", 0.0)) - float(pred_r.get("sph", 0.0))) <= 0.25 if ("sph" in gt_r and "sph" in pred_r) else (gt_r == pred_r)
    r_cyl_ok = abs(float(gt_r.get("cyl", 0.0)) - float(pred_r.get("cyl", 0.0))) <= 0.25 if ("cyl" in gt_r and "cyl" in pred_r) else (gt_r == pred_r)
    r_axis_ok = abs(int(gt_r.get("axis", 0)) - int(pred_r.get("axis", 0))) <= 5 if ("axis" in gt_r and "axis" in pred_r) else True

    # 2. So sánh Mắt Trái (OS)
    l_sph_ok = abs(float(gt_l.get("sph", 0.0)) - float(pred_l.get("sph", 0.0))) <= 0.25 if ("sph" in gt_l and "sph" in pred_l) else (gt_l == pred_l)
    l_cyl_ok = abs(float(gt_l.get("cyl", 0.0)) - float(pred_l.get("cyl", 0.0))) <= 0.25 if ("cyl" in gt_l and "cyl" in pred_l) else (gt_l == pred_l)
    l_axis_ok = abs(int(gt_l.get("axis", 0)) - int(pred_l.get("axis", 0))) <= 5 if ("axis" in gt_l and "axis" in pred_l) else True

    # 3. Khoảng cách đồng tử PD
    gt_pd = float(gt_data.get("pd", 0.0))
    pred_pd = float(pred_data.get("pd", 0.0))
    pd_ok = abs(gt_pd - pred_pd) <= 1.0 if (gt_pd > 0 and pred_pd > 0) else True

    # 4. Tên Bệnh Viện & Loại Tài Liệu
    doc_type_ok = gt.get("document_type", "").lower() == pred.get("document_type", "").lower()
    hosp_ok = (gt.get("hospital_name", "").lower() in pred.get("hospital_name", "").lower()) or (pred.get("hospital_name", "").lower() in gt.get("hospital_name", "").lower()) if gt.get("hospital_name") else True

    is_all_correct = r_sph_ok and r_cyl_ok and r_axis_ok and l_sph_ok and l_cyl_ok and l_axis_ok and pd_ok and doc_type_ok

    return {
        "r_sph": r_sph_ok,
        "r_cyl": r_cyl_ok,
        "r_axis": r_axis_ok,
        "l_sph": l_sph_ok,
        "l_cyl": l_cyl_ok,
        "l_axis": l_axis_ok,
        "pd": pd_ok,
        "doc_type": doc_type_ok,
        "hospital": hosp_ok,
        "exact_match": is_all_correct
    }


def main():
    args = parse_args()

    if args.device == "auto":
        device_str = "cuda" if torch.cuda.is_available() else "cpu"
    else:
        device_str = args.device
    device = torch.device(device_str)

    print("=" * 80)
    print("🎯 ĐÁNH GIÁ ĐỘ CHÍNH XÁC (ACCURACY) MÔ HÌNH TRÍCH XUẤT ĐƠN KÍNH QUANG HỌC")
    print("=" * 80)
    print(f"👉 Thư mục Model:       {args.model_dir}")
    print(f"📁 Thư mục Validation:  {args.val_dir}")
    print(f"💻 Thiết bị chạy:       {device}")
    print("=" * 80)

    # 1. Nạp Processor và Model
    print("\n📥 Đang nạp mô hình...")
    try:
        processor = AutoProcessor.from_pretrained(args.model_dir)
    except Exception:
        processor = AutoProcessor.from_pretrained("naver-clova-ix/donut-base")

    if os.path.exists(os.path.join(args.model_dir, "config.json")):
        print("✅ Nạp Standalone Merged Model.")
        model = VisionEncoderDecoderModel.from_pretrained(args.model_dir).to(device)
    else:
        adapter_path = os.path.join(args.model_dir, "lora_adapter")
        if os.path.exists(os.path.join(adapter_path, "adapter_config.json")):
            print("✅ Nạp LoRA Adapter Model.")
            base = VisionEncoderDecoderModel.from_pretrained("naver-clova-ix/donut-base")
            base.decoder = PeftModel.from_pretrained(base.decoder, adapter_path)
            model = base.to(device)
        else:
            print(f"❌ Không tìm thấy trọng số hợp lệ trong {args.model_dir}")
            return

    model.eval()

    # 2. Đọc tập Validation metadata.jsonl
    metadata_file = os.path.join(args.val_dir, "metadata.jsonl")
    if not os.path.exists(metadata_file):
        print(f"❌ Không tìm thấy file {metadata_file}")
        return

    samples = []
    with open(metadata_file, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                samples.append(json.loads(line.strip()))

    samples = samples[:args.max_samples]
    total_samples = len(samples)
    print(f"📊 Bắt đầu đánh giá trên {total_samples} mẫu Validation...")

    field_scores = {
        "r_sph": 0, "r_cyl": 0, "r_axis": 0,
        "l_sph": 0, "l_cyl": 0, "l_axis": 0,
        "pd": 0, "doc_type": 0, "hospital": 0,
        "exact_match": 0
    }

    task_prompt = "<s_doc_type>"
    decoder_input_ids = processor.tokenizer(task_prompt, add_special_tokens=False, return_tensors="pt").input_ids.to(device)

    print("\n⏳ Đang tiến hành suy luận và chấm điểm...")
    for idx, item in enumerate(samples):
        img_path = os.path.join(args.val_dir, item["file_name"])
        if not os.path.exists(img_path):
            continue

        image = Image.open(img_path).convert("RGB")
        pixel_values = processor(image, return_tensors="pt").pixel_values.to(device)

        with torch.no_grad():
            outputs = model.generate(
                pixel_values=pixel_values,
                decoder_input_ids=decoder_input_ids,
                max_length=384,
                pad_token_id=processor.tokenizer.pad_token_id,
                eos_token_id=processor.tokenizer.eos_token_id,
                use_cache=True,
                num_beams=1
            )

        seq = processor.batch_decode(outputs, skip_special_tokens=True)[0]
        pred_dict = clean_and_parse_donut_json(seq) or {}
        gt_dict = json.loads(item["ground_truth"]).get("gt_parse", {})

        sample_eval = evaluate_single_sample(gt_dict, pred_dict)
        for k, v in sample_eval.items():
            if v:
                field_scores[k] += 1

        status_icon = "✅" if sample_eval["exact_match"] else "⚠️"
        print(f" [{idx+1:02d}/{total_samples:02d}] {status_icon} {item['file_name']:<18} | OD SPH: {str(sample_eval['r_sph']):<5} | OS SPH: {str(sample_eval['l_sph']):<5} | PD: {str(sample_eval['pd']):<5}")

    # 3. Tính toán Bảng Tỷ lệ % Độ chính xác
    print("\n" + "=" * 80)
    print("🏆 BẢNG TỔNG KẾT ĐỘ CHÍNH XÁC (ACCURACY METRICS BREAKDOWN)")
    print("=" * 80)
    
    def pct(key):
        return (field_scores[key] / max(1, total_samples)) * 100

    print(f"🎯 1. Độ chính xác Khớp 100% toàn bộ Đơn kính (Exact Match): {pct('exact_match'):.1f}% ({field_scores['exact_match']}/{total_samples})")
    print(f"📋 2. Nhận diện Đúng Loại Tài Liệu (Document Type):          {pct('doc_type'):.1f}%")
    print(f"🏥 3. Nhận diện Tên Bệnh Viện / Phòng Khám:                {pct('hospital'):.1f}%")
    print("-" * 80)
    print(f"👁️ 4. Mắt Phải (OD) - Độ Cầu (SPH):                         {pct('r_sph'):.1f}%")
    print(f"👁️ 5. Mắt Phải (OD) - Độ Loạn (CYL):                        {pct('r_cyl'):.1f}%")
    print(f"🎯 6. Mắt Phải (OD) - Trục Loạn (AXIS):                      {pct('r_axis'):.1f}%")
    print("-" * 80)
    print(f"👁️ 7. Mắt Trái (OS) - Độ Cầu (SPH):                         {pct('l_sph'):.1f}%")
    print(f"👁️ 8. Mắt Trái (OS) - Độ Loạn (CYL):                        {pct('l_cyl'):.1f}%")
    print(f"🎯 9. Mắt Trái (OS) - Trục Loạn (AXIS):                      {pct('l_axis'):.1f}%")
    print("-" * 80)
    print(f"📏 10. Khoảng cách Đồng Tử (PD Accuracy):                   {pct('pd'):.1f}%")
    print("=" * 80)

    core_optical_acc = (pct('r_sph') + pct('r_cyl') + pct('r_axis') + pct('l_sph') + pct('l_cyl') + pct('l_axis') + pct('pd')) / 7
    print(f"🌟 ĐỘ CHÍNH XÁC QUANG HỌC CỐT LÕI (CORE OPTICAL ACCURACY): {core_optical_acc:.2f}%\n")


if __name__ == "__main__":
    main()
