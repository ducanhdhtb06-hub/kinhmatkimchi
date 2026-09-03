#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
OptiStyle Pro - Multimodal AI & Optical Evaluation Harness (deepseek_harness.py)
================================================================================
Công cụ kiểm thử & đánh giá độc lập (Evaluation Harness) tích hợp chính thức:
  1. Google Gemini API (gemini-2.0-flash, gemini-1.5-flash, gemini-1.5-pro)
  2. DeepSeek API (deepseek-chat V3, deepseek-reasoner R1)

Đánh giá tự động:
  - Trích xuất thông số khúc xạ nhãn khoa (SPH, CYL, AXIS, PD).
  - Kiểm định chính sách Zero-Hallucination (Chống bịa số độ trên hóa đơn, giấy khám tổng quát).
  - So sánh độ chính xác và độ trễ (latency) giữa các mô hình AI thật.
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

SYSTEM_PROMPT = (
    "Bạn là Hệ Thống Phân Tích & Kiểm Duyệt Khúc Xạ Mắt Chuyên Nghiệp. "
    "Nhiệm vụ của bạn là kiểm tra văn bản đầu vào và trích xuất thông số y tế thành JSON:\n"
    "1. Nếu văn bản KHÔNG PHẢI là đơn kính thuốc hoặc phiếu đo mắt (ví dụ: hóa đơn mua sắm, giấy khám sức khỏe tổng quát, thực đơn...):\n"
    "   => Trả về JSON: {\"is_prescription\": false, \"message\": \"Không phải đơn kính mắt.\"}\n"
    "   => TUYỆT ĐỐI KHÔNG BỊA SỐ ĐỘ.\n"
    "2. Nếu ĐÚNG là đơn kính / phiếu đo khúc xạ:\n"
    "   => Trả về JSON chứa: is_prescription (true), right_sph (float), right_cyl (float), right_axis (int), left_sph (float), left_cyl (float), left_axis (int), pd (float), recommended_index (float).\n"
    "Luôn trả về duy nhất một khối JSON hợp lệ."
)


# ============================ HARNESS ENGINE ============================
class OpticalEvaluationHarness:
    """Harness chuyên dụng hỗ trợ đa mô hình AI: DeepSeek và Google Gemini."""

    def __init__(self, provider: str = "deepseek", model: Optional[str] = None, api_key: Optional[str] = None):
        self.provider = provider.lower()
        self.api_key = api_key or os.environ.get(
            "GEMINI_API_KEY" if self.provider == "gemini" else "DEEPSEEK_API_KEY", ""
        )
        if not self.api_key and self.provider == "gemini":
            self.api_key = os.environ.get("GOOGLE_API_KEY", "")
            if not self.api_key and os.path.exists(".gemini_api_key"):
                with open(".gemini_api_key", "r") as f:
                    self.api_key = f.read().strip()

        if self.provider == "gemini":
            self.model = model or "gemini-2.0-flash"
        else:
            self.model = model or "deepseek-chat"

    def call_ai(self, prompt: str) -> Dict[str, Any]:
        """Điều hướng gọi API theo provider được chọn."""
        if not self.api_key:
            return self._mock_response(prompt)

        if self.provider == "gemini":
            return self._call_real_gemini(prompt)
        else:
            return self._call_real_deepseek(prompt)

    def _call_real_gemini(self, prompt: str) -> Dict[str, Any]:
        """Gửi prompt trực tiếp tới Google Generative Language REST API với cơ chế tự động Fallback model."""
        start_time = time.time()
        fallback_models = [self.model, "gemini-3.5-flash", "gemini-3.6-flash", "gemini-flash-latest"]
        
        last_error = None
        for m_name in dict.fromkeys(fallback_models):  # giữ thứ tự và loại bỏ trùng
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{m_name}:generateContent?key={self.api_key}"
            payload = {
                "contents": [{"parts": [{"text": prompt}]}],
                "systemInstruction": {"parts": [{"text": SYSTEM_PROMPT}]},
                "generationConfig": {"responseMimeType": "application/json", "temperature": 0.0}
            }

            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST"
            )

            try:
                with urllib.request.urlopen(req, timeout=30) as resp:
                    raw_res = json.loads(resp.read().decode("utf-8"))
                    latency = round(time.time() - start_time, 2)
                    candidate = raw_res.get("candidates", [{}])[0]
                    text_content = candidate.get("content", {}).get("parts", [{}])[0].get("text", "{}")
                    parsed_json = json.loads(text_content)
                    return {
                        "success": True,
                        "latency_sec": latency,
                        "provider": f"Google Gemini ({raw_res.get('modelVersion', m_name)})",
                        "model": m_name,
                        "data": parsed_json,
                        "usage": raw_res.get("usageMetadata", {})
                    }
            except Exception as e:
                last_error = e
                time.sleep(0.5)
                continue

        return {
            "success": False,
            "error": f"Gemini API Error: {str(last_error)}",
            "latency_sec": round(time.time() - start_time, 2),
            "provider": "Google Gemini"
        }

    def _call_real_deepseek(self, prompt: str) -> Dict[str, Any]:
        """Gửi prompt tới DeepSeek API chính thức."""
        api_url = "https://api.deepseek.com/v1/chat/completions"
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ],
            "response_format": {"type": "json_object"},
            "temperature": 0.0
        }

        req = urllib.request.Request(
            api_url,
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
                latency = round(time.time() - start_time, 2)
                content_str = raw_res["choices"][0]["message"]["content"]
                parsed_json = json.loads(content_str)
                return {
                    "success": True,
                    "latency_sec": latency,
                    "provider": "DeepSeek (Official API)",
                    "model": self.model,
                    "data": parsed_json
                }
        except Exception as e:
            return {
                "success": False,
                "error": f"DeepSeek API Error: {str(e)}",
                "latency_sec": round(time.time() - start_time, 2),
                "provider": "DeepSeek"
            }

    def _mock_response(self, prompt: str) -> Dict[str, Any]:
        """Chế độ Mock Offline mô phỏng khi chưa nhập API Key."""
        prompt_lower = prompt.lower()
        time.sleep(0.04)

        if any(w in prompt_lower for w in ["hóa đơn", "siêu thị", "huyết áp", "khám sức khỏe", "co.opmart"]):
            return {
                "success": True,
                "latency_sec": 0.04,
                "provider": "Offline Mock Heuristics (Chưa có API Key)",
                "data": {"is_prescription": False, "message": "Phát hiện tài liệu không phải đơn kính nhãn khoa."}
            }

        if "-1.75" in prompt:
            return {
                "success": True,
                "latency_sec": 0.04,
                "provider": "Offline Mock Heuristics (Chưa có API Key)",
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

        if "-3.50" in prompt:
            return {
                "success": True,
                "latency_sec": 0.04,
                "provider": "Offline Mock Heuristics (Chưa có API Key)",
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

        if "-6.50" in prompt:
            return {
                "success": True,
                "latency_sec": 0.04,
                "provider": "Offline Mock Heuristics (Chưa có API Key)",
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
            "latency_sec": 0.04,
            "provider": "Offline Mock Heuristics (Chưa có API Key)",
            "data": {"is_prescription": False}
        }

    def run_benchmark(self) -> Dict[str, Any]:
        """Chạy toàn bộ Harness Benchmark Suite và tổng hợp điểm số."""
        print("=" * 80)
        print("🚀 ĐANG CHẠY OPTICAL & MEDICAL AI EVALUATION HARNESS")
        print(f"📌 Provider: {self.provider.upper()} | Model: {self.model}")
        print(f"🔑 Chế độ: {'API Trực Tiếp' if self.api_key else '⚠️ Mock Engine (Offline Heuristics - Cần cung cấp API Key để gọi API thật)'}")
        print("=" * 80)

        total_cases = len(BENCHMARK_PRESCRIPTION_TESTS)
        passed_cases = 0
        results = []

        for idx, test_case in enumerate(BENCHMARK_PRESCRIPTION_TESTS, 1):
            print(f"\n[Test {idx:02d}/{total_cases:02d}] {test_case['id']} - {test_case['description']}")
            prompt = f"Hãy phân tích và trích xuất dữ liệu từ văn bản y tế sau:\n{test_case['input_text']}"
            
            res = self.call_ai(prompt)
            if not res.get("success"):
                print(f"  ❌ Lỗi gọi AI: {res.get('error')}")
                results.append({"id": test_case["id"], "passed": False, "error": res.get("error")})
                continue

            extracted = res.get("data", {})
            gt = test_case["ground_truth"]

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
                print(f"  ✅ [PASS] Trích xuất chính xác (Độ trễ: {res.get('latency_sec')}s | Engine: {res.get('provider')})")
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
        print(f"📊 KẾT QUẢ ĐÁNH GIÁ: {passed_cases}/{total_cases} CASES ĐẠT ({accuracy}% ACCURACY)")
        print("=" * 80)

        return {
            "total": total_cases,
            "passed": passed_cases,
            "accuracy_percent": accuracy,
            "results": results
        }


# ============================ CLI ENTRYPOINT ============================
def main():
    parser = argparse.ArgumentParser(description="Multimodal AI Optical Evaluation Harness")
    parser.add_argument("--provider", type=str, default="deepseek", choices=["deepseek", "gemini"], help="Nhà cung cấp AI (deepseek hoặc gemini)")
    parser.add_argument("--model", type=str, default=None, help="Tên model (Ví dụ: gemini-2.0-flash, gemini-1.5-pro, deepseek-chat, deepseek-reasoner)")
    parser.add_argument("--api_key", type=str, default=None, help="API Key của DeepSeek hoặc Google Gemini")
    parser.add_argument("--export_json", type=str, default=None, help="Xuất kết quả benchmark ra file JSON")
    args = parser.parse_args()

    harness = OpticalEvaluationHarness(provider=args.provider, model=args.model, api_key=args.api_key)
    summary = harness.run_benchmark()

    if args.export_json:
        with open(args.export_json, "w", encoding="utf-8") as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
        print(f"💾 Đã lưu báo cáo chi tiết vào: {args.export_json}")

    sys.exit(0 if summary["passed"] == summary["total"] else 1)


if __name__ == "__main__":
    main()
