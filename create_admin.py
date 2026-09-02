import sys
import getpass
from app.database import SessionLocal
from app import models, crud

def main():
    print("=" * 60)
    print("🔒 TẠO HOẶC ĐẶT LẠI MẬT KHẨU QUẢN TRỊ VIÊN (ADMIN)")
    print("=" * 60)

    if len(sys.argv) >= 3:
        username = sys.argv[1].strip()
        password = sys.argv[2].strip()
    else:
        username = input("👉 Nhập Tên đăng nhập Admin muốn tạo: ").strip()
        if not username:
            print("❌ Tên đăng nhập không được để trống!")
            return
        password = getpass.getpass("👉 Nhập Mật khẩu Admin bảo mật: ").strip()
        if len(password) < 6:
            print("❌ Mật khẩu phải có tối thiểu 6 ký tự!")
            return

    db = SessionLocal()
    # Check if admin already exists
    admin = db.query(models.AdminUser).filter(models.AdminUser.username == username).first()
    if admin:
        admin.password_hash = crud.hash_password(password)
        db.commit()
        print(f"✅ Đã cập nhật mật khẩu mới cho quản trị viên '{username}' thành công!")
    else:
        new_admin = models.AdminUser(
            username=username,
            password_hash=crud.hash_password(password),
            full_name="Chủ Cửa Hàng Kim Chi",
            is_active=True
        )
        db.add(new_admin)
        db.commit()
        print(f"🎉 Đã tạo tài khoản Quản trị viên '{username}' thành công!")

    db.close()
    print("=" * 60)

if __name__ == "__main__":
    main()
