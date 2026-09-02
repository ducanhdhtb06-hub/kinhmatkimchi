import json
import urllib.request
import urllib.parse
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session

try:
    from app import models
except (ImportError, ModuleNotFoundError):
    from . import models

def send_raw_telegram_message(bot_token: str, chat_id: str, text: str) -> Dict[str, Any]:
    if not bot_token or not chat_id:
        return {"success": False, "message": "Chưa cấu hình Telegram Bot Token hoặc Chat ID"}
    
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML"
    }

    try:
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=8) as response:
            res_data = json.loads(response.read().decode("utf-8"))
            if res_data.get("ok"):
                return {"success": True, "message": "Gửi tin nhắn Telegram thành công!"}
            return {"success": False, "message": res_data.get("description", "Lỗi gửi tin")}
    except Exception as e:
        return {"success": False, "message": f"Không thể kết nối tới Telegram API: {str(e)}"}

def get_telegram_config(db: Session) -> Optional[models.TelegramConfig]:
    config = db.query(models.TelegramConfig).first()
    if not config:
        config = models.TelegramConfig(
            bot_token="",
            chat_id="",
            is_active=False,
            notify_on_order=True,
            notify_on_payment=True
        )
        db.add(config)
        db.commit()
        db.refresh(config)
    return config

def notify_telegram_new_order(db: Session, order: models.Order):
    config = get_telegram_config(db)
    if not config or not config.is_active or not config.notify_on_order:
        return
    if not config.bot_token or not config.chat_id:
        return

    items_text = ""
    for idx, item in enumerate(order.items, 1):
        frame_name = item.frame.name if item.frame else "Gọng Kính"
        lens_name = item.lens.name if item.lens else "Không cắt tròng"
        items_text += f"\n  {idx}. <b>{frame_name}</b> (x{item.quantity})\n     Tròng: <i>{lens_name}</i>"
        if item.right_sph or item.left_sph:
            items_text += f"\n     Độ: R(SPH {item.right_sph:+0.2f}, CYL {item.right_cyl:+0.2f}) | L(SPH {item.left_sph:+0.2f}, CYL {item.left_cyl:+0.2f}) | PD: {item.pd}mm"

    msg = (
        f"🔔 <b>CÓ ĐƠN HÀNG MỚI TẠI KÍNH MẮT KIM CHI!</b>\n"
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"📋 <b>Mã đơn:</b> <code>#{order.order_code}</code>\n"
        f"👤 <b>Khách hàng:</b> {order.customer_name}\n"
        f"📞 <b>SĐT:</b> <code>{order.phone}</code>\n"
        f"📍 <b>Địa chỉ:</b> {order.shipping_address}\n"
        f"💳 <b>Phương thức:</b> {order.payment_method}\n"
        f"💰 <b>Tổng tiền:</b> <b>{int(order.total_amount):,} VNĐ</b>\n"
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"👓 <b>Chi tiết kính đặt:</b>{items_text}\n"
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"⚡ <i>Vui lòng vào trang quản trị để xử lý mài tròng và đóng gói giao hàng.</i>"
    )

    send_raw_telegram_message(config.bot_token, config.chat_id, msg)

def notify_telegram_payment_success(db: Session, order: models.Order, amount: float, gateway: str):
    config = get_telegram_config(db)
    if not config or not config.is_active or not config.notify_on_payment:
        return
    if not config.bot_token or not config.chat_id:
        return

    msg = (
        f"💸 <b>TIỀN VỀ TÀI KHOẢN - THANH TOÁN VIETQR THÀNH CÔNG!</b>\n"
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"💰 <b>Số tiền nhận:</b> <b>+{int(amount):,} VNĐ</b>\n"
        f"📋 <b>Mã đơn hàng:</b> <code>#{order.order_code}</code>\n"
        f"👤 <b>Người mua:</b> {order.customer_name} ({order.phone})\n"
        f"🏦 <b>Cổng xác nhận:</b> {gateway}\n"
        f"✅ <b>Trạng thái:</b> Đã thanh toán tự động (Đang chuyển sang mài kính)\n"
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"🎉 <i>Chúc mừng Kính Mắt Kim Chi có thêm doanh thu mới!</i>"
    )

    send_raw_telegram_message(config.bot_token, config.chat_id, msg)
