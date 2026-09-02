import os
import sys
import json
import time
import argparse
import torch
from torch.utils.data import Dataset, DataLoader
from PIL import Image
from torch.optim import AdamW
from transformers import (
    VisionEncoderDecoderModel,
    AutoProcessor,
    AutoTokenizer,
    get_linear_schedule_with_warmup
)

# ----------------- DEFAULT CONFIGURATION -----------------
DEFAULT_BASE_MODEL = "naver-clova-ix/donut-base"
DEFAULT_DATA_DIR = "data/dataset"
DEFAULT_OUTPUT_DIR = "models/optical_prescription_model"
DEFAULT_BATCH_SIZE = 2
DEFAULT_EPOCHS = 3
DEFAULT_LEARNING_RATE = 5e-5
DEFAULT_MAX_LENGTH = 512
DEFAULT_ACCUM_STEPS = 1


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

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        item = self.samples[idx]
        img_path = os.path.join(self.split_dir, item["file_name"])
        image = Image.open(img_path).convert("RGB")

        # Encode Image Pixel Values (Donut Processor tự xử lý resizing & normalization)
        pixel_values = self.processor(image, return_tensors="pt").pixel_values.squeeze(0)

        # Encode Ground Truth JSON text
        gt_dict = json.loads(item["ground_truth"])
        target_seq = json.dumps(gt_dict["gt_parse"], ensure_ascii=False)
        
        # Tokenize label
        labels = self.processor.tokenizer(
            target_seq,
            add_special_tokens=False,
            max_length=self.max_length,
            padding="max_length",
            truncation=True,
            return_tensors="pt"
        ).input_ids.squeeze(0)

        # Ignore padding tokens in loss calculation (-100)
        labels[labels == self.processor.tokenizer.pad_token_id] = -100

        return {
            "pixel_values": pixel_values,
            "labels": labels
        }


def parse_args():
    parser = argparse.ArgumentParser(description="🚀 Huấn luyện mô hình Optical Prescription Donut (GPU & CPU)")
    parser.add_argument("--base_model", type=str, default=DEFAULT_BASE_MODEL, help="Tên model base từ HuggingFace")
    parser.add_argument("--data_dir", type=str, default=DEFAULT_DATA_DIR, help="Thư mục chứa dataset (train & val)")
    parser.add_argument("--output_dir", type=str, default=DEFAULT_OUTPUT_DIR, help="Thư mục lưu weights sau khi train")
    parser.add_argument("--batch_size", type=int, default=DEFAULT_BATCH_SIZE, help="Kích thước batch (Mặc định: 2)")
    parser.add_argument("--epochs", type=int, default=DEFAULT_EPOCHS, help="Số lượng Epochs (Mặc định: 3)")
    parser.add_argument("--lr", type=float, default=DEFAULT_LEARNING_RATE, help="Learning rate (Mặc định: 5e-5)")
    parser.add_argument("--accum_steps", type=int, default=DEFAULT_ACCUM_STEPS, help="Gradient accumulation steps")
    parser.add_argument("--device", type=str, default="auto", help="Thiết bị tính toán: auto, cuda, cuda:0, cpu")
    parser.add_argument("--fp16", action="store_true", default=True, help="Bật Mixed Precision (FP16) khi chạy GPU")
    parser.add_argument("--no_fp16", action="store_false", dest="fp16", help="Tắt FP16")
    return parser.parse_args()


def train():
    args = parse_args()

    # 1. Thiết lập phần cứng (GPU / CPU)
    if args.device == "auto":
        device_str = "cuda" if torch.cuda.is_available() else "cpu"
    else:
        device_str = args.device

    device = torch.device(device_str)
    is_cuda = device.type == "cuda" and torch.cuda.is_available()
    use_fp16 = is_cuda and args.fp16

    print("=" * 75)
    print("🚀 HUẤN LUYỆN MÔ HÌNH TRANSFORMER DONUT OPTICAL PRESCRIPTION")
    print("=" * 75)
    print(f"👉 Thiết bị (Device):          {device}")
    if is_cuda:
        gpu_name = torch.cuda.get_device_name(device)
        total_vram = torch.cuda.get_device_properties(device).total_memory / (1024 ** 3)
        cuda_ver = torch.version.cuda
        print(f"🎮 GPU Tên:                    {gpu_name}")
        print(f"💾 Dung lượng VRAM:            {total_vram:.2f} GB")
        print(f"⚡ Phiên bản CUDA PyTorch:     {cuda_ver}")
        print(f"🔥 Mixed Precision (FP16):     {'BẬT (Tối ưu tốc độ & VRAM)' if use_fp16 else 'TẮT'}")
    else:
        print("💻 Chế độ:                     CPU Mode (Không phát hiện CUDA Driver trong môi trường hiện tại)")
        print("💡 Gợi ý: Chạy trên Terminal máy host ngoài sandbox để nhận diện GPU NVIDIA đầy đủ.")

    print(f"📁 Thư mục dữ liệu:            {args.data_dir}")
    print(f"💾 Thư mục lưu Model:          {args.output_dir}")
    print(f"⚙️ Tham số:                    Epochs={args.epochs} | Batch={args.batch_size} | LR={args.lr} | Accum={args.accum_steps}")
    print("=" * 75)

    os.makedirs(args.output_dir, exist_ok=True)

    # 2. Khởi tạo Processor & Model
    print("\n📥 Đang nạp Processor và Kiến trúc Donut VisionEncoderDecoder...")
    try:
        processor = AutoProcessor.from_pretrained(args.base_model)
        model = VisionEncoderDecoderModel.from_pretrained(args.base_model)
        print("✅ Đã nạp thành công mô hình Base từ HuggingFace Hub.")
    except Exception as e:
        print(f"⚠️ Không thể nạp online ({e}), đang khởi tạo kiến trúc Donut cục bộ...")
        from transformers import VisionEncoderDecoderConfig, DonutSwinConfig, MBartConfig
        config = VisionEncoderDecoderConfig.from_encoder_decoder_configs(
            DonutSwinConfig(image_size=[960, 720]),
            MBartConfig(vocab_size=processor.tokenizer.vocab_size if 'processor' in locals() else 50000)
        )
        model = VisionEncoderDecoderModel(config=config)

    model.to(device)

    # 3. Khởi tạo Datasets & DataLoaders
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

    print(f"📊 Số lượng mẫu Train: {len(train_dataset)} | Số lượng mẫu Validation: {len(val_dataset)}")
    if len(train_dataset) == 0:
        print("❌ Lỗi: Tập train trống. Vui lòng kiểm tra lại thư mục dataset.")
        return

    # 4. Optimizer, Scheduler & GradScaler
    optimizer = AdamW(model.parameters(), lr=args.lr, weight_decay=0.01)
    total_steps = (len(train_loader) // args.accum_steps) * args.epochs
    scheduler = get_linear_schedule_with_warmup(
        optimizer,
        num_warmup_steps=max(1, int(total_steps * 0.1)),
        num_training_steps=max(1, total_steps)
    )
    scaler = torch.amp.GradScaler('cuda', enabled=use_fp16)

    # 5. Vòng lặp Huấn luyện (Training Loop)
    best_val_loss = float("inf")
    start_time = time.time()

    for epoch in range(args.epochs):
        model.train()
        train_loss = 0.0
        epoch_start = time.time()

        print(f"\n🔄 Epoch [{epoch + 1}/{args.epochs}] Bắt đầu:")
        optimizer.zero_grad()

        for step, batch in enumerate(train_loader):
            pixel_values = batch["pixel_values"].to(device, non_blocking=is_cuda)
            labels = batch["labels"].to(device, non_blocking=is_cuda)

            # Mixed Precision Forward
            with torch.amp.autocast('cuda', enabled=use_fp16):
                outputs = model(pixel_values=pixel_values, labels=labels)
                loss = outputs.loss / args.accum_steps

            # Backward pass với GradScaler
            scaler.scale(loss).backward()

            train_loss += loss.item() * args.accum_steps

            if (step + 1) % args.accum_steps == 0 or (step + 1) == len(train_loader):
                scaler.unscale_(optimizer)
                torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
                scaler.step(optimizer)
                scaler.update()
                optimizer.zero_grad()
                scheduler.step()

            # In tiến trình
            if (step + 1) % 10 == 0 or (step + 1) == len(train_loader):
                gpu_mem_str = ""
                if is_cuda:
                    mem_mb = torch.cuda.memory_allocated(device) / (1024 ** 2)
                    gpu_mem_str = f" | VRAM: {mem_mb:.1f}MB"
                print(f"   Step [{step + 1:02d}/{len(train_loader):02d}] - Loss: {loss.item() * args.accum_steps:.4f}{gpu_mem_str}")

        avg_train_loss = train_loss / max(1, len(train_loader))
        epoch_elapsed = time.time() - epoch_start

        # 6. Đánh giá trên tập Validation
        model.eval()
        val_loss = 0.0
        with torch.no_grad():
            for val_batch in val_loader:
                pixel_values = val_batch["pixel_values"].to(device, non_blocking=is_cuda)
                labels = val_batch["labels"].to(device, non_blocking=is_cuda)

                with torch.amp.autocast('cuda', enabled=use_fp16):
                    outputs = model(pixel_values=pixel_values, labels=labels)
                    val_loss += outputs.loss.item()

        avg_val_loss = val_loss / max(1, len(val_loader))
        print(f"✅ Epoch {epoch + 1} hoàn thành ({epoch_elapsed:.1f}s) - Train Loss: {avg_train_loss:.4f} | Val Loss: {avg_val_loss:.4f}")

        # Lưu Checkpoint tốt nhất
        if avg_val_loss < best_val_loss:
            best_val_loss = avg_val_loss
            best_dir = os.path.join(args.output_dir, "best_checkpoint")
            os.makedirs(best_dir, exist_ok=True)
            model.save_pretrained(best_dir)
            processor.save_pretrained(best_dir)

    total_elapsed = time.time() - start_time
    print(f"\n⏱️ Tổng thời gian huấn luyện: {total_elapsed:.1f}s (Trung bình: {total_elapsed/args.epochs:.1f}s/epoch)")

    # 7. Lưu Trọng số Model và Processor cuối cùng
    print(f"💾 Đang lưu mô hình vào: {args.output_dir}")
    model.save_pretrained(args.output_dir)
    processor.save_pretrained(args.output_dir)

    # Lưu Metadata Model Card
    model_card = {
        "model_type": "Donut Optical Prescription Parser",
        "base_model": args.base_model,
        "device_used": str(device),
        "gpu_name": torch.cuda.get_device_name(device) if is_cuda else "N/A (CPU)",
        "dataset_size": {
            "train": len(train_dataset),
            "val": len(val_dataset)
        },
        "epochs": args.epochs,
        "batch_size": args.batch_size,
        "learning_rate": args.lr,
        "best_val_loss": round(best_val_loss, 4),
        "target_fields": ["hospital_name", "patient_name", "date", "right_eye", "left_eye", "pd"],
        "status": "Trained & Ready for Production Inference"
    }

    info_path = os.path.join(args.output_dir, "model_info.json")
    with open(info_path, "w", encoding="utf-8") as f:
        json.dump(model_card, f, ensure_ascii=False, indent=2)

    print("🎉 Huấn luyện thành công! Metadata đã được ghi vào model_info.json.")
    print(f"👉 Sẵn sàng phục vụ suy luận qua DonutPrescriptionService (app/donut_service.py)")


if __name__ == "__main__":
    train()
