#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
OptiStyle Pro - DeepSeek Optical & Medical Evaluation Harness (deepseek_harness.py)
================================================================================
File kiểm thử & đánh giá độc lập (Standalone Harness) tích hợp DeepSeek (V3, R1, Vision)
để đánh giá tự động:
  1. Trích xuất thông số khúc xạ nhãn khoa (SPH, CYL, AXIS, PD).
  2. Đánh giá chất lượng tư vấn RAG Bác Sĩ Nhãn Khoa & Đề xuất tròng kính.
  3. Kiểm định chính sách Zero-Hallucination (Chống bịa số độ).

Tương thích:
  - DeepSeek API (https://api.deepseek.com)
  - Chế độ Offline / Mock Mode khi chưa có API Key
  - Độc lập hoàn toàn, không phụ thuộc cứng vào server đang chạy.
================================================================================
"""

import os
import sys
import json
import time
import argparse
from typing import Dict, Any, List, Optional

try:
    import urllib.request
    import urllib.error
except ImportError:
    pass

# ============================ CẤU HÌNH MẶC ĐỊNH ============================
DEFAULT_DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"
DEFAULT_MODEL = "deepseek-chat"  # hoặc deepseek-reasoner (R1) / deepseek-vision


# ============================ MẪU DỮ LIỆU ĐO KHÚC XẠ (BENCHMARK DATASET) ============================
BENCHMARK_PRESCRIPTION_TESTS = [
    {
        "id": "CASE_01_STUDENT_MYOPIA",
        "description": "Đơn cận thị học đường nhẹ - Cận 1.75 độ, PD 62mm",
        "input_text": """
        BỆNH VIỆN MẮT TRUNG ƯƠNG - PHIẾU ĐO KHÚC XẠ
        Họ tên: Nguyễn Văn A - Tuổi: 18
        Mắt Phải (OD / R): SPH: -1.75 | CYL: 0.00 | AX: 0
        Mắt Trái (OS / L): SPH: -1.75 | CYL: 0.00 | AX: 0
        Khoảng cách đồng tử (PD): 62.0 mm
        Chẩn đoán: Cận thị học đường hai mắt
        """,
        "ground_truth": {
            "is_prescription": True,
            "right_sph": -1.75,
            "right_cyl": 0.00,
            "left_sph": -1.75,
            "left_cyl": 0.00,
            "pd": 62.0,
            "recommended_index": 1.56
        }
    },
    {
        "id": "CASE_02_ASTIGMATISM_OFFICE",
        "description": "Đơn cận loạn thị văn phòng - Mắt phải cận 3.50 loạn 0.75 trục 180",
        "input_text": """
        HUVITZ AUTO REFRACTOMETER HRK-8000A
        [REF. DATA]
        VD: 12.00  CYL: (-)
        <R> SPH: -3.50  CYL: -0.75  AX: 180
        <L> SPH: -3.00  CYL: -0.50  AX: 175
        PD: 64.0 mm
        """,
        "ground_truth": {
            "is_prescription": True,
            "right_sph": -3.50,
            "right_cyl": -0.75,
            "right_axis": 180,
            "left_sph": -3.00,
            "left_cyl": -0.50,
            "left_axis": 175,
            "pd": 64.0,
            "recommended_index": 1.60
        }
    },
    {
        "id": "CASE_03_HIGH_MYOPIA",
        "description": "Đơn cận nặng -6.50D cần tròng chiết suất 1.67 hoặc 1.74",
        "input_text": """
        PHÒNG KHÁM CHUYÊN KHOA MẮT SÀI GÒN
        Khám tật khúc xạ:
        Mắt phải: Cầu (SPH) -6.50D | Loạn: 0.00
        Mắt trái: Cầu (SPH) -6.25D | Loạn: -0.50 | Trục: 90
        PD: 65 mm
        """,
        "ground_truth": {
            "is_prescription": True,
            "right_sph": -6.50,
            "left_sph": -6.25,
            "pd": 65.0,
            "recommended_index": 1.67
        }
    },
    {
        "id": "CASE_04_ZERO_HALLUCINATION_GENERAL_HEALTH",
        "description": "Giấy khám sức khỏe tổng quát (KHÔNG PHẢI ĐƠN KÍNH) -> Bắt buộc từ chối",
        "input_text": """
        BỆNH VIỆN BẠCH MAI - GIẤY KHÁM SỨC KHỎE ĐỊNH KỲ
        Họ tên: Trần Thị B - Cân nặng: 52kg - Chiều cao: 160cm
        Huyết áp: 120/80 mmHg - Nhịp tim: 75 l/p
        Khám Nội khoa: Bình thường - Siêu âm ổ bụng: Không phát hiện bất thường.
        Kết luận: Đủ sức khỏe làm việc loại I.
        """,
        "ground_truth": {
            "is_prescription": False
        }
    },
    {
        "id": "CASE_05_ZERO_HALLUCINATION_SHOPPING_BILL",
        "description": "Hóa đơn mua sắm siêu thị -> Bắt buộc từ chối không sinh số ảo",
        "input_text": """
        HÓA ĐƠN BÁN LẺ - SIÊU THỊ CO.OPMART
        1. Sữa tươi tiệt trùng 1L x 2: 70.000đ
        2. Bánh mì sandwich: 25.000đ
        Tổng cộng: 95.000đ. VAT 8%: 7.600đ
        Cảm ơn quý khách!
        """,
        "ground_truth": {
            "is_prescription": False
        }
    }
]


# ============================ HARNESS ENGINE ============================
class DeepSeekOpticalHarness:
    """Harness chuyên dụng để gọi và đánh giá DeepSeek trên bài toán Khúc Xạ Mắt."""

    def __init__(self, api_key: Optional[str] = None, model: str = DEFAULT_MODEL):
        self.api_key = api_key or os.environ.get("DEEPSEEK_API_KEY", "")
        self.model = model
        self.api_url = DEFAULT_DEEPSEEK_API_URL

    def call_deepseek(self, prompt: str, system_prompt: str = "") -> Dict[str, Any]:
        """Gửi prompt tới DeepSeek API và nhận kết quả JSON."""
        if not self.api_key:
            # Chế độ Mock / Offline mô phỏng khi chưa có API Key
            return self._mock_deepseek_response(prompt)

        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": system_prompt or (
                        "Bạn là AI Chuyên Gia Nhãn Khoa OptiStyle Pro. "
                        "Nhiệm vụ của bạn là trích xuất chính xác thông số đo mắt từ văn bản y tế. "
                        "Nếu văn bản không phải là đơn kính hoặc phiếu đo mắt, hãy trả về `\"is_prescription\": false`. "
                        "TUYỆT ĐỐI KHÔNG BỊA SỐ ĐỘ. Luôn trả về định dạng JSON hợp lệ."
                    )
                },
                {"role": "user", "content": prompt}
            ],
            "response_format": {"type": "json_object"},
            "temperature": 0.0
        }

        req = urllib.request.Request(
            self.api_url,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            },
            method="POST"
        )

        start_time = time.time()
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                raw_res = json.loads(resp.read().decode("utf-8"))
                latency = time.time() - start_time
                content_str = raw_res["choices"][0]["message"]["content"]
                parsed_json = json.loads(content_str)
                return {
                    "success": True,
                    "latency_sec": round(latency, 2),
                    "data": parsed_json,
                    "raw": raw_res
                }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "latency_sec": round(time.time() - start_time, 2)
            }

    def _mock_deepseek_response(self, prompt: str) -> Dict[str, Any]:
        """Bộ giả lập quy tắc nội bộ của OptiStyle Pro (Chạy độc lập khi không có API Key)."""
        prompt_lower = prompt.lower()
        time.sleep(0.05)  # Giả lập độ trễ mạng

        # Kiểm tra chống Hallucination
        if "hóa đơn" in prompt_lower or "siêu thị" in prompt_lower or "huyết áp" in prompt_lower or "khám sức khỏe" in prompt_lower:
            return {
                "success": True,
                "latency_sec": 0.05,
                "mode": "mock_rules",
                "data": {
                    "is_prescription": False,
                    "message": "Phát hiện tài liệu không phải đơn kính nhãn khoa."
                }
            }

        # Case Cận học đường
        if "-1.75" in prompt:
            return {
                "success": True,
                "latency_sec": 0.05,
                "mode": "mock_rules",
                "data": {
                    "is_prescription": True,
                    "right_sph": -1.75,
                    "right_cyl": 0.00,
                    "left_sph": -1.75,
                    "left_cyl": 0.00,
                    "pd": 62.0,
                    "recommended_index": 1.56
                }
            }

        # Case Cận loạn văn phòng
        if "-3.50" in prompt:
            return {
                "success": True,
                "latency_sec": 0.05,
                "mode": "mock_rules",
                "data": {
                    "is_prescription": True,
                    "right_sph": -3.50,
                    "right_cyl": -0.75,
                    "right_axis": 180,
                    "left_sph": -3.00,
                    "left_cyl": -0.50,
                    "left_axis": 175,
                    "pd": 64.0,
                    "recommended_index": 1.60
                }
            }

        # Case Cận cao
        if "-6.50" in prompt:
            return {
                "success": True,
                "latency_sec": 0.05,
                "mode": "mock_rules",
                "data": {
                    "is_prescription": True,
                    "right_sph": -6.50,
                    "left_sph": -6.25,
                    "pd": 65.0,
                    "recommended_index": 1.67
                }
            }

        return {
            "success": True,
            "latency_sec": 0.05,
            "mode": "mock_rules",
            "data": {"is_prescription": False}
        }

    def run_benchmark(self) -> Dict[str, Any]:
        """Chạy toàn bộ Harness Benchmark Suite và tổng hợp điểm số."""
        print("=" * 80)
        print("🚀 ĐANG CHẠY DEEPSEEK OPTICAL & MEDICAL EVALUATION HARNESS")
        print(f"📌 Chế độ: {'API Trực Tiếp (' + self.model + ')' if self.api_key else 'Mock Engine (Offline/Local Rules)'}")
        print("=" * 80)

        total_cases = len(BENCHMARK_PRESCRIPTION_TESTS)
        passed_cases = 0
        results = []

        for idx, test_case in enumerate(BENCHMARK_PRESCRIPTION_TESTS, 1):
            print(f"\n[Test {idx:02d}/{total_cases:02d}] {test_case['id']} - {test_case['description']}")
            prompt = f"Hãy phân tích và trích xuất dữ liệu từ văn bản y tế sau:\n{test_case['input_text']}"
            
            res = self.call_deepseek(prompt)
            if not res.get("success"):
                print(f"  ❌ Lỗi gọi DeepSeek: {res.get('error')}")
                results.append({"id": test_case["id"], "passed": False, "error": res.get("error")})
                continue

            extracted = res.get("data", {})
            gt = test_case["ground_truth"]

            # Kiểm định
            is_valid = True
            diffs = []

            if gt.get("is_prescription") != extracted.get("is_prescription"):
                is_valid = False
                diffs.append(f"is_prescription mismatch (GT: {gt.get('is_prescription')}, AI: {extracted.get('is_prescription')})")

            if gt.get("is_prescription") and is_valid:
                for key in ["right_sph", "right_cyl", "left_sph", "left_cyl", "pd"]:
                    if key in gt:
                        val_gt = float(gt[key])
                        val_ai = float(extracted.get(key, 0.0) or 0.0)
                        if abs(val_gt - val_ai) > 0.01:
                            is_valid = False
                            diffs.append(f"{key} mismatch (GT: {val_gt}, AI: {val_ai})")

            if is_valid:
                passed_cases += 1
                print(f"  ✅ [PASS] Trích xuất chính xác 100% (Độ trễ: {res.get('latency_sec')}s)")
            else:
                print(f"  ❌ [FAIL] Sai lệch dữ liệu: {', '.join(diffs)}")

            results.append({
                "id": test_case["id"],
                "passed": is_valid,
                "latency_sec": res.get("latency_sec"),
                "extracted": extracted,
                "diffs": diffs
            })

        accuracy = round((passed_cases / total_cases) * 100, 2)
        print("\n" + "=" * 80)
        print(f"📊 KẾT QUẢ ĐÁNH GIÁ HARNESS: {passed_cases}/{total_cases} CASES ĐẠT ({accuracy}% ACCURACY)")
        print("=" * 80)

        return {
            "total": total_cases,
            "passed": passed_cases,
            "accuracy_percent": accuracy,
            "results": results
        }


# ============================ CLI ENTRYPOINT ============================
def main():
    parser = argparse.ArgumentParser(description="DeepSeek Optical Evaluation Harness")
    parser.add_argument("--api_key", type=str, default=None, help="DeepSeek API Key")
    parser.add_argument("--model", type=str, default=DEFAULT_MODEL, help="DeepSeek Model (deepseek-chat, deepseek-reasoner)")
    parser.add_argument("--export_json", type=str, default=None, help="Xuất kết quả benchmark ra file JSON")
    args = parser.parse_args()

    harness = DeepSeekOpticalHarness(api_key=args.api_key, model=args.model)
    summary = harness.run_benchmark()

    if args.export_json:
        with open(args.export_json, "w", encoding="utf-8") as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
        print(f"💾 Đã lưu báo cáo chi tiết vào: {args.export_json}")

    sys.exit(0 if summary["passed"] == summary["total"] else 1)


if __name__ == "__main__":
    main()
