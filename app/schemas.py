from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, EmailStr

# Category Schemas
class CategoryBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    slug: str = Field(..., min_length=2, max_length=100)
    description: Optional[str] = None
    icon: str = "fa-glasses"

class CategoryResponse(CategoryBase):
    id: int

    class Config:
        from_attributes = True


# Frame Product Schemas
class FrameProductBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=150)
    category_id: Optional[int] = None
    brand: str = "OptiStyle Pro"
    sku: str
    price: float = Field(..., ge=0)
    original_price: Optional[float] = None
    material: str = "Acetate"
    shape: str = "Vuông"
    gender: str = "Unisex"
    suitable_face_shapes: str = "Tròn,Trái xoan,Vuông,Dài"
    eye_size: int = 52
    bridge_size: int = 18
    temple_size: int = 140
    frame_width: int = 136
    image_url: str
    tryon_overlay_url: Optional[str] = None
    description: Optional[str] = None
    stock: int = 20
    is_featured: bool = False
    is_active: bool = True

class FrameProductCreate(FrameProductBase):
    pass

class FrameProductUpdate(BaseModel):
    name: Optional[str] = None
    category_id: Optional[int] = None
    brand: Optional[str] = None
    price: Optional[float] = None
    original_price: Optional[float] = None
    material: Optional[str] = None
    shape: Optional[str] = None
    gender: Optional[str] = None
    suitable_face_shapes: Optional[str] = None
    eye_size: Optional[int] = None
    bridge_size: Optional[int] = None
    temple_size: Optional[int] = None
    frame_width: Optional[int] = None
    image_url: Optional[str] = None
    tryon_overlay_url: Optional[str] = None
    description: Optional[str] = None
    stock: Optional[int] = None
    is_featured: Optional[bool] = None
    is_active: Optional[bool] = None

class FrameProductResponse(FrameProductBase):
    id: int
    discount_percent: int
    created_at: datetime

    class Config:
        from_attributes = True


# Lens Product Schemas
class LensProductBase(BaseModel):
    name: str
    brand: str = "Chemi Lens"
    lens_type: str = "Kính Cận / Viễn / Loạn"
    index_refraction: float = 1.56
    is_blue_cut: bool = True
    is_photochromic: bool = False
    is_anti_scratch: bool = True
    price: float = 350000
    description: Optional[str] = None
    is_active: bool = True

class LensProductCreate(LensProductBase):
    pass

class LensProductResponse(LensProductBase):
    id: int

    class Config:
        from_attributes = True


# Prescription & Order Schemas
class OrderItemInput(BaseModel):
    frame_id: int
    lens_id: Optional[int] = None
    quantity: int = Field(1, ge=1)
    
    # Prescription data
    right_sph: float = 0.0
    right_cyl: float = 0.0
    right_axis: int = 0
    left_sph: float = 0.0
    left_cyl: float = 0.0
    left_axis: int = 0
    pd: float = 62.0
    prescription_image_url: Optional[str] = None
    notes: Optional[str] = None

class OrderCreateRequest(BaseModel):
    user_id: Optional[int] = None
    customer_name: str = Field(..., min_length=2)
    phone: str = Field(..., min_length=9)
    email: Optional[str] = None
    shipping_address: str = Field(..., min_length=5)
    payment_method: str = "COD"
    voucher_code: Optional[str] = None
    notes: Optional[str] = None
    items: List[OrderItemInput] = []

class OrderItemResponse(BaseModel):
    id: int
    frame_id: Optional[int]
    frame_name: Optional[str]
    frame_image: Optional[str]
    frame_price: float
    lens_id: Optional[int]
    lens_name: Optional[str]
    lens_price: float
    quantity: int
    right_sph: float
    right_cyl: float
    right_axis: int
    left_sph: float
    left_cyl: float
    left_axis: int
    pd: float
    prescription_image_url: Optional[str]

    class Config:
        from_attributes = True

class OrderResponse(BaseModel):
    id: int
    order_code: str
    user_id: Optional[int] = None
    customer_name: str
    phone: str
    email: Optional[str]
    shipping_address: str
    payment_method: str
    payment_status: str
    order_status: str
    original_amount: Optional[float] = 0.0
    discount_amount: Optional[float] = 0.0
    voucher_code: Optional[str] = None
    total_amount: float
    notes: Optional[str]
    created_at: datetime
    items: List[OrderItemResponse] = []


    class Config:
        from_attributes = True

class OrderStatusUpdate(BaseModel):
    order_status: Optional[str] = None
    payment_status: Optional[str] = None

# Computer Vision Schemas
class FaceAnalysisRequest(BaseModel):
    face_shape: str # Tròn, Vuông, Trái xoan, Dài, Kim cương
    face_width_mm: Optional[float] = None
    estimated_pd: Optional[float] = None

class FaceAnalysisResponse(BaseModel):
    face_shape: str
    recommended_frame_shapes: List[str]
    recommended_size: str # S, M, L
    explanation: str
    matching_frames: List[FrameProductResponse] = []
