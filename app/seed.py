from sqlalchemy.orm import Session
from . import models

def seed_eyewear_data(db: Session):
    if db.query(models.Category).count() > 0:
        return

    print("🌱 Đang khởi tạo dữ liệu mẫu OptiStyle Pro...")

    # 1. Danh mục
    cat_optical = models.Category(name="Gọng Kính Cận", slug="gong-kinh-can", description="Gọng kính cận thời trang cao cấp, siêu nhẹ và bền bỉ", icon="fa-glasses")
    cat_sun = models.Category(name="Kính Râm / Kính Mát", slug="kinh-ram", description="Kính mát phân cực chống tia UV400 bảo vệ mắt tối đa", icon="fa-sun")
    cat_blue = models.Category(name="Kính Chống Ánh Sáng Xanh", slug="kinh-chong-anh-sang-xanh", description="Bảo vệ mắt khi dùng máy tính, điện thoại cho dân văn phòng & IT", icon="fa-laptop")
    cat_acc = models.Category(name="Phụ Kiện Kính", slug="phu-kien", description="Hộp kính, khăn lau nano, nước xịt vệ sinh tròng kính", icon="fa-box-open")

    db.add_all([cat_optical, cat_sun, cat_blue, cat_acc])
    db.commit()

    # 2. Tròng kính
    lenses = [
        models.LensProduct(
            name="Chemi Perfect UV 1.56 (Chống AS Xanh)",
            brand="Chemi Lens (Hàn Quốc)",
            lens_type="Kính Cận / Viễn / Loạn",
            index_refraction=1.56,
            is_blue_cut=True,
            is_photochromic=False,
            is_anti_scratch=True,
            price=350000,
            description="Tròng kính phổ thông được ưa chuộng nhất, ngăn 98% ánh sáng xanh có hại từ màn hình."
        ),
        models.LensProduct(
            name="Chemi Crystal Super Thin 1.60 (Mỏng & Trong suốt)",
            brand="Chemi Lens (Hàn Quốc)",
            lens_type="Kính Cận / Viễn / Loạn",
            index_refraction=1.60,
            is_blue_cut=True,
            is_photochromic=False,
            is_anti_scratch=True,
            price=650000,
            description="Mỏng hơn 25% so với tròng thường, chống bám bụi và chống bám nước vượt trội."
        ),
        models.LensProduct(
            name="Essilor Crizal Sapphire HR 1.67 (Siêu Mỏng & Chống Chói)",
            brand="Essilor (Pháp)",
            lens_type="Kính Cận / Viễn / Loạn",
            index_refraction=1.67,
            is_blue_cut=True,
            is_photochromic=False,
            is_anti_scratch=True,
            price=1450000,
            description="Thương hiệu số 1 thế giới từ Pháp, siêu mỏng, phủ nano chống chói 360 độ, phù hợp độ cận từ 3.00 đến 8.00 Diop."
        ),
        models.LensProduct(
            name="Chemi Transitions Photochromic 1.56 (Đổi Màu Trà / Xám Khói)",
            brand="Chemi Transitions",
            lens_type="Kính Đổi Màu",
            index_refraction=1.56,
            is_blue_cut=True,
            is_photochromic=True,
            is_anti_scratch=True,
            price=950000,
            description="Tròng kính 2 trong 1: Trong suốt khi ở trong nhà, tự động đổi màu râm mát khi ra nắng bảo vệ mắt khỏi tia UV."
        ),
        models.LensProduct(
            name="Kính Không Độ 0.00D (Thời trang / Chống bụi)",
            brand="OptiStyle Standard",
            lens_type="Kính 0 Độ",
            index_refraction=1.56,
            is_blue_cut=True,
            is_photochromic=False,
            is_anti_scratch=True,
            price=150000,
            description="Tròng kính 0 độ chuẩn quang học, chuyên dùng cho khách hàng đeo thời trang hoặc đi đường chống bụi."
        )
    ]
    db.add_all(lenses)
    db.commit()

    # 3. Gọng Kính
    frames = [
        models.FrameProduct(
            category_id=cat_optical.id,
            name="Gọng Titan Tối Giản Opti-Titan 01",
            brand="Kim Chi Signature",
            sku="OPT-TITAN-01",
            price=850000,
            original_price=1200000,
            material="Titanium",
            shape="Vuông",
            gender="Unisex",
            suitable_face_shapes="Tròn,Trái xoan,Dài",
            eye_size=52,
            bridge_size=18,
            temple_size=142,
            frame_width=138,
            image_url="https://images.unsplash.com/photo-1572635196237-14b3f281503f?w=600&auto=format&fit=crop&q=80",
            tryon_overlay_url="/static/img/frames/square_black.svg",
            description="Gọng kính chế tác từ Titanium nguyên khối siêu nhẹ (chỉ 8.5g), chống ăn mòn và không gây dị ứng da. Phù hợp cho người đeo kính làm việc cả ngày.",
            stock=25,
            is_featured=True
        ),
        models.FrameProduct(
            category_id=cat_optical.id,
            name="Gọng Tròn Retro Gold Havana",
            brand="Retro Vintage",
            sku="RTO-GOLD-02",
            price=650000,
            original_price=900000,
            material="Kim loại",
            shape="Tròn",
            gender="Unisex",
            suitable_face_shapes="Vuông,Trái xoan,Dài",
            eye_size=50,
            bridge_size=20,
            temple_size=140,
            frame_width=135,
            image_url="https://images.unsplash.com/photo-1511499767150-a48a237f0083?w=600&auto=format&fit=crop&q=80",
            tryon_overlay_url="/static/img/frames/round_gold.svg",
            description="Phong cách trí thức thanh lịch thập niên 80. Viền kim loại mạ vàng sang trọng kết hợp ve mũi silicon êm ái.",
            stock=18,
            is_featured=True
        ),
        models.FrameProduct(
            category_id=cat_sun.id,
            name="Kính Mát Phi Công Aviator Classic Silver",
            brand="OptiStyle Polarized",
            sku="SUN-AVIATOR-03",
            price=1150000,
            original_price=1500000,
            material="Kim loại",
            shape="Aviator",
            gender="Nam",
            suitable_face_shapes="Vuông,Trái xoan,Tròn",
            eye_size=58,
            bridge_size=15,
            temple_size=145,
            frame_width=142,
            image_url="https://images.unsplash.com/photo-1508296695146-257a814070b4?w=600&auto=format&fit=crop&q=80",
            tryon_overlay_url="/static/img/frames/aviator_silver.svg",
            description="Huyền thoại kính phi công viền bạc sắc nét. Tròng kính phân cực Polarized chống lóa hoàn hảo khi lái xe dưới trời nắng gắt.",
            stock=15,
            is_featured=True
        ),
        models.FrameProduct(
            category_id=cat_optical.id,
            name="Gọng Mắt Mèo Cat-Eye Đồi Mồi Nữ Tính",
            brand="Glamour Paris",
            sku="GLAM-CATEYE-04",
            price=720000,
            original_price=950000,
            material="Acetate",
            shape="Mắt mèo",
            gender="Nữ",
            suitable_face_shapes="Tròn,Trái xoan,Kim cương",
            eye_size=53,
            bridge_size=17,
            temple_size=140,
            frame_width=136,
            image_url="https://images.unsplash.com/photo-1591076482161-42ce6da69f67?w=600&auto=format&fit=crop&q=80",
            tryon_overlay_url="/static/img/frames/cateye_tortoise.svg",
            description="Đường nét mắt mèo xếch nhẹ tạo vẻ cuốn hút và tôn dáng gò má của phái nữ. Nhựa Acetate vân đồi mồi sáng bóng không phai màu.",
            stock=12,
            is_featured=True
        ),
        models.FrameProduct(
            category_id=cat_blue.id,
            name="Gọng Cổ Điển Browline Clubmaster Black/Gold",
            brand="Classic Club",
            sku="CLUB-BROW-05",
            price=890000,
            original_price=1250000,
            material="Acetate",
            shape="Browline",
            gender="Unisex",
            suitable_face_shapes="Tròn,Trái xoan,Kim cương",
            eye_size=51,
            bridge_size=19,
            temple_size=142,
            frame_width=139,
            image_url="https://images.unsplash.com/photo-1577803645773-f96470509666?w=600&auto=format&fit=crop&q=80",
            tryon_overlay_url="/static/img/frames/browline_vintage.svg",
            description="Thiết kế viền trên đậm cá tính mang lại vẻ lịch lãm cho các buổi họp và phong thái chuyên nghiệp nơi công sở.",
            stock=20,
            is_featured=True
        ),
        models.FrameProduct(
            category_id=cat_optical.id,
            name="Gọng Nhựa Dẻo TR90 Siêu Bền Chống Gãy",
            brand="FlexComfort",
            sku="FLEX-TR90-06",
            price=450000,
            original_price=600000,
            material="Nhựa TR90",
            shape="Chữ nhật",
            gender="Unisex",
            suitable_face_shapes="Tròn,Trái xoan",
            eye_size=54,
            bridge_size=17,
            temple_size=140,
            frame_width=138,
            image_url="https://images.unsplash.com/photo-1473496169904-658ba7c44d8a?w=600&auto=format&fit=crop&q=80",
            tryon_overlay_url="/static/img/frames/square_black.svg",
            description="Chất liệu TR90 đàn hồi cực cao, có thể uốn cong mà không sợ gãy. Lý tưởng cho học sinh, sinh viên và người thường xuyên vận động.",
            stock=30,
            is_featured=False
        )
    ]
    db.add_all(frames)
    db.commit()

    # 4. Đơn hàng mẫu
    order1 = models.Order(
        order_code="OPT-260901-A1B2",
        customer_name="Hoàng Minh Tuấn",
        phone="0988776655",
        email="tuan.hoang@gmail.com",
        shipping_address="Tòa nhà Landmark 81, P. 22, Q. Bình Thạnh, TP. Hồ Chí Minh",
        payment_method="COD",
        payment_status="Chờ thanh toán",
        order_status="Đang mài tròng",
        total_amount=1500000,
        notes="Giao vào giờ hành chính, gọi trước 15 phút."
    )
    db.add(order1)
    db.flush()

    item1 = models.OrderItem(
        order_id=order1.id,
        frame_id=frames[0].id, # Gọng Titan
        lens_id=lenses[1].id,  # Tròng 1.60
        frame_price=850000,
        lens_price=650000,
        quantity=1,
        right_sph=-2.25,
        right_cyl=-0.50,
        right_axis=180,
        left_sph=-2.75,
        left_cyl=0.0,
        left_axis=0,
        pd=63.0,
        notes="Yêu cầu vát mỏng cạnh tròng kính."
    )
    db.add(item1)
    db.commit()

    print("✅ Đã nạp thành công 4 danh mục, 5 loại tròng, 6 gọng kính và đơn hàng mẫu!")
