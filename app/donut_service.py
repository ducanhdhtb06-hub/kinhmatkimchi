import os
import json
import re
from typing import Dict, Any, Optional
from PIL import Image

# Thư mục chứa trọng số mô hình đã huấn luyện
MODEL_DIR = "models/optical_prescription_model"


def clean_and_parse_donut_json(raw_str: str) -> Optional[Dict[str, Any]]:
    """Làm sạch chuỗi sinh từ Donut và chuyển đổi thành JSON chuẩn."""
    if not raw_str:
        return None
    
    # 1. Bỏ special tokens và ký tự rác
    text = re.sub(r'</?s_doc_type>', '', raw_str)
    text = re.sub(r'[ًَُِْ~]', '', text).strip()
    
    # 2. Sửa lỗi { { double bracket
    text = re.sub(r'\{\s*\{', '{', text)
    
    # 3. Sửa dấu + trước số (+1.75 -> 1.75)
    text = re.sub(r':\s*\+(\d+(?:\.\d+)?)', r': \1', text)
    
    # 4. Thử tìm JSON object hợp lệ
    m = re.search(r'\{.*\}', text, re.DOTALL)
    if m:
        candidate = m.group(0)
        try:
            return json.loads(candidate)
        except Exception:
            pass
        
        # Thử cắt đến dấu đóng ngoặc hợp lệ gần nhất
        for i in range(len(candidate), 2, -1):
            sub = candidate[:i]
            if sub.endswith('}'):
                try:
                    open_b = sub.count('{')
                    close_b = sub.count('}')
                    if open_b > close_b:
                        sub += '}' * (open_b - close_b)
                    return json.loads(sub)
                except Exception:
                    pass

    # 5. Fallback Regex extraction
    sph_m = re.findall(r'[\"\']?sph[\"\']?\s*:\s*([+\-]?\d+(?:\.\d+)?)', text, re.IGNORECASE)
    cyl_m = re.findall(r'[\"\']?cyl[\"\']?\s*:\s*([+\-]?\d+(?:\.\d+)?)', text, re.IGNORECASE)
    pd_m = re.search(r'[\"\']?pd[\"\']?\s*:\s*([567]\d(?:\.\d+)?)', text, re.IGNORECASE)
    hosp_m = re.search(r'[\"\']?hospital_name[\"\']?\s*:\s*[\"\']([^\"\']+)[\"\']', text, re.IGNORECASE)
    
    if sph_m or cyl_m or pd_m:
        data = {}
        r_eye = {}
        l_eye = {}
        if sph_m:
            r_eye['sph'] = float(sph_m[0])
            if len(sph_m) > 1:
                l_eye['sph'] = float(sph_m[1])
        if cyl_m:
            r_eye['cyl'] = float(cyl_m[0])
            if len(cyl_m) > 1:
                l_eye['cyl'] = float(cyl_m[1])
        
        data['right_eye'] = r_eye
        data['left_eye'] = l_eye
        if pd_m:
            data['pd'] = float(pd_m.group(1))
        
        result = {"document_type": "EYE_PRESCRIPTION", "data": data}
        if hosp_m:
            result['hospital_name'] = hosp_m.group(1)
        return result

    return None


class DonutPrescriptionService:
    """
    Dịch vụ trích xuất đơn kính bằng mô hình Transformer Document Understanding (Donut + LoRA).
    Chuyển đổi trực tiếp từ Ảnh -> Cấu trúc JSON quang học không cần bước OCR cắt dòng.
    """
    _instance = None
    _model = None
    _processor = None
    _is_ready = False

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self):
        self._load_model()

    def _load_model(self):
        if os.path.exists(os.path.join(MODEL_DIR, "model_info.json")) or os.path.exists(os.path.join(MODEL_DIR, "config.json")):
            try:
                import torch
                from transformers import VisionEncoderDecoderModel, AutoProcessor

                self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
                print(f"🤖 Đang nạp mô hình Donut Optical Prescription từ: {MODEL_DIR} ({self.device})")
                self.processor = AutoProcessor.from_pretrained(MODEL_DIR)
                
                # Ưu tiên 1: Mô hình đã được Merge hoàn chỉnh (Standalone Model)
                if os.path.exists(os.path.join(MODEL_DIR, "config.json")):
                    self.model = VisionEncoderDecoderModel.from_pretrained(MODEL_DIR).to(self.device)
                else:
                    # Ưu tiên 2: Nạp LoRA Adapter trên Decoder
                    adapter_path = os.path.join(MODEL_DIR, "lora_adapter")
                    if os.path.exists(os.path.join(adapter_path, "adapter_config.json")):
                        try:
                            from peft import PeftModel
                            base_model_name = "naver-clova-ix/donut-base"
                            base = VisionEncoderDecoderModel.from_pretrained(base_model_name)
                            base.decoder = PeftModel.from_pretrained(base.decoder, adapter_path)
                            self.model = base.to(self.device)
                            print("✅ Đã nạp thành công mô hình Donut LoRA Adapter.")
                        except Exception as ex_lora:
                            print(f"⚠️ Lỗi nạp LoRA Adapter ({ex_lora}), nạp VisionEncoderDecoderModel chuẩn...")
                            self.model = VisionEncoderDecoderModel.from_pretrained(MODEL_DIR).to(self.device)
                    else:
                        self.model = VisionEncoderDecoderModel.from_pretrained(MODEL_DIR).to(self.device)

                self.model.eval()
                self._is_ready = True
                print("✅ Mô hình Donut Optical Prescription sẵn sàng phục vụ.")
            except Exception as e:
                print(f"⚠️ Chưa thể nạp trọng số Donut ({e}). Sẽ sử dụng Fallback Transformer Engine.")
                self._is_ready = False
        else:
            self._is_ready = False

    def is_available(self) -> bool:
        return self._is_ready

    def extract_from_image(self, image_path: str) -> Optional[Dict[str, Any]]:
        """Dự đoán trực tiếp cấu trúc JSON từ ảnh đơn kính."""
        if not self._is_ready:
            return None

        try:
            import torch
            image = Image.open(image_path).convert("RGB")
            pixel_values = self.processor(image, return_tensors="pt").pixel_values.to(self.device)

            task_prompt = "<s_doc_type>"
            decoder_input_ids = self.processor.tokenizer(
                task_prompt, add_special_tokens=False, return_tensors="pt"
            ).input_ids.to(self.device)

            with torch.no_grad():
                outputs = self.model.generate(
                    pixel_values,
                    decoder_input_ids=decoder_input_ids,
                    max_length=384,
                    pad_token_id=self.processor.tokenizer.pad_token_id,
                    eos_token_id=self.processor.tokenizer.eos_token_id,
                    use_cache=True,
                    num_beams=1
                )

            seq = self.processor.batch_decode(outputs, skip_special_tokens=True)[0]
            return clean_and_parse_donut_json(seq)
        except Exception as e:
            print(f"Lỗi suy luận Donut: {e}")
            return None


def get_donut_extractor() -> DonutPrescriptionService:
    return DonutPrescriptionService.get_instance()
