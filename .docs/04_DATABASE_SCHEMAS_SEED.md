# 🗄️ DATABASE SCHEMAS & DỮ LIỆU SEED (SQLITE / SQLALCHEMY)

## 1. DANH SÁCH BẢNG CƠ SỞ DỮ LIỆU (`models.py`)

### 1.1. `users` (Tài khoản người dùng)
* `id` (Integer, Primary Key)
* `email` (String, Unique)
* `username` (String, Unique)
* `hashed_password` (String)
* `full_name` (String)
* `phone` (String)
* `role` (String: `admin`, `customer`)
* `saved_prescription` (JSON: `right_sph`, `right_cyl`, `right_axis`, `left_sph`, `left_cyl`, `left_axis`, `pd`)

### 1.2. `categories` (Danh mục kính)
* `id`, `name`, `slug`, `description`, `icon`

### 1.3. `frames` (Sản phẩm Gọng kính)
* `id`, `category_id`, `name`, `slug`, `price`, `original_price`, `material`, `shape`, `gender`, `color`, `image_url`, `tryon_image_url`, `model_3d_url`, `lens_width`, `bridge_width`, `temple_length`, `is_featured`, `stock`

### 1.4. `lenses` (Tròng kính quang học)
* `id`, `name`, `index_value` (1.56, 1.60, 1.67, 1.74), `coating`, `price`, `description`, `features` (Chống UV, Chống ánh sáng xanh, Đổi màu, Siêu mỏng)

### 1.5. `orders` & `order_items` (Đơn hàng & Chi tiết tròng gọng)
* `id`, `order_code` (e.g. `KC-260901-XXXX`), `user_id`, `customer_name`, `phone`, `email`, `shipping_address`, `payment_method` (`vietqr`, `cod`), `payment_status` (`unpaid`, `paid`), `order_status` (`pending`, `processing`, `shipping`, `completed`, `cancelled`), `original_amount`, `discount_amount`, `voucher_code`, `total_amount`

### 1.6. `vouchers` (Mã giảm giá)
* `code` (e.g. `KIMCHI50K`, `KIMCHI10`), `name`, `discount_type` (`fixed`, `percent`), `discount_value`, `min_order_amount`, `max_discount`, `usage_limit`, `used_count`, `is_active`

### 1.7. `system_settings` (Cấu hình VietQR & Telegram Bot)
* `vietqr_bank_id`, `vietqr_account_no`, `vietqr_account_name`, `telegram_bot_token`, `telegram_chat_id`
