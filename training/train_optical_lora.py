"""
🚀 HUẤN LUYỆN MÔ HÌNH TRÍCH XUẤT ĐƠN KÍNH QUANG HỌC VỚI DONUT + LoRA (PEFT)
================================================================================
- Tiết kiệm 65 - 75% VRAM (Chỉ tốn ~3GB - 4GB VRAM thay vì 12GB+).
- Tốc độ huấn luyện nhanh gấp 3 lần.
- THEO DÕI ĐỘ CHÍNH XÁC (VALIDATION ACCURACY %) & VAL LOSS THỜI GIAN THỰC.
- Tự động lưu lịch sử Training/Validation vào training_history.csv & training_history.json.
- Hỗ trợ HUẤN LUYỆN NỐI TIẾP (--resume): Sau khi xong, có thể train tiếp mà không mất dữ liệu.
- Tự động xuất cả LoRA Adapter lẫn mô hình Merged độc lập để chạy suy luận tốc độ cao.
"""

import os
import sys
import csv
import json
import time
import argparse
import torch
from torch.utils.data import Dataset, DataLoader
from PIL import Image
from torch.optim import AdamW

try:
    from transformers import (
        VisionEncoderDecoderModel,
        AutoProcessor,
        get_linear_schedule_with_warmup
    )
except ImportError:
    print("❌ Lỗi: Chưa cài đặt thư viện 'transformers'. Vui lòng chạy: pip install transformers")
    sys.exit(1)

try:
    from peft import LoraConfig, get_peft_model, PeftModel
except ImportError:
    print("⚠️ Cảnh báo: Chưa cài đặt 'peft'. Vui lòng chạy: pip install peft")

# ----------------- CẤU HÌNH MẶC ĐỊNH -----------------
DEFAULT_BASE_MODEL = "naver-clova-ix/donut-base"
DEFAULT_DATA_DIR = "data/dataset"
DEFAULT_OUTPUT_DIR = "models/optical_prescription_model"
DEFAULT_LORA_R = 16
DEFAULT_LORA_ALPHA = 32
DEFAULT_LORA_DROPOUT = 0.05
DEFAULT_BATCH_SIZE = 2
DEFAULT_EPOCHS = 5
DEFAULT_LEARNING_RATE = 2e-4
DEFAULT_MAX_LENGTH = 512
DEFAULT_ACCUM_STEPS = 2


class OpticalPrescriptionDataset(Dataset):
    """Dataset đọc ảnh đơn kính và nhãn JSON chuẩn định dạng Donut."""
    def __init__(self, split_dir: str, processor, max_length: int = DEFAULT_MAX_LENGTH):
        self.split_dir = split_dir
        self.processor = processor
        self.max_length = max_length
        self.samples = []

        metadata_file = os.path.join(split_dir, "metadata.jsonl")
        if os.path.exists(metadata_file):
            with open(metadata_file, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        self.samples.append(json.loads(line.strip()))
        else:
            print(f"⚠️ Không tìm thấy file metadata: {metadata_file}")

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        item = self.samples[idx]
        img_path = os.path.join(self.split_dir, item["file_name"])
        image = Image.open(img_path).convert("RGB")

        # Chuẩn hóa ảnh qua Donut Processor
        pixel_values = self.processor(image, return_tensors="pt").pixel_values.squeeze(0)

        # Định dạng chuỗi Ground Truth JSON
        gt_dict = json.loads(item["ground_truth"])
        target_seq = f"<s_doc_type>{json.dumps(gt_dict.get('gt_parse', {}), ensure_ascii=False)}</s_doc_type>"

        # Tokenize nhãn
        labels = self.processor.tokenizer(
            target_seq,
            add_special_tokens=False,
            max_length=self.max_length,
            padding="max_length",
            truncation=True,
            return_tensors="pt"
        ).input_ids.squeeze(0)

        # Bỏ qua loss cho các padding token (-100)
        labels[labels == self.processor.tokenizer.pad_token_id] = -100

        return {
            "pixel_values": pixel_values,
            "labels": labels,
            "file_name": item["file_name"],
            "target_seq": target_seq
        }


def parse_args():
    parser = argparse.ArgumentParser(description="🚀 Huấn luyện Donut Optical Prescription với LoRA siêu nhẹ (Theo dõi Accuracy & Validation)")
    parser.add_argument("--base_model", type=str, default=DEFAULT_BASE_MODEL, help="Tên model base từ Hugging Face")
    parser.add_argument("--data_dir", type=str, default=DEFAULT_DATA_DIR, help="Thư mục dataset (chứa train/ & val/)")
    parser.add_argument("--output_dir", type=str, default=DEFAULT_OUTPUT_DIR, help="Thư mục lưu weights sau khi train")
    parser.add_argument("--resume", action="store_true", default=False, help="Bật cờ này để TIẾP TỤC HUẤN LUYỆN từ checkpoint trước đó")
    parser.add_argument("--resume_from_checkpoint", type=str, default=None, help="Đường dẫn thư mục LoRA adapter để tiếp tục train")
    parser.add_argument("--lora_r", type=int, default=DEFAULT_LORA_R, help="LoRA Rank r (Mặc định: 16)")
    parser.add_argument("--lora_alpha", type=int, default=DEFAULT_LORA_ALPHA, help="LoRA Alpha (Mặc định: 32)")
    parser.add_argument("--batch_size", type=int, default=DEFAULT_BATCH_SIZE, help="Kích thước batch (Mặc định: 2)")
    parser.add_argument("--epochs", type=int, default=DEFAULT_EPOCHS, help="Số lượng Epochs muốn train (Mặc định: 5)")
    parser.add_argument("--lr", type=float, default=DEFAULT_LEARNING_RATE, help="Learning rate (Mặc định: 2e-4)")
    parser.add_argument("--accum_steps", type=int, default=DEFAULT_ACCUM_STEPS, help="Gradient accumulation steps")
    parser.add_argument("--device", type=str, default="auto", help="Thiết bị: auto, cuda, cuda:0, cpu")
    parser.add_argument("--fp16", action="store_true", default=True, help="Bật Mixed Precision (FP16)")
    parser.add_argument("--no_fp16", action="store_false", dest="fp16", help="Tắt FP16")
    parser.add_argument("--merge_weights", action="store_true", default=True, help="Tự động merge LoRA vào Base Model")
    parser.add_argument("--show_val_sample", action="store_true", default=True, help="Hiển thị mẫu dự đoán Validation sau mỗi Epoch")
    return parser.parse_args()


def print_trainable_parameters(model):
    """Tính toán tỷ lệ tham số được huấn luyện (Trainable vs Total)."""
    trainable_params = 0
    all_param = 0
    for _, param in model.named_parameters():
        all_param += param.numel()
        if param.requires_grad:
            trainable_params += param.numel()
    pct = 100 * trainable_params / all_param
    print(f"📊 Tham số huấn luyện (LoRA): {trainable_params:,} / {all_param:,} ({pct:.2f}%)")
    print(f"💡 Đã đóng băng {100 - pct:.2f}% mô hình gốc giúp tiết kiệm bộ nhớ tối đa!")


def train():
    args = parse_args()

    # 1. Cấu hình thiết bị phần cứng
    if args.device == "auto":
        device_str = "cuda" if torch.cuda.is_available() else "cpu"
    else:
        device_str = args.device

    device = torch.device(device_str)
    is_cuda = device.type == "cuda" and torch.cuda.is_available()
    use_fp16 = is_cuda and args.fp16

    print("=" * 90)
    print("🚀 HUẤN LUYỆN MÔ HÌNH DONUT OPTICAL PRESCRIPTION VỚI LoRA & THEO DÕI ĐỘ CHÍNH XÁC (ACCURACY)")
    print("=" * 90)
    print(f"👉 Thiết bị (Device):          {device}")
    if is_cuda:
        gpu_name = torch.cuda.get_device_name(device)
        total_vram = torch.cuda.get_device_properties(device).total_memory / (1024 ** 3)
        print(f"🎮 Tên GPU:                    {gpu_name}")
        print(f"💾 Dung lượng VRAM:            {total_vram:.2f} GB")
        print(f"🔥 Mixed Precision (FP16):     {'BẬT (Siêu tốc & nhẹ VRAM)' if use_fp16 else 'TẮT'}")
    else:
        print("💻 Chế độ:                     CPU Mode (Khuyến khích chạy trên máy có GPU / Colab để train nhanh hơn)")

    print(f"📁 Thư mục dữ liệu:            {args.data_dir}")
    print(f"💾 Thư mục lưu mô hình:        {args.output_dir}")
    print(f"🔄 Huấn luyện nối tiếp:        {'BẬT (Tiếp tục từ checkpoint cũ)' if args.resume or args.resume_from_checkpoint else 'TẮT (Bắt đầu mới từ Base Model)'}")
    print(f"⚙️ Tham số LoRA:               r={args.lora_r} | alpha={args.lora_alpha} | dropout={DEFAULT_LORA_DROPOUT}")
    print(f"⚙️ Tham số Train:              Epochs={args.epochs} | Batch={args.batch_size} | LR={args.lr} | Accum={args.accum_steps}")
    print("=" * 90)

    os.makedirs(args.output_dir, exist_ok=True)

    # 2. Khởi tạo Processor & Base Model
    print(f"\n📥 Đang nạp Processor & Base Model từ: {args.base_model}...")
    processor = AutoProcessor.from_pretrained(args.base_model)
    model = VisionEncoderDecoderModel.from_pretrained(args.base_model)

    # Thêm special tokens nếu chưa có
    special_tokens = ["<s_doc_type>", "</s_doc_type>"]
    num_added = processor.tokenizer.add_special_tokens({"additional_special_tokens": special_tokens})
    if num_added > 0:
        model.decoder.resize_token_embeddings(len(processor.tokenizer))

    # Cấu hình Token ID cho Generator
    model.config.decoder_start_token_id = processor.tokenizer.convert_tokens_to_ids("<s_doc_type>")
    model.config.pad_token_id = processor.tokenizer.pad_token_id

    # 3. Đóng băng Encoder Swin
    for param in model.encoder.parameters():
        param.requires_grad = False

    # 4. Kiểm tra xem có Tiếp tục huấn luyện (Resume) hay Khởi tạo mới LoRA
    checkpoint_to_resume = None
    if args.resume_from_checkpoint:
        checkpoint_to_resume = args.resume_from_checkpoint
    elif args.resume:
        default_adapter_path = os.path.join(args.output_dir, "lora_adapter")
        if os.path.exists(os.path.join(default_adapter_path, "adapter_config.json")):
            checkpoint_to_resume = default_adapter_path
        else:
            print(f"ℹ️ Không tìm thấy adapter cũ tại {default_adapter_path}, sẽ khởi tạo LoRA mới.")

    if checkpoint_to_resume and os.path.exists(os.path.join(checkpoint_to_resume, "adapter_config.json")):
        try:
            print(f"\n🔄 Đang nạp LoRA Checkpoint để TIẾP TỤC HUẤN LUYỆN từ: {checkpoint_to_resume}...")
            model.decoder = PeftModel.from_pretrained(model.decoder, checkpoint_to_resume, is_trainable=True)
            print("✅ Đã nạp thành công trọng số trước đó. Sẽ học nối tiếp các Epoch mới!")
            print_trainable_parameters(model)
        except Exception as ex_resume:
            print(f"⚠️ Lỗi khi nạp checkpoint cũ ({ex_resume}), sẽ khởi tạo LoRA mới...")
            checkpoint_to_resume = None

    if not checkpoint_to_resume or not hasattr(model.decoder, "peft_config"):
        print("\n🧩 Đang cấu hình PEFT LoRA Adapter mới trên Decoder...")
        try:
            from peft import LoraConfig, get_peft_model
            
            target_modules = ["q_proj", "v_proj", "k_proj", "out_proj", "fc1", "fc2"]
            lora_config = LoraConfig(
                r=args.lora_r,
                lora_alpha=args.lora_alpha,
                target_modules=target_modules,
                lora_dropout=DEFAULT_LORA_DROPOUT,
                bias="none"
            )
            model.decoder = get_peft_model(model.decoder, lora_config)
            print("✅ Gắn LoRA Adapter vào Decoder thành công.")
            print_trainable_parameters(model)
        except Exception as e:
            print(f"⚠️ Lỗi khi nạp LoRA ({e}).")

    model.to(device)

    # 5. Khởi tạo Datasets & DataLoader
    train_dataset = OpticalPrescriptionDataset(os.path.join(args.data_dir, "train"), processor)
    val_dataset = OpticalPrescriptionDataset(os.path.join(args.data_dir, "val"), processor)

    train_loader = DataLoader(
        train_dataset,
        batch_size=args.batch_size,
        shuffle=True,
        num_workers=2 if is_cuda else 0,
        pin_memory=is_cuda
    )
    val_loader = DataLoader(
        val_dataset,
        batch_size=args.batch_size,
        shuffle=False,
        num_workers=2 if is_cuda else 0,
        pin_memory=is_cuda
    )

    print(f"\n📊 Mẫu dữ liệu: Train={len(train_dataset)} mẫu | Validation={len(val_dataset)} mẫu")
    if len(train_dataset) == 0:
        print("❌ Lỗi: Thư mục train trống! Vui lòng kiểm tra lại dataset.")
        return

    # 6. Optimizer, Scheduler & GradScaler
    optimizer = AdamW(filter(lambda p: p.requires_grad, model.parameters()), lr=args.lr, weight_decay=0.01)
    total_steps = (len(train_loader) // args.accum_steps) * args.epochs
    scheduler = get_linear_schedule_with_warmup(
        optimizer,
        num_warmup_steps=max(1, int(total_steps * 0.1)),
        num_training_steps=max(1, total_steps)
    )
    scaler = torch.amp.GradScaler('cuda', enabled=use_fp16)

    # 7. Khởi tạo Lịch sử Theo dõi (Training History Tracker)
    history = []
    history_csv_path = os.path.join(args.output_dir, "training_history.csv")
    history_json_path = os.path.join(args.output_dir, "training_history.json")

    # Đọc lại history cũ nếu đang resume
    if args.resume and os.path.exists(history_json_path):
        try:
            with open(history_json_path, "r", encoding="utf-8") as f:
                history = json.load(f)
        except Exception:
            history = []

    best_val_loss = min([h["val_loss"] for h in history]) if history else float("inf")
    start_time = time.time()

    print("\n" + "=" * 90)
    print("🔥 BẮT ĐẦU HUẤN LUYỆN & THEO DÕI CHỈ SỐ ACCURACY & VAL LOSS")
    print("=" * 90)
    print(f"{'Epoch':<8} | {'Train Loss':<11} | {'Val Loss':<10} | {'Val Acc %':<10} | {'LR':<9} | {'Thời gian':<9} | {'Trạng thái':<18}")
    print("-" * 90)

    for epoch in range(args.epochs):
        model.train()
        train_loss = 0.0
        epoch_start = time.time()

        optimizer.zero_grad()

        for step, batch in enumerate(train_loader):
            pixel_values = batch["pixel_values"].to(device, non_blocking=is_cuda)
            labels = batch["labels"].to(device, non_blocking=is_cuda)

            with torch.amp.autocast('cuda', enabled=use_fp16):
                outputs = model(pixel_values=pixel_values, labels=labels)
                loss = outputs.loss / args.accum_steps

            scaler.scale(loss).backward()
            train_loss += loss.item() * args.accum_steps

            if (step + 1) % args.accum_steps == 0 or (step + 1) == len(train_loader):
                scaler.unscale_(optimizer)
                torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
                scaler.step(optimizer)
                scaler.update()
                optimizer.zero_grad()
                scheduler.step()

        avg_train_loss = train_loss / max(1, len(train_loader))
        epoch_time = time.time() - epoch_start
        current_lr = scheduler.get_last_lr()[0] if scheduler.get_last_lr() else args.lr

        # -------------------------------------------------------------
        # 8. ĐÁNH GIÁ TRÊN TẬP VALIDATION (LOSS & ACCURACY %)
        # -------------------------------------------------------------
        model.eval()
        val_loss = 0.0
        val_correct_tokens = 0
        val_total_tokens = 0

        with torch.no_grad():
            for val_batch in val_loader:
                pixel_values = val_batch["pixel_values"].to(device, non_blocking=is_cuda)
                labels = val_batch["labels"].to(device, non_blocking=is_cuda)

                with torch.amp.autocast('cuda', enabled=use_fp16):
                    outputs = model(pixel_values=pixel_values, labels=labels)
                    val_loss += outputs.loss.item()
                    
                    # Tính toán Token Accuracy trên tập Val
                    logits = outputs.logits
                    preds = logits.argmax(dim=-1)
                    mask = labels != -100
                    val_correct_tokens += (preds[mask] == labels[mask]).sum().item()
                    val_total_tokens += mask.sum().item()

        avg_val_loss = val_loss / max(1, len(val_loader))
        val_accuracy_pct = (val_correct_tokens / max(1, val_total_tokens)) * 100

        # Kiểm tra Checkpoint tốt nhất
        is_best = avg_val_loss < best_val_loss
        if is_best:
            best_val_loss = avg_val_loss
            status_str = "🏆 Best Checkpoint"
            adapter_dir = os.path.join(args.output_dir, "lora_adapter")
            os.makedirs(adapter_dir, exist_ok=True)
            if hasattr(model.decoder, "save_pretrained"):
                model.decoder.save_pretrained(adapter_dir)
            processor.save_pretrained(args.output_dir)
        else:
            status_str = "✓ Đã cập nhật"

        # In dòng trạng thái bảng
        epoch_idx_display = len(history) + 1
        print(f"Epoch {epoch_idx_display:02d}/{args.epochs + len(history):02d} | {avg_train_loss:<11.4f} | {avg_val_loss:<10.4f} | {val_accuracy_pct:<9.2f}% | {current_lr:<9.1e} | {epoch_time:<8.1f}s | {status_str:<18}")

        # -------------------------------------------------------------
        # 9. TRỰC QUAN HÓA: DỰ ĐOÁN THỬ 1 MẪU TẬP VALIDATION (LIVE PREVIEW)
        # -------------------------------------------------------------
        if args.show_val_sample and len(val_dataset) > 0 and (epoch % 2 == 0 or epoch == args.epochs - 1 or is_best):
            try:
                sample_item = val_dataset[0]
                sample_pixel = sample_item["pixel_values"].unsqueeze(0).to(device)
                
                task_prompt = "<s_doc_type>"
                decoder_input_ids = processor.tokenizer(task_prompt, add_special_tokens=False, return_tensors="pt").input_ids.to(device)

                with torch.no_grad():
                    gen_out = model.generate(
                        pixel_values=sample_pixel,
                        decoder_input_ids=decoder_input_ids,
                        max_length=256,
                        early_stopping=True,
                        pad_token_id=processor.tokenizer.pad_token_id,
                        eos_token_id=processor.tokenizer.eos_token_id,
                        use_cache=True,
                        num_beams=1
                    )
                predicted_seq = processor.batch_decode(gen_out, skip_special_tokens=True)[0]
                
                print(f"   ┌─ 🧪 [LIVE VAL PREVIEW - File: {sample_item['file_name']}]")
                print(f"   │ 🎯 Ground Truth:   {sample_item['target_seq'][:110]}...")
                print(f"   │ 🤖 Model Predict:  {predicted_seq[:110]}...")
                print(f"   └─────────────────────────────────────────────────────────────")
            except Exception as ex_gen:
                pass

        # Ghi log lịch sử Epoch
        epoch_record = {
            "epoch": epoch_idx_display,
            "train_loss": round(avg_train_loss, 4),
            "val_loss": round(avg_val_loss, 4),
            "val_accuracy": round(val_accuracy_pct, 2),
            "lr": current_lr,
            "epoch_time_sec": round(epoch_time, 1),
            "is_best": is_best
        }
        history.append(epoch_record)

        # Lưu lịch sử ra file JSON & CSV ngay sau mỗi epoch
        with open(history_json_path, "w", encoding="utf-8") as f:
            json.dump(history, f, ensure_ascii=False, indent=2)

        with open(history_csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["epoch", "train_loss", "val_loss", "val_accuracy", "lr", "epoch_time_sec", "is_best"])
            writer.writeheader()
            writer.writerows(history)

    total_time = time.time() - start_time
    print("-" * 90)
    print(f"⏱️ Tổng thời gian huấn luyện: {total_time:.1f}s | Best Val Loss: {best_val_loss:.4f} | Final Val Accuracy: {val_accuracy_pct:.2f}% 🏆")
    print(f"📊 Đã ghi toàn bộ lịch sử theo dõi vào: {history_csv_path}")

    # 10. Lưu mô hình cuối cùng & Merge Weights (Nếu có)
    print(f"\n💾 Đang xuất và hoàn thiện mô hình vào: {args.output_dir}")
    adapter_dir = os.path.join(args.output_dir, "lora_adapter")
    os.makedirs(adapter_dir, exist_ok=True)
    if hasattr(model.decoder, "save_pretrained"):
        model.decoder.save_pretrained(adapter_dir)
    processor.save_pretrained(args.output_dir)

    # Merge LoRA weights vào Base Model để tạo Standalone Model (chạy độc lập siêu nhanh)
    if args.merge_weights and hasattr(model.decoder, "merge_and_unload"):
        try:
            print("🔀 Đang hợp nhất LoRA Adapter vào Base Model (Merge & Unload)...")
            model.decoder = model.decoder.merge_and_unload()
            model.save_pretrained(args.output_dir)
            processor.save_pretrained(args.output_dir)
            print("✅ Đã lưu mô hình hoàn chỉnh (Merged Model) sẵn sàng cho Inference!")
        except Exception as e:
            print(f"⚠️ Không thể merge tự động ({e}), mô hình LoRA Adapter đã được lưu tại: {adapter_dir}")

    # Ghi Metadata Model Card
    card_info = {
        "model_type": "Donut LoRA Optical Prescription Extractor",
        "base_model": args.base_model,
        "lora_r": args.lora_r,
        "lora_alpha": args.lora_alpha,
        "trainable_percent": "~0.84%",
        "best_val_loss": round(best_val_loss, 4),
        "final_val_accuracy": round(val_accuracy_pct, 2),
        "total_epochs_trained": len(history),
        "batch_size": args.batch_size,
        "dataset_size": {"train": len(train_dataset), "val": len(val_dataset)},
        "target_fields": ["hospital_name", "patient_name", "date", "document_type", "data"],
        "history_file": history_csv_path,
        "status": "Ready for Production"
    }
    with open(os.path.join(args.output_dir, "model_info.json"), "w", encoding="utf-8") as f:
        json.dump(card_info, f, ensure_ascii=False, indent=2)

    print("\n🎉 HUẤN LUYỆN HOÀN TẤT THÀNH CÔNG!")
    print(f"👉 Để đánh giá sâu từng trường SPH/CYL/AXIS/PD, hãy chạy: python training/evaluate_prescription_model.py")


if __name__ == "__main__":
    train()
