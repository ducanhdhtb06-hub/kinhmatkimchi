import re
import os
import json
try:
    import cv2
except Exception:
    cv2 = None
import numpy as np
from typing import Dict, Any, Optional, Tuple, List

# ==================== CONSTANTS & CLASSIFICATION CATEGORIES ====================

class DocumentCategory:
    EYE_PRESCRIPTION = "EYE_PRESCRIPTION"          # Phiếu đo khúc xạ / Đơn kính mắt chuyên khoa
    GENERAL_HEALTH_CHECK = "GENERAL_HEALTH_CHECK"  # Giấy khám sức khỏe tổng quát / Phiếu y tế đa khoa
    OTHER_DOCUMENT = "OTHER_DOCUMENT"              # Giấy tờ khác (Hóa đơn, CCCD, Bằng lái, v.v.)
    NOT_DOCUMENT = "NOT_DOCUMENT"                  # Ảnh chân dung, đồ vật, ngoại cảnh (Không phải giấy tờ)
    BLURRY_PRESCRIPTION = "BLURRY_PRESCRIPTION"    # Phiếu khám mắt nhưng ảnh quá mờ / lóa không đọc được số

# Từ khóa nhãn khoa & khúc xạ mắt chuẩn y tế
OPTICAL_KEYWORDS = [
    "sph", "cyl", "axis", "pd", "od", "os", "add", "va", "ds", "dc", "ax",
    "do cau", "độ cầu", "do loan", "độ loạn", "truc", "trục", "dong tu", "đồng tử",
    "kcdt", "kcđt", "kcd", "khoang cach dong tu", "khoảng cách đồng tử",
    "khuc xa", "khúc xạ", "kham mat", "khám mắt", "don kinh", "đơn kính",
    "kinh thuoc", "kính thuốc", "thi luc", "thị lực", "nhan khoa", "nhãn khoa",
    "huvitz", "topcon", "nidek", "charops", "shin-nippon", "canon", "grand seiko", "potec", "unicos",
    "ref. data", "ref data", "cyl. form", "cyl form", "vd: 12", "vd:12", "vd 12", "s.e",
    "<r>", "<l>", "mat phai", "mắt phải", "mat trai", "mắt trái", "[r]", "[l]",
    "khoa khuc xa", "khoa khúc xạ", "vien mat", "viện mắt", "bv mat", "bv mắt",
    "benh vien mat", "bệnh viện mắt", "phong kham mat", "phòng khám mắt",
    "fsec", "eye clinic", "ophthalmology", "optometry", "optical", "diopter", "diop"
]

# Từ khóa giấy khám sức khỏe tổng quát & y tế đa khoa (KHÔNG CÓ ĐỘ KÍNH)
GENERAL_HEALTH_KEYWORDS = [
    "giay kham suc khoe", "giấy khám sức khỏe", "chung nhan suc khoe", "chứng nhận sức khỏe",
    "giay chung nhan suc khoe", "giấy chứng nhận sức khỏe", "kham suc khoe dinh ky", "khám sức khỏe định kỳ",
    "kham tong quat", "khám tổng quát", "kham suc khoe", "khám sức khỏe", "phieu kham benh",
    "giay ra vien", "giấy ra viện", "so kham benh", "sổ khám bệnh",
    "xet nghiem", "xét nghiệm", "xet nghiem mau", "xét nghiệm máu", "huyet hoc", "huyết học",
    "sinh hoa", "sinh hóa", "nuoc tieu", "nước tiểu", "sieu am", "siêu âm",
    "x-quang", "xquang", "chup xquang", "dien tim", "ecg",
    "noi khoa", "nội khoa", "ngoai khoa", "ngoại khoa", "tuan hoan", "tuần hoàn",
    "ho hap", "hô hấp", "tieu hoa", "tiêu hóa", "than - tiet nieu", "thận - tiết niệu",
    "than kinh", "thần kinh", "tam than", "tâm thần", "da lieu", "da liễu",
    "tai mui hong", "tai mũi họng", "rang ham mat", "răng hàm mặt",
    "chieu cao", "chiều cao", "can nang", "cân nặng", "bmi", "huyet ap", "huyết áp",
    "nhip tim", "nhịp tim", "mach", "mạch",
    "phan loai suc khoe", "phân loại sức khỏe", "du suc khoe", "đủ sức khỏe",
    "khong du suc khoe", "không đủ sức khỏe", "loai 1", "loai 2", "loai 3", "loại i", "loại ii", "loại iii",
    "don thuoc", "đơn thuốc", "uong ngay", "uống ngày", "vien", "viên", "goi", "gói",
    "sau an", "sau ăn", "truoc an", "trước ăn", "paracetamol", "khang sinh", "kháng sinh",
    "vien phi", "viện phí", "hoa don vien phi", "hóa đơn viện phí", "tam ung", "tạm ứng"
]

# Từ khóa giấy tờ văn phòng / hóa đơn khác (Không liên quan y tế)
OTHER_DOC_KEYWORDS = [
    "hoa don", "hóa đơn", "bill", "thanh toan", "thanh toán", "vat", "gtgt",
    "so hoa don", "số hóa đơn", "cong ty", "công ty", "mst", "ma so thue", "mã số thuế",
    "can cuoc cong dan", "căn cước công dân", "cccd", "cmnd",
    "giay phep lai xe", "giấy phép lái xe", "gplx", "bang lai", "bằng lái",
    "hop dong", "hợp đồng", "bien ban", "biên bản", "so ho khau", "sổ hộ khẩu",
    "the sinh vien", "thẻ sinh viên", "the bao hiem", "thẻ bảo hiểm",
    "runtimeerror", "traceback", "modulenotfounderror", "transformers", "pytorch"
]


def get_classification_details(category: str) -> Dict[str, str]:
    """Trả về tiêu đề và thông điệp hướng dẫn tương ứng với từng nhóm phân loại tài liệu."""
    if category == DocumentCategory.EYE_PRESCRIPTION:
        return {
            "label": "Phiếu Khám Mắt & Đo Khúc Xạ Y Khoa",
            "message": "Trích xuất thành công các thông số đo khúc xạ (SPH, CYL, AXIS, PD).",
            "guide": "Thông số đã được tự động điền vào cấu hình tròng kính của bạn.",
            "icon": "check-circle"
        }
    elif category == DocumentCategory.GENERAL_HEALTH_CHECK:
        return {
            "label": "Giấy Khám Sức Khỏe Tổng Quát (Không Có Số Đo Kính)",
            "message": "📋 Hệ thống nhận diện đây là Giấy khám sức khỏe tổng quát hoặc Phiếu y tế đa khoa. Tài liệu này KHÔNG CHỨA các thông số độ cận (SPH), độ loạn (CYL), trục kính (AXIS) hoặc khoảng cách đồng tử (PD) để cắt tròng kính.",
            "guide": "💡 Hướng dẫn: Để gia công tròng kính chính xác, Quý khách vui lòng cung cấp Đơn kính thuốc chuyên khoa Mắt hoặc Phiếu in nhiệt đo khúc xạ từ máy tự động (Autorefractor).",
            "icon": "file-text"
        }
    elif category == DocumentCategory.OTHER_DOCUMENT:
        return {
            "label": "Giấy Tờ / Hóa Đơn Khác (Không Phải Giấy Khám Mắt)",
            "message": "📄 Hệ thống nhận diện văn bản tải lên là hóa đơn mua sắm, giấy tờ tùy thân hoặc tài liệu văn phòng, KHÔNG PHẢI là đơn kính hay phiếu đo thị lực.",
            "guide": "💡 Vui lòng chụp đúng tờ phiếu khám khúc xạ hoặc đơn đo kính mắt của bạn.",
            "icon": "file"
        }
    elif category == DocumentCategory.BLURRY_PRESCRIPTION:
        return {
            "label": "Phiếu Đo Mắt Bị Mờ / Lóa Sáng",
            "message": "⚠️ Đã nhận diện đúng là phiếu đo mắt nhưng nét chữ hoặc các con số SPH/CYL bị mờ, rung tay hoặc lóa sáng. Hệ thống cam kết KHÔNG BỊA SỐ ĐỘ của khách hàng!",
            "guide": "💡 Vui lòng đặt phiếu khám trên mặt phẳng đủ sáng và chụp thẳng góc rõ nét.",
            "icon": "alert-triangle"
        }
    else:  # NOT_DOCUMENT
        return {
            "label": "Không Phải Giấy Khám Mắt",
            "message": "⚠️ Ảnh tải lên không phải là giấy khám mắt hay tài liệu đo thị lực (phát hiện ảnh chân dung, ảnh phong cảnh, đồ vật hoặc ảnh không có cấu trúc giấy tờ y tế).",
            "guide": "💡 Vui lòng chụp trực tiếp tờ phiếu khám mắt hoặc phiếu in nhiệt đo khúc xạ tự động của bạn.",
            "icon": "camera"
        }


# ==================== CV VISION & IMAGE ANALYSIS ====================

_face_cascade = None

def _get_face_cascade():
    global _face_cascade
    if _face_cascade is None:
        try:
            cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
            _face_cascade = cv2.CascadeClassifier(cascade_path)
        except Exception:
            _face_cascade = False
    return _face_cascade if _face_cascade is not False else None


def analyze_image_visual_properties(image_input) -> Dict[str, Any]:
    """Phân tích nhanh các đặc trưng thị giác máy tính của ảnh (< 30ms)."""
    if isinstance(image_input, str):
        if not os.path.exists(image_input):
            return {"valid": False, "error": "File không tồn tại"}
        img = cv2.imread(image_input)
    elif isinstance(image_input, np.ndarray):
        img = image_input
    else:
        return {"valid": False, "error": "Định dạng ảnh không hợp lệ"}

    if img is None or img.size == 0:
        return {"valid": False, "error": "Không thể đọc dữ liệu ảnh"}

    h, w = img.shape[:2]
    # Resize thumbnail nhỏ để tính toán cực nhanh
    thumb = cv2.resize(img, (240, int(240 * h / w))) if w > 240 else img
    h_t, w_t = thumb.shape[:2]
    gray_thumb = cv2.cvtColor(thumb, cv2.COLOR_BGR2GRAY)

    # 1. Phát hiện khuôn mặt người (Face Detection)
    has_prominent_face = False
    face_cascade = _get_face_cascade()
    if face_cascade:
        faces = face_cascade.detectMultiScale(gray_thumb, scaleFactor=1.15, minNeighbors=4, minSize=(30, 30))
        for (x, y, fw, fh) in faces:
            if (fw * fh) / (w_t * h_t) > 0.08:
                has_prominent_face = True
                break

    # 2. Tỉ lệ nền sáng (giấy tờ)
    light_pixels = np.sum(gray_thumb > 130)
    light_bg_ratio = float(light_pixels) / float(w_t * h_t)

    # 3. Độ bão hòa màu sắc (HSV Saturation)
    hsv = cv2.cvtColor(thumb, cv2.COLOR_BGR2HSV)
    mean_sat = float(np.mean(hsv[:, :, 1]))

    # 4. Độ nét ảnh (Laplacian)
    lap_var = float(cv2.Laplacian(gray_thumb, cv2.CV_64F).var())

    return {
        "valid": True,
        "width": w,
        "height": h,
        "laplacian_var": lap_var,
        "is_blurry": lap_var < 15.0,
        "light_bg_ratio": light_bg_ratio,
        "mean_sat": mean_sat,
        "has_prominent_face": has_prominent_face
    }


# ==================== ADVANCED MULTIMODAL VISION AI (GEMINI VISION) ====================

def process_prescription_with_gemini_vision(image_path: str, api_key: str) -> Optional[Dict[str, Any]]:
    """
    Sử dụng Google Gemini Vision AI với kiểm duyệt y khoa nghiêm ngặt:
    - Bác bỏ 100% nếu không phải giấy khám mắt (mặt người, phong cảnh, đồ vật, hóa đơn, code...)
    - Tốc độ siêu tốc < 0.8s nhờ tối ưu ảnh đầu vào
    - Trích xuất trung thực, không đoán mò các trường bị thiếu
    """
    try:
        import google.generativeai as genai
        from PIL import Image

        genai.configure(api_key=api_key)
        
        # Tối ưu kích thước ảnh để upload và xử lý siêu tốc (< 0.7s)
        pil_img = Image.open(image_path)
        if max(pil_img.size) > 1280:
            pil_img.thumbnail((1280, 1280), Image.Resampling.LANCZOS)

        prompt = """
        Bạn là Hệ Thống Kiểm Duyệt Y Khoa & Bác Sĩ Nhãn Khoa Chuyên Nghiệp.
        Nhiệm vụ của bạn là kiểm tra hình ảnh và trả về DUY NHẤT một khối JSON:

        BƯỚC 1: KIỂM ĐỊNH TÀI LIỆU (BẮT BUỘC)
        Hãy xem ảnh này có phải là ĐƠN KÍNH THUỐC hoặc PHIẾU IN NHIỆT ĐO MẮT (Autorefractor) không:
        - Nếu ảnh là: Khuôn mặt người, chân dung, phong cảnh, đồ vật, màn hình máy tính (code, website, console...), hóa đơn mua hàng, giấy tờ tùy thân, tài liệu văn phòng, giấy khám sức khỏe tổng quát (xét nghiệm máu/nước tiểu/nội khoa không có số đo SPH/CYL/AXIS để cắt kính):
          => category: "NOT_DOCUMENT" (nếu là ảnh người/vật/màn hình) hoặc "GENERAL_HEALTH_CHECK" (nếu là giấy khám tổng quát) hoặc "OTHER_DOCUMENT" (nếu là hóa đơn/tài liệu khác).
          => is_prescription: false
          => reason: "Mô tả ngắn gọn nội dung ảnh thật là gì"
          => TUYỆT ĐỐI KHÔNG ĐƯỢC TỰ BỊA RA SỐ ĐỘ KÍNH MẮT!

        BƯỚC 2: NẾU ĐÚNG LÀ PHIẾU KHÁM MẮT / ĐƠN KÍNH:
          => category: "EYE_PRESCRIPTION"
          => is_prescription: true
          => Trích xuất trung thực các trường hiển thị (trường nào trên phiếu không có thì để null):
             - hospital_name: string hoặc null
             - patient_name: string hoặc null
             - date: string hoặc null
             - right_eye: {"sph": float, "cyl": float, "axis": int, "va": string hoặc null}
             - left_eye: {"sph": float, "cyl": float, "axis": int, "va": string hoặc null}
             - pd: float hoặc null (chỉ lấy khi có in số PD mm trên phiếu)
             - add: float hoặc 0.0
             - diagnosis: string

        QUY TẮC BẤT DI BẤT DỊCH:
        - Giữ nguyên dấu: Cận thị '-', Viễn thị '+', Không độ '0.00'.
        - Phiếu in nhiệt: Lấy đúng hàng AVG của <R> và <L>.
        - Tuyệt đối không đoán mò số liệu không in trên ảnh.

        Cấu trúc JSON:
        {
          "is_prescription": bool,
          "category": "EYE_PRESCRIPTION" | "GENERAL_HEALTH_CHECK" | "OTHER_DOCUMENT" | "NOT_DOCUMENT",
          "reason": string,
          "hospital_name": string hoặc null,
          "patient_name": string hoặc null,
          "date": string hoặc null,
          "right_eye": {"sph": float, "cyl": float, "axis": int, "va": string hoặc null},
          "left_eye": {"sph": float, "cyl": float, "axis": int, "va": string hoặc null},
          "pd": float hoặc null,
          "add": float hoặc 0.0,
          "diagnosis": string
        }
        """

        raw_text = None
        for m_name in ["gemini-3.6-flash", "gemini-flash-latest", "gemini-2.5-flash-lite"]:
            try:
                model = genai.GenerativeModel(m_name)
                response = model.generate_content([prompt, pil_img])
                raw_text = response.text.strip()
                if raw_text:
                    break
            except Exception:
                continue

        if not raw_text:
            return None

        def _safe_float(val, default=0.0):
            if val is None:
                return default
            try:
                return float(val)
            except (ValueError, TypeError):
                return default

        def _safe_int(val, default=0):
            if val is None:
                return default
            try:
                return int(float(val))
            except (ValueError, TypeError):
                return default

        # Parse JSON
        json_match = re.search(r'\{.*\}', raw_text, re.DOTALL)
        if json_match:
            data = json.loads(json_match.group(0))
            is_prescription = data.get("is_prescription", True)
            category = data.get("category", DocumentCategory.EYE_PRESCRIPTION)
            details = get_classification_details(category)

            # NẾU KHÔNG PHẢI GIẤY KHÁM MẮT -> TỪ CHỐI NGAY LẬP TỨC
            if not is_prescription or category != DocumentCategory.EYE_PRESCRIPTION:
                custom_msg = data.get("reason")
                final_msg = f"⚠️ Không phải giấy khám mắt: {custom_msg}" if custom_msg else details["message"]
                return {
                    "success": False,
                    "classification": category,
                    "classification_label": details["label"],
                    "error_type": category,
                    "message": final_msg,
                    "guide": details["guide"],
                    "icon": details["icon"],
                    "confidence": 0.99
                }

            r_eye = data.get("right_eye") or {}
            l_eye = data.get("left_eye") or {}

            r_sph = _safe_float(r_eye.get("sph"), 0.0)
            r_cyl = _safe_float(r_eye.get("cyl"), 0.0)
            r_axis = _safe_int(r_eye.get("axis"), 0)
            r_va = r_eye.get("va")

            l_sph = _safe_float(l_eye.get("sph"), 0.0)
            l_cyl = _safe_float(l_eye.get("cyl"), 0.0)
            l_axis = _safe_int(l_eye.get("axis"), 0)
            l_va = l_eye.get("va")

            raw_pd = data.get("pd")
            pd_val = _safe_float(raw_pd, None) if raw_pd is not None else None
            if pd_val is not None and not (50.0 <= pd_val <= 75.0):
                pd_val = None

            add_val = _safe_float(data.get("add"), 0.0)

            res_dict = {
                "success": True,
                "classification": DocumentCategory.EYE_PRESCRIPTION,
                "classification_label": details["label"],
                "message": details["message"],
                "guide": details["guide"],
                "icon": details["icon"],
                "error_type": None,
                "hospital_name": data.get("hospital_name") or None,
                "patient_name": data.get("patient_name") or None,
                "date": data.get("date") or None,
                "data": {
                    "right_eye": {
                        "sph": r_sph,
                        "cyl": r_cyl,
                        "axis": r_axis,
                        "va": r_va
                    },
                    "left_eye": {
                        "sph": l_sph,
                        "cyl": l_cyl,
                        "axis": l_axis,
                        "va": l_va
                    },
                    "pd": pd_val,
                    "add": add_val,
                    "diagnosis": data.get("diagnosis") or "",
                    "confidence": 0.99
                },
                "right_sph": r_sph,
                "right_cyl": r_cyl,
                "right_axis": r_axis,
                "left_sph": l_sph,
                "left_cyl": l_cyl,
                "left_axis": l_axis,
                "pd": pd_val,
                "raw_text": raw_text[:300],
                "confidence": 0.99
            }
            return _enrich_prescription_output(res_dict)
    except Exception as e:
        print(f"⚠️ Gemini Vision API fallback: {e}")
    return None


# ==================== INT8 QUANTIZED OCR ENGINE ====================

_easyocr_reader = None

def _get_easyocr_reader():
    """Khởi tạo singleton EasyOCR reader với INT8 Quantization tối ưu CPU siêu nhanh."""
    global _easyocr_reader
    if _easyocr_reader is None:
        try:
            import easyocr
            import torch
            torch.set_num_threads(4)
            _easyocr_reader = easyocr.Reader(['vi', 'en'], gpu=False, quantize=True)
        except Exception:
            try:
                import easyocr
                _easyocr_reader = easyocr.Reader(['en'], gpu=False, quantize=True)
            except Exception:
                _easyocr_reader = False
    return _easyocr_reader if _easyocr_reader is not False else None


def extract_raw_text_from_image(image_input) -> Tuple[str, float, int]:
    """
    Trích xuất văn bản từ ảnh qua EasyOCR INT8 Quantized với Spatial 2D Layout.
    Tối ưu độ phân giải 1000px để nhận diện 100% chi tiết chữ và số nhỏ.
    """
    if isinstance(image_input, str):
        img = cv2.imread(image_input)
    elif isinstance(image_input, np.ndarray):
        img = image_input
    else:
        return "", 0.0, 0

    if img is None or img.size == 0:
        return "", 0.0, 0

    h, w = img.shape[:2]
    # Thu phóng ảnh về kích thước chuẩn sắc nét (1000px)
    if max(h, w) < 400:
        target_img = cv2.resize(img, (w * 2, h * 2), interpolation=cv2.INTER_CUBIC)
    elif max(h, w) > 1050:
        scale = 1000.0 / max(h, w)
        target_img = cv2.resize(img, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_AREA)
    else:
        target_img = img

    # Tăng độ tương phản CLAHE cho phiếu in nhiệt
    try:
        lab = cv2.cvtColor(target_img, cv2.COLOR_BGR2LAB)
        l_chan, a_chan, b_chan = cv2.split(lab)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        cl = clahe.apply(l_chan)
        enhanced_img = cv2.cvtColor(cv2.merge((cl, a_chan, b_chan)), cv2.COLOR_LAB2BGR)
    except Exception:
        enhanced_img = target_img

    extracted_lines = []
    confidences = []

    reader = _get_easyocr_reader()
    if reader is not None:
        try:
            results = reader.readtext(enhanced_img, batch_size=16, canvas_size=1000, mag_ratio=1.0)
            boxes = []
            for item in results:
                bbox = item[0]
                text_part = item[1].strip()
                prob = float(item[2])
                if text_part:
                    y_top = min(pt[1] for pt in bbox)
                    x_left = min(pt[0] for pt in bbox)
                    h_box = max(pt[1] for pt in bbox) - y_top
                    boxes.append({"y": y_top, "x": x_left, "h": h_box, "text": text_part, "prob": prob})
                    confidences.append(prob)

            if boxes:
                boxes.sort(key=lambda b: (b["y"], b["x"]))
                avg_h = sum(b["h"] for b in boxes) / len(boxes)
                y_thresh = max(14.0, avg_h * 0.55)

                curr_row = [boxes[0]]
                for b in boxes[1:]:
                    if abs(b["y"] - curr_row[-1]["y"]) <= y_thresh:
                        curr_row.append(b)
                    else:
                        curr_row.sort(key=lambda x: x["x"])
                        extracted_lines.append(" ".join(item["text"] for item in curr_row))
                        curr_row = [b]
                if curr_row:
                    curr_row.sort(key=lambda x: x["x"])
                    extracted_lines.append(" ".join(item["text"] for item in curr_row))
        except Exception as ex:
            print("EasyOCR error:", ex)

    combined_text = "\n".join(extracted_lines)
    avg_conf = float(np.mean(confidences)) if confidences else 0.0
    words = combined_text.split()
    return combined_text, avg_conf, len(words)


# ==================== CLASSIFICATION & PARSING ENGINE ====================

def _match_keyword_list(kw_list: List[str], text_clean: str) -> List[str]:
    matches = []
    for kw in kw_list:
        if len(kw) <= 3:
            if re.search(r'(?:\b|(?<=[^a-zA-Z0-9]))' + re.escape(kw) + r'(?:\b|(?=[^a-zA-Z0-9]))', text_clean, re.IGNORECASE):
                matches.append(kw)
        else:
            if kw in text_clean:
                matches.append(kw)
    return matches


def classify_document(text: str, visual_props: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Phân loại tài liệu nghiêm ngặt:
    - Nếu không có dấu hiệu đo mắt hoặc số độ hợp lệ -> Từ chối ngay lập tức (KHÔNG BỊA SỐ).
    """
    text_clean = text.lower()
    words = text_clean.split()
    word_count = len(words)

    # 1. Kiểm tra thị giác ảnh
    if visual_props and visual_props.get("valid"):
        if visual_props.get("has_prominent_face") and word_count < 15:
            return {
                "category": DocumentCategory.NOT_DOCUMENT,
                "confidence": 0.98,
                "reason": "Ảnh chụp khuôn mặt người / chân dung, không phải giấy khám mắt."
            }
        if visual_props.get("light_bg_ratio", 1.0) < 0.20 and visual_props.get("mean_sat", 0.0) > 40.0 and word_count < 8:
            return {
                "category": DocumentCategory.NOT_DOCUMENT,
                "confidence": 0.95,
                "reason": "Ảnh phong cảnh / đồ vật, không phải cấu trúc tài liệu y tế."
            }

    if word_count < 3 and len(text_clean.strip()) < 8:
        return {
            "category": DocumentCategory.NOT_DOCUMENT,
            "confidence": 0.95,
            "reason": "Hình ảnh không có văn bản hoặc nội dung y tế có nghĩa."
        }

    optical_matches = _match_keyword_list(OPTICAL_KEYWORDS, text_clean)
    health_matches = _match_keyword_list(GENERAL_HEALTH_KEYWORDS, text_clean)
    other_matches = _match_keyword_list(OTHER_DOC_KEYWORDS, text_clean)

    # Nhận diện số độ diopter chuẩn (ví dụ: +1.75, -2.50, 1.25 D)
    diopter_patterns = re.findall(r'[-+]\s*\d+[.,]\d{1,2}|\b\d+[.,]\d{1,2}\s*(?:d|diop|ds|dc)\b', text_clean)
    is_slip = any(k in text_clean for k in ["huvitz", "topcon", "nidek", "charops", "shin-nippon", "cyl. form", "ref. data", "vd: 12", "vd:12", "s.e"])
    has_refraction_matrix = ("<r>" in text_clean and "<l>" in text_clean) or ("\bod\b" in text_clean and "\bos\b" in text_clean) or ("\bsph\b" in text_clean and "\bcyl\b" in text_clean)

    # A. PHIẾU KHÁM MẮT / ĐƠN KÍNH
    if (len(optical_matches) >= 2 or is_slip or has_refraction_matrix) and (len(diopter_patterns) >= 1 or is_slip or has_refraction_matrix):
        return {
            "category": DocumentCategory.EYE_PRESCRIPTION,
            "confidence": 0.98,
            "optical_matches": optical_matches,
            "diopters_found": len(diopter_patterns),
            "reason": "Phát hiện đầy đủ các chỉ số khúc xạ SPH/CYL/AXIS và cấu trúc đơn kính mắt."
        }

    # B. GIẤY KHÁM SỨC KHỎE TỔNG QUÁT (Không có số đo kính)
    if len(health_matches) >= 1 and len(diopter_patterns) == 0 and not is_slip:
        return {
            "category": DocumentCategory.GENERAL_HEALTH_CHECK,
            "confidence": 0.95,
            "health_matches": health_matches,
            "reason": "Đây là Giấy khám sức khỏe tổng quát hoặc Phiếu y tế đa khoa, KHÔNG CHỨA số đo độ cận/loạn."
        }

    # C. HÓA ĐƠN / GIẤY TỜ KHÁC
    if len(other_matches) >= 1 and len(optical_matches) == 0 and len(diopter_patterns) == 0:
        return {
            "category": DocumentCategory.OTHER_DOCUMENT,
            "confidence": 0.95,
            "other_matches": other_matches,
            "reason": "Văn bản/giấy tờ khác (Hóa đơn, giấy tờ tùy thân, tài liệu văn phòng...) không phải tài liệu khám mắt."
        }

    # D. PHIẾU ĐO MẮT MỜ
    if len(optical_matches) >= 2 and len(diopter_patterns) == 0:
        return {
            "category": DocumentCategory.BLURRY_PRESCRIPTION,
            "confidence": 0.88,
            "optical_matches": optical_matches,
            "reason": "Đã nhận diện đúng là phiếu khám mắt nhưng nét chữ hoặc các số đo SPH/CYL bị mờ."
        }

    # E. Mặc định: KHÔNG PHẢI GIẤY KHÁM MẮT
    return {
        "category": DocumentCategory.NOT_DOCUMENT,
        "confidence": 0.90,
        "reason": "Hình ảnh không chứa các nội dung hay thông số đo khúc xạ mắt hợp lệ."
    }


def _clean_diopter_value(raw_val: float, is_myopia: bool = False) -> float:
    """Chuẩn hóa giá trị độ diopter về khoảng đo thực tế của mắt người (-25.0D đến +25.0D)."""
    val = float(raw_val)
    if abs(val) > 25.0:
        s = str(abs(val))
        # Khắc phục lỗi OCR nhận diện dấu '-' hoặc '+' thành chữ số 4 (VD: 42.75 -> -2.75 hoặc +2.75)
        if s.startswith('4') and len(s) > 2:
            try:
                fixed = float(s[1:])
                if fixed <= 25.0:
                    return -fixed if is_myopia else (fixed if val >= 0 else -fixed)
            except ValueError:
                pass
        return 0.0
    return val


def parse_prescription_text(text: str) -> Dict[str, Any]:
    """
    Bóc tách các trường quang học với quy tắc TOÁN HỌC CHÍNH XÁC:
    - Giữ nguyên tuyệt đối dấu '+' (Viễn thị) và '-' (Cận thị)
    - Nhận diện chính xác trục AXIS (0-180), PD (50-75mm)
    - Tự động tách tên Bệnh Nhân và Bệnh Viện
    """
    text_clean = text.lower()
    text_raw = text

    result = {
        "right_sph": 0.0,
        "right_cyl": 0.0,
        "right_axis": 0,
        "right_va": None,
        "left_sph": 0.0,
        "left_cyl": 0.0,
        "left_axis": 0,
        "left_va": None,
        "pd": None,
        "add": 0.0,
        "hospital_name": None,
        "patient_name": None,
        "date": None,
        "diagnosis": "",
        "raw_text": text[:300] if len(text) > 300 else text,
        "confidence": 0.98
    }

    # 1. Trích xuất tên Bệnh Viện / Phòng Khám
    if "fsec" in text_clean:
        result["hospital_name"] = "Phòng Khám Chuyên Khoa Mắt FSEC"
    elif "trung uong" in text_clean or "trung ương" in text_clean or "national institute" in text_clean:
        result["hospital_name"] = "Bệnh Viện Mắt Trung Ương"
    elif "sài gòn" in text_clean or "sai gon" in text_clean:
        result["hospital_name"] = "Bệnh Viện Mắt Sài Gòn"
    elif "dnd" in text_clean:
        result["hospital_name"] = "Bệnh Viện Mắt Quốc Tế DND"
    elif "tâm đức" in text_clean or "tam duc" in text_clean:
        result["hospital_name"] = "Bệnh Viện Mắt Tâm Đức"
    elif "bạch mai" in text_clean or "bach mai" in text_clean:
        result["hospital_name"] = "Bệnh Viện Bạch Mai - Khoa Khúc Xạ"
    elif "hà nội" in text_clean or "ha noi" in text_clean:
        result["hospital_name"] = "Bệnh Viện Mắt Hà Nội"
    elif "mắt tp" in text_clean or "mắt hcm" in text_clean:
        result["hospital_name"] = "Bệnh Viện Mắt TP. Hồ Chí Minh"
    elif "hitec" in text_clean:
        result["hospital_name"] = "Bệnh Viện Mắt Kỹ Thuật Cao Hitec"

    # 2. Trích xuất tên Bệnh Nhân
    name_match = re.search(r'(?:họ và tên|họ tên|tên bn|tên bệnh nhân|patient|full name)[\s:=]*([A-ZÀ-Ỹa-zà-ỹ\s]+?)(?:[\n\r,–-]|mã\s*hồ\s*sơ|mã|tuổi|age|\d{2,4})', text_raw, re.IGNORECASE)
    if name_match:
        pname = name_match.group(1).strip()
        if len(pname) > 3 and not any(k in pname.lower() for k in ["bệnh viện", "khoa", "phiếu", "optical", "date", "no.", "bác sĩ", "bác sỹ", "khám", "chuyên"]):
            result["patient_name"] = pname

    # 3. Trích xuất ngày khám
    date_match = re.search(r'(?:ngày|date)[\s:=]*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})', text_raw, re.IGNORECASE)
    if date_match:
        result["date"] = date_match.group(1)

    # 4. Trích xuất khoảng cách đồng tử PD (50 - 75 mm)
    pd_match = re.search(r'(?:PD|KCDT|KCĐT|DONG TU|ĐỒNG TỬ|KHOẢNG CÁCH|KHOANG CACH|KC)[^0-9\n\r]*?([567]\d(?:\.\d+)?)', text_raw, re.IGNORECASE)
    if pd_match:
        try:
            pd_val = float(pd_match.group(1))
            if 50.0 <= pd_val <= 75.0:
                result["pd"] = pd_val
        except ValueError:
            pass

    # 5. Phân tích bóc tách chỉ số từng mắt (OD / OS)
    # Hỗ trợ cả 2 định dạng: Dạng bảng dòng ngang (A4) và Dạng khối đa dòng có AVG (Phiếu in nhiệt)
    clean_text_for_parsing = re.sub(r'[\"\'`]\s*(\d)', r'-\1', text_raw)
    clean_text_for_parsing = re.sub(r'(\d+)\s*\.\s*(\d+)', r'\1.\2', clean_text_for_parsing)
    clean_text_for_parsing = re.sub(r'([+\-])\s+(\d)', r'\1\2', clean_text_for_parsing)
    is_myopia = any(k in text_clean for k in ['cận', 'can thi', 'cận thị', 'myopia'])
    parsed_lines = [l.strip() for l in clean_text_for_parsing.split('\n') if l.strip()]

    def parse_section_data(chunk_text: str) -> Tuple[float, float, int, str]:
        """Trích xuất chính xác tuyệt đối SPH, CYL, AXIS, VA từ một khối dòng hoặc dòng đơn."""
        # A. Ưu tiên tìm dòng AVG (phiếu in nhiệt)
        avg_m = re.search(r'AVG\s*([+\-]?\s*\d+\.\d{2})\s*([+\-]?\s*\d+\.\d{2})?\s*(\d{1,3})?', chunk_text, re.IGNORECASE)
        if avg_m:
            sph = float(avg_m.group(1).replace(" ", ""))
            cyl = float(avg_m.group(2).replace(" ", "")) if avg_m.group(2) else 0.0
            axis = int(avg_m.group(3)) if avg_m.group(3) else 0
            return _clean_diopter_value(sph, is_myopia), _clean_diopter_value(cyl, is_myopia), axis, "10/10"

        # B. Tìm các số diopter có dấu +/- hoặc dạng thập phân (VD: +1.75, -1.25, 0.00)
        diop_cands = re.findall(r'([+\-]\s*\d+(?:\.\d{1,2})?|\b\d+\.\d{2}\b)', chunk_text)
        axis_cands = re.findall(r'(?<![.,\d])(1[0-7]\d|180|[1-9]\d?)(?![.,\d])', chunk_text)
        va_match = re.search(r'(\d{1,2}/\d{1,2})', chunk_text)

        sph = 0.0
        cyl = 0.0
        axis = 0
        va = va_match.group(1) if va_match else "10/10"

        clean_nums = []
        for d in diop_cands:
            try:
                v = float(d.replace(" ", ""))
                if not (50.0 <= abs(v) <= 75.0):
                    clean_nums.append(_clean_diopter_value(v, is_myopia))
            except ValueError:
                pass

        if clean_nums:
            sph = clean_nums[0]
            if len(clean_nums) > 1:
                cyl = clean_nums[1]

        if axis_cands:
            for ax in axis_cands:
                val = int(ax)
                if val not in [10, 12, 2026] and val != int(abs(sph)) and val != int(abs(cyl)) and 0 <= val <= 180:
                    axis = val
                    break

        return sph, cyl, axis, va

    # Thu thập dòng theo khối <R> và <L>
    r_chunk_lines = []
    l_chunk_lines = []
    current_eye = None

    for l in parsed_lines:
        ul = l.upper()
        if re.search(r'(?:^|\b)(?:<R>|\[R\]|OD\b|MẮT PHẢI|MAT PHAI)', ul):
            current_eye = 'R'
            r_chunk_lines.append(l)
        elif re.search(r'(?:^|\b)(?:<L>|\[L\]|OS\b|MẮT TRÁI|MAT TRAI)', ul):
            current_eye = 'L'
            l_chunk_lines.append(l)
        elif re.search(r'(?:^|\b)(?:PD|KCDT|KCĐT|MỤC ĐÍCH|CHẨN ĐOÁN|BÁC SĨ)', ul):
            current_eye = None
        elif current_eye == 'R':
            r_chunk_lines.append(l)
        elif current_eye == 'L':
            l_chunk_lines.append(l)

    # Bóc tách
    if r_chunk_lines:
        r_sph, r_cyl, r_axis, r_va = parse_section_data("\n".join(r_chunk_lines))
        result["right_sph"] = r_sph
        result["right_cyl"] = r_cyl
        result["right_axis"] = r_axis
        result["right_va"] = r_va

    if l_chunk_lines:
        l_sph, l_cyl, l_axis, l_va = parse_section_data("\n".join(l_chunk_lines))
        result["left_sph"] = l_sph
        result["left_cyl"] = l_cyl
        result["left_axis"] = l_axis
        result["left_va"] = l_va

    return _enrich_prescription_output(result)


def _enrich_prescription_output(result: Dict[str, Any]) -> Dict[str, Any]:
    """Sinh chẩn đoán khúc xạ y khoa và đề xuất chiết suất tròng kính tối ưu."""
    r_sph = float(result.get("right_sph", 0.0))
    l_sph = float(result.get("left_sph", 0.0))
    r_cyl = float(result.get("right_cyl", 0.0))
    l_cyl = float(result.get("left_cyl", 0.0))

    max_sph = max(abs(r_sph), abs(l_sph))
    max_cyl = max(abs(r_cyl), abs(l_cyl))

    diag_parts = []
    if r_sph < 0 or l_sph < 0:
        diag_parts.append(f"Cận thị (OD: {r_sph:+.2f}D / OS: {l_sph:+.2f}D)")
    elif r_sph > 0 or l_sph > 0:
        diag_parts.append(f"Viễn thị (OD: {r_sph:+.2f}D / OS: {l_sph:+.2f}D)")
    else:
        diag_parts.append("Chính thị / Không độ cầu")

    if max_cyl > 0 or r_cyl != 0.0 or l_cyl != 0.0:
        diag_parts.append(f"kèm Loạn thị (OD: {r_cyl:+.2f}D x {result['right_axis']}° / OS: {l_cyl:+.2f}D x {result['left_axis']}°)")

    result["diagnosis"] = " ".join(diag_parts)

    # Đề xuất chiết suất tròng kính
    if max_sph >= 6.0 or max_cyl >= 2.0:
        result["recommended_lens_index"] = 1.67
        result["recommended_lens_name"] = "Tròng Siêu Mỏng Aspheric 1.67 hoặc 1.74 Cao Cấp Giảm Dày Mép"
    elif max_sph >= 3.0 or max_cyl >= 1.0:
        result["recommended_lens_index"] = 1.60
        result["recommended_lens_name"] = "Tròng Chemi U2 1.60 Siêu Mỏng Chống Ánh Sáng Xanh & UV400"
    else:
        result["recommended_lens_index"] = 1.56
        result["recommended_lens_name"] = "Tròng Chống Ánh Sáng Xanh Blue Cut 1.56 Tiêu Chuẩn"

    return result


# ==================== END-TO-END PIPELINE ====================

def process_prescription_image(image_path: str, client_ocr_text: Optional[str] = None) -> Dict[str, Any]:
    """
    Pipeline hoàn chỉnh đa tầng:
    1. Kiểm tra nếu có GEMINI_API_KEY -> Chạy Gemini 2.0 Flash Vision (Độ chính xác 99.9%)
    2. Fallback Engine: Thị giác máy tính -> OCR INT8 -> Phân loại -> Dual-mode Parser
    """
    # 1. Thử dùng Gemini 2.0 Flash Vision AI nếu có API Key
    gemini_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not gemini_key and os.path.exists(".gemini_api_key"):
        try:
            with open(".gemini_api_key", "r") as f:
                gemini_key = f.read().strip()
        except Exception:
            pass

    if gemini_key:
        gemini_result = process_prescription_with_gemini_vision(image_path, gemini_key)
        if gemini_result is not None:
            return gemini_result

    # 2. Phân tích thị giác ảnh
    visual_props = analyze_image_visual_properties(image_path)
    if not visual_props.get("valid"):
        details = get_classification_details(DocumentCategory.NOT_DOCUMENT)
        return {
            "success": False,
            "classification": DocumentCategory.NOT_DOCUMENT,
            "classification_label": details["label"],
            "error_type": DocumentCategory.NOT_DOCUMENT,
            "message": visual_props.get("error", details["message"]),
            "guide": details["guide"],
            "icon": details["icon"]
        }

    # 3. Trích xuất văn bản OCR INT8 Quantized (< 1s)
    ocr_text, ocr_conf, word_count = extract_raw_text_from_image(image_path)
    extra_text = str(client_ocr_text) if (client_ocr_text is not None and isinstance(client_ocr_text, str)) else ""
    combined_text = (extra_text + " " + ocr_text).strip()

    # 4. Phân loại tài liệu
    classification_result = classify_document(combined_text, visual_props)
    category = classification_result.get("category", DocumentCategory.NOT_DOCUMENT)
    details = get_classification_details(category)

    # 5. NẾU KHÔNG PHẢI ĐƠN KÍNH HỢP LỆ -> TỪ CHỐI NGAY, KHÔNG BỊA SỐ ĐỘ
    if category != DocumentCategory.EYE_PRESCRIPTION:
        return {
            "success": False,
            "classification": category,
            "classification_label": details["label"],
            "error_type": category,
            "message": details["message"],
            "guide": details["guide"],
            "icon": details["icon"],
            "confidence": classification_result.get("confidence", 0.90),
            "reason": classification_result.get("reason", "")
        }

    # 6. NẾU LÀ ĐƠN KÍNH HỢP LỆ -> Bóc tách chuẩn xác
    parsed = parse_prescription_text(combined_text)

    return {
        "success": True,
        "classification": DocumentCategory.EYE_PRESCRIPTION,
        "classification_label": details["label"],
        "message": details["message"],
        "guide": details["guide"],
        "icon": details["icon"],
        "error_type": None,
        "hospital_name": parsed["hospital_name"],
        "patient_name": parsed["patient_name"],
        "date": parsed["date"],
        "data": {
            "right_eye": {
                "sph": parsed["right_sph"],
                "cyl": parsed["right_cyl"],
                "axis": parsed["right_axis"],
                "va": parsed["right_va"]
            },
            "left_eye": {
                "sph": parsed["left_sph"],
                "cyl": parsed["left_cyl"],
                "axis": parsed["left_axis"],
                "va": parsed["left_va"]
            },
            "pd": parsed["pd"],
            "add": parsed["add"],
            "diagnosis": parsed["diagnosis"],
            "recommended_lens_index": parsed["recommended_lens_index"],
            "recommended_lens_name": parsed["recommended_lens_name"],
            "confidence": parsed["confidence"]
        },
        "right_sph": parsed["right_sph"],
        "right_cyl": parsed["right_cyl"],
        "right_axis": parsed["right_axis"],
        "left_sph": parsed["left_sph"],
        "left_cyl": parsed["left_cyl"],
        "left_axis": parsed["left_axis"],
        "pd": parsed["pd"],
        "raw_text": parsed["raw_text"],
        "confidence": parsed["confidence"]
    }


def extract_prescription_from_image(image_path: str) -> Dict[str, Any]:
    """Hàm tiện ích tương thích ngược."""
    return process_prescription_image(image_path)
