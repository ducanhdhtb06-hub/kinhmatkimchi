from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Boolean, Text, ForeignKey, DateTime
from sqlalchemy.orm import relationship

try:
    from app.database import Base
except (ImportError, ModuleNotFoundError):
    from .database import Base

class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True)
    slug = Column(String(100), nullable=False, unique=True, index=True)
    description = Column(Text, nullable=True)
    icon = Column(String(50), default="fa-glasses")

    frames = relationship("FrameProduct", back_populates="category")


class FrameProduct(Base):
    __tablename__ = "frames"

    id = Column(Integer, primary_key=True, index=True)
    category_id = Column(Integer, ForeignKey("categories.id", ondelete="SET NULL"), nullable=True)
    name = Column(String(150), nullable=False, index=True)
    brand = Column(String(100), default="Kim Chi Eyewear")
    sku = Column(String(50), unique=True, index=True)
    price = Column(Float, nullable=False)
    original_price = Column(Float, nullable=True)
    
    # Kỹ thuật & Vật liệu
    material = Column(String(50), default="Acetate") # Titanium, Acetate, Kim loại, Nhựa TR90
    shape = Column(String(50), default="Vuông") # Tròn, Vuông, Chữ nhật, Aviator, Mắt mèo, Browline
    gender = Column(String(20), default="Unisex") # Nam, Nữ, Unisex
    suitable_face_shapes = Column(String(200), default="Tròn,Trái xoan,Vuông,Dài") # Phân cách bằng dấu phẩy
    
    # Kích thước chuẩn quang học (Frame Dimensions in mm)
    eye_size = Column(Integer, default=52)     # Độ rộng tròng kính (mm)
    bridge_size = Column(Integer, default=18)  # Cầu mũi (mm)
    temple_size = Column(Integer, default=140) # Chiều dài càng kính (mm)
    frame_width = Column(Integer, default=136) # Tổng chiều rộng bề ngang gọng (mm)
    
    # Media & AR Try-On Assets
    image_url = Column(String(300), nullable=False)
    tryon_overlay_url = Column(String(300), nullable=True) # Ảnh PNG trong suốt không nền dùng cho AR Try-On
    
    description = Column(Text, nullable=True)
    stock = Column(Integer, default=20)
    is_featured = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    category = relationship("Category", back_populates="frames")
    order_items = relationship("OrderItem", back_populates="frame")

    @property
    def discount_percent(self) -> int:
        if self.original_price and self.original_price > self.price:
            return int(round((1 - self.price / self.original_price) * 100))
        return 0


class LensProduct(Base):
    __tablename__ = "lenses"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(150), nullable=False)
    brand = Column(String(100), default="Essilor / Chemi")
    lens_type = Column(String(50), default="Kính Cận / Viễn / Loạn") # 0 độ, Cận viễn loạn, Đổi màu, Siêu mỏng
    index_refraction = Column(Float, default=1.56) # 1.56, 1.60, 1.67, 1.74
    
    # Tính năng tròng kính
    is_blue_cut = Column(Boolean, default=True)      # Chống ánh sáng xanh
    is_photochromic = Column(Boolean, default=False) # Đổi màu khi ra nắng
    is_anti_scratch = Column(Boolean, default=True)  # Chống trầy & chống bám nước
    
    price = Column(Float, nullable=False, default=350000)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)

    order_items = relationship("OrderItem", back_populates="lens")


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    order_code = Column(String(50), unique=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    customer_name = Column(String(100), nullable=False)
    phone = Column(String(20), nullable=False)
    email = Column(String(100), nullable=True)
    shipping_address = Column(String(255), nullable=False)
    
    payment_method = Column(String(50), default="COD") # COD, Chuyển khoản QR, VNPay
    payment_status = Column(String(50), default="Chờ thanh toán") # Chờ thanh toán, Đã thanh toán
    order_status = Column(String(50), default="Đang xử lý") # Đang xử lý, Đang mài tròng, Đang giao, Hoàn tất, Đã hủy
    
    original_amount = Column(Float, default=0.0)
    discount_amount = Column(Float, default=0.0)
    voucher_code = Column(String(50), nullable=True)
    total_amount = Column(Float, default=0.0)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")


class OrderItem(Base):
    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id", ondelete="CASCADE"), nullable=False)
    frame_id = Column(Integer, ForeignKey("frames.id", ondelete="SET NULL"), nullable=True)
    lens_id = Column(Integer, ForeignKey("lenses.id", ondelete="SET NULL"), nullable=True)
    
    frame_price = Column(Float, default=0.0)
    lens_price = Column(Float, default=0.0)
    quantity = Column(Integer, default=1)
    
    # Thông số thị lực cá nhân (Prescription details)
    # Mắt phải (OD)
    right_sph = Column(Float, default=0.0)  # Độ cầu (- cận, + viễn)
    right_cyl = Column(Float, default=0.0)  # Độ loạn
    right_axis = Column(Integer, default=0) # Trục loạn (0 - 180)
    
    # Mắt trái (OS)
    left_sph = Column(Float, default=0.0)
    left_cyl = Column(Float, default=0.0)
    left_axis = Column(Integer, default=0)
    
    pd = Column(Float, default=62.0) # Khoảng cách đồng tử (mm)
    prescription_image_url = Column(String(300), nullable=True) # Ảnh chụp phiếu khám mắt tải lên
    notes = Column(String(255), nullable=True)

    # Relationships
    order = relationship("Order", back_populates="items")
    frame = relationship("FrameProduct", back_populates="order_items")
    lens = relationship("LensProduct", back_populates="order_items")


class BankConfig(Base):
    __tablename__ = "bank_config"

    id = Column(Integer, primary_key=True, index=True)
    bank_id = Column(String(20), default="MB") # MB, VCB, TCB, ACB, VPB, ICB, TPB, STB
    bank_name = Column(String(100), default="MBBank (Ngân Hàng Quân Đội)")
    account_number = Column(String(50), default="0988888888")
    account_name = Column(String(100), default="KINH MAT KIM CHI")
    is_auto_active = Column(Boolean, default=True)
    webhook_secret = Column(String(100), default="kimchi_secret_key_2026")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class AdminUser(Base):
    __tablename__ = "admin_users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(100), default="Quản Trị Viên Kim Chi")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(100), unique=True, index=True, nullable=False)
    phone = Column(String(20), unique=True, index=True, nullable=True)
    full_name = Column(String(100), nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(20), default="customer") # "customer" or "admin"
    is_active = Column(Boolean, default=True)
    
    # Hồ sơ thị lực lưu sẵn
    saved_right_sph = Column(Float, default=0.0)
    saved_right_cyl = Column(Float, default=0.0)
    saved_right_axis = Column(Integer, default=0)
    saved_left_sph = Column(Float, default=0.0)
    saved_left_cyl = Column(Float, default=0.0)
    saved_left_axis = Column(Integer, default=0)
    saved_pd = Column(Float, default=62.5)

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    orders = relationship("Order", backref="user")


class Voucher(Base):
    __tablename__ = "vouchers"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(50), unique=True, index=True, nullable=False)
    name = Column(String(150), nullable=False)
    discount_type = Column(String(20), default="percent") # "percent" or "fixed"
    discount_value = Column(Float, default=10.0) # 10% or 50,000 VND
    min_order_amount = Column(Float, default=0.0) # Minimum cart value
    max_discount = Column(Float, default=500000.0) # Cap for percent discounts
    usage_limit = Column(Integer, default=100)
    used_count = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class TelegramConfig(Base):
    __tablename__ = "telegram_config"

    id = Column(Integer, primary_key=True, index=True)
    bot_token = Column(String(150), nullable=True) # e.g. 123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11
    chat_id = Column(String(100), nullable=True)   # e.g. -100123456789 or 987654321
    is_active = Column(Boolean, default=False)
    notify_on_order = Column(Boolean, default=True)
    notify_on_payment = Column(Boolean, default=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)




