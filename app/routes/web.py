import os
import hmac
import hashlib
import time
from typing import Optional
from fastapi import APIRouter, Request, Depends, HTTPException, Form, Response, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

try:
    from app.database import get_db
    from app import crud, models
except (ImportError, ModuleNotFoundError):
    from ..database import get_db
    from .. import crud, models

router = APIRouter(include_in_schema=False)

current_dir = os.path.dirname(os.path.abspath(__file__))
templates_dir = os.path.join(os.path.dirname(current_dir), "app", "templates")
if not os.path.exists(templates_dir):
    templates_dir = os.path.join(os.path.dirname(current_dir), "templates")
if not os.path.exists(templates_dir):
    templates_dir = "app/templates"

templates = Jinja2Templates(directory=templates_dir)

# ==================== UNIVERSAL USER SESSION AUTH ====================

SESSION_SECRET = "kimchi_universal_user_session_secret_2026"

def sign_user_token(user_id: int, role: str) -> str:
    timestamp = str(int(time.time()))
    payload = f"{user_id}:{role}:{timestamp}"
    signature = hmac.new(SESSION_SECRET.encode('utf-8'), payload.encode('utf-8'), hashlib.sha256).hexdigest()
    return f"{payload}:{signature}"

def verify_user_token(token: Optional[str]) -> Optional[dict]:
    if not token or ":" not in token:
        return None
    parts = token.split(":")
    if len(parts) != 4:
        return None
    user_id_str, role, timestamp, signature = parts
    
    # Check expiry (7 days)
    try:
        ts = int(timestamp)
        if time.time() - ts > 7 * 86400:
            return None
        user_id = int(user_id_str)
    except ValueError:
        return None

    expected_payload = f"{user_id_str}:{role}:{timestamp}"
    expected_sig = hmac.new(SESSION_SECRET.encode('utf-8'), expected_payload.encode('utf-8'), hashlib.sha256).hexdigest()
    if hmac.compare_digest(expected_sig, signature):
        return {"user_id": user_id, "role": role}
    return None

def get_current_user_from_cookie(request: Request, db: Session) -> Optional[models.User]:
    # Ensure default users exist
    crud.ensure_default_accounts(db)
    token = request.cookies.get("kimchi_user_token")
    verified = verify_user_token(token)
    if not verified:
        return None
    return crud.get_user_by_id(db, verified["user_id"])


# ==================== AUTHENTICATION & MEMBERSHIP ROUTES ====================

@router.get("/login", response_class=HTMLResponse)
def page_login(request: Request, next: Optional[str] = None, db: Session = Depends(get_db)):
    user = get_current_user_from_cookie(request, db)
    if user:
        return RedirectResponse(url=next or "/", status_code=status.HTTP_303_SEE_OTHER)

    return templates.TemplateResponse(
        request=request,
        name="login.html",
        context={
            "page_title": "Đăng Nhập / Đăng Ký - Kính Mắt Kim Chi",
            "active_nav": "login",
            "current_user": None,
            "next_url": next or "/",
            "initial_tab": "login",
            "error_message": None,
            "success_message": None
        }
    )

@router.post("/login")
def action_login(
    request: Request,
    identifier: str = Form(...),
    password: str = Form(...),
    next_url: str = Form("/"),
    db: Session = Depends(get_db)
):
    crud.ensure_default_accounts(db)
    user = crud.authenticate_user(db, identifier=identifier, password=password)
    if not user:
        return templates.TemplateResponse(
            request=request,
            name="login.html",
            context={
                "page_title": "Đăng Nhập / Đăng Ký - Kính Mắt Kim Chi",
                "active_nav": "login",
                "current_user": None,
                "next_url": next_url,
                "initial_tab": "login",
                "error_message": "Tài khoản hoặc mật khẩu không chính xác!",
                "success_message": None
            },
            status_code=status.HTTP_401_UNAUTHORIZED
        )

    target_url = next_url if next_url and next_url != "/login" else ("/" if user.role != "admin" else "/admin")
    response = RedirectResponse(url=target_url, status_code=status.HTTP_303_SEE_OTHER)
    token = sign_user_token(user.id, user.role)
    response.set_cookie(
        key="kimchi_user_token",
        value=token,
        max_age=7 * 86400,
        httponly=True,
        samesite="lax"
    )
    return response

@router.post("/register")
def action_register(
    request: Request,
    full_name: str = Form(...),
    email: str = Form(...),
    phone: str = Form(...),
    password: str = Form(...),
    next_url: str = Form("/"),
    db: Session = Depends(get_db)
):
    crud.ensure_default_accounts(db)
    if len(password) < 6:
        return templates.TemplateResponse(
            request=request,
            name="login.html",
            context={
                "page_title": "Đăng Nhập / Đăng Ký - Kính Mắt Kim Chi",
                "active_nav": "login",
                "current_user": None,
                "next_url": next_url,
                "initial_tab": "register",
                "error_message": "Mật khẩu phải có độ dài tối thiểu 6 ký tự!",
                "success_message": None
            },
            status_code=status.HTTP_400_BAD_REQUEST
        )

    existing_user = crud.get_user_by_email_or_phone(db, email) or crud.get_user_by_email_or_phone(db, phone)
    if existing_user:
        return templates.TemplateResponse(
            request=request,
            name="login.html",
            context={
                "page_title": "Đăng Nhập / Đăng Ký - Kính Mắt Kim Chi",
                "active_nav": "login",
                "current_user": None,
                "next_url": next_url,
                "initial_tab": "register",
                "error_message": "Email hoặc Số điện thoại này đã được đăng ký tài khoản!",
                "success_message": None
            },
            status_code=status.HTTP_400_BAD_REQUEST
        )

    new_user = crud.create_customer_user(
        db=db,
        email=email,
        phone=phone,
        full_name=full_name,
        password=password,
        role="customer"
    )

    response = RedirectResponse(url=next_url or "/", status_code=status.HTTP_303_SEE_OTHER)
    token = sign_user_token(new_user.id, new_user.role)
    response.set_cookie(
        key="kimchi_user_token",
        value=token,
        max_age=7 * 86400,
        httponly=True,
        samesite="lax"
    )
    return response

@router.get("/logout")
def action_logout():
    response = RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
    response.delete_cookie("kimchi_user_token")
    return response

# Backward compatibility alias
@router.get("/admin/login")
def admin_login_alias():
    return RedirectResponse(url="/login?next=/admin", status_code=status.HTTP_303_SEE_OTHER)

@router.get("/admin/logout")
def admin_logout_alias():
    return RedirectResponse(url="/logout", status_code=status.HTTP_303_SEE_OTHER)


# ==================== STOREFRONT & PUBLIC WEB ROUTES ====================

@router.get("/", response_class=HTMLResponse)
def page_homepage(request: Request, db: Session = Depends(get_db)):
    user = get_current_user_from_cookie(request, db)
    featured_frames = crud.get_frames(db, is_featured=True, limit=6)
    categories = crud.get_categories(db)
    lenses = crud.get_lenses(db)

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "page_title": "Kính Mắt Kim Chi - Kính Mắt Thông Minh & AR Virtual Try-On",
            "active_nav": "home",
            "current_user": user,
            "featured_frames": featured_frames,
            "categories": categories,
            "lenses": lenses
        }
    )

@router.get("/products", response_class=HTMLResponse)
def page_products_catalog(
    request: Request,
    category: Optional[str] = None,
    shape: Optional[str] = None,
    material: Optional[str] = None,
    gender: Optional[str] = None,
    face_shape: Optional[str] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db)
):
    user = get_current_user_from_cookie(request, db)
    categories = crud.get_categories(db)
    category_id = None
    if category:
        cat_obj = crud.get_category_by_slug(db, category)
        if cat_obj:
            category_id = cat_obj.id

    frames = crud.get_frames(
        db=db,
        category_id=category_id,
        shape=shape,
        material=material,
        gender=gender,
        face_shape=face_shape,
        search=search,
        limit=50
    )

    return templates.TemplateResponse(
        request=request,
        name="products.html",
        context={
            "page_title": "Bộ Sưu Tập Gọng Kính Cao Cấp - Kính Mắt Kim Chi",
            "active_nav": "products",
            "current_user": user,
            "frames": frames,
            "categories": categories,
            "selected_category": category,
            "selected_shape": shape,
            "selected_material": material,
            "selected_gender": gender,
            "selected_face_shape": face_shape,
            "search_query": search
        }
    )

@router.get("/products/{frame_id}", response_class=HTMLResponse)
def page_product_detail(request: Request, frame_id: int, db: Session = Depends(get_db)):
    user = get_current_user_from_cookie(request, db)
    frame = crud.get_frame_by_id(db, frame_id)
    if not frame:
        raise HTTPException(status_code=404, detail="Sản phẩm gọng kính không tồn tại")
    
    lenses = crud.get_lenses(db)
    related_frames = crud.get_frames(db, category_id=frame.category_id, limit=4)
    related_frames = [f for f in related_frames if f.id != frame.id]

    return templates.TemplateResponse(
        request=request,
        name="product_detail.html",
        context={
            "page_title": f"{frame.name} - Kính Mắt Kim Chi",
            "active_nav": "products",
            "current_user": user,
            "frame": frame,
            "lenses": lenses,
            "related_frames": related_frames
        }
    )

@router.get("/tryon", response_class=HTMLResponse)
def page_virtual_tryon(
    request: Request,
    frame_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    user = get_current_user_from_cookie(request, db)
    frames = crud.get_frames(db, limit=30)
    selected_frame = None
    if frame_id:
        selected_frame = crud.get_frame_by_id(db, frame_id)
    if not selected_frame and frames:
        selected_frame = frames[0]

    return templates.TemplateResponse(
        request=request,
        name="tryon.html",
        context={
            "page_title": "Phòng Thử Kính Ảo AR - Kính Mắt Kim Chi",
            "active_nav": "tryon",
            "current_user": user,
            "frames": frames,
            "selected_frame": selected_frame
        }
    )

@router.get("/prescription-scan", response_class=HTMLResponse)
def page_prescription_scanner(request: Request, db: Session = Depends(get_db)):
    user = get_current_user_from_cookie(request, db)
    return templates.TemplateResponse(
        request=request,
        name="prescription_scanner.html",
        context={
            "page_title": "Quét Phiếu Khám Mắt AI OCR - Kính Mắt Kim Chi",
            "active_nav": "prescription_scan",
            "current_user": user
        }
    )

# Convenient Alias Redirects
@router.get("/scan")
@router.get("/scanner")
@router.get("/prescription")
@router.get("/prescriptions")
@router.get("/ocr")
@router.get("/vision-test")
def page_prescription_aliases():
    return RedirectResponse(url="/prescription-scan", status_code=status.HTTP_302_FOUND)

@router.get("/virtual-tryon")
@router.get("/virtualtryon")
@router.get("/ar")
def page_tryon_aliases():
    return RedirectResponse(url="/tryon", status_code=status.HTTP_302_FOUND)

@router.get("/cart", response_class=HTMLResponse)
def page_cart(request: Request, db: Session = Depends(get_db)):
    user = get_current_user_from_cookie(request, db)
    return templates.TemplateResponse(
        request=request,
        name="cart.html",
        context={
            "page_title": "Giỏ Hàng & Cắt Tròng - Kính Mắt Kim Chi",
            "active_nav": "cart",
            "current_user": user
        }
    )

@router.get("/checkout", response_class=HTMLResponse)
def page_checkout(request: Request, db: Session = Depends(get_db)):
    user = get_current_user_from_cookie(request, db)
    if not user:
        return RedirectResponse(url="/login?next=/checkout", status_code=status.HTTP_303_SEE_OTHER)

    return templates.TemplateResponse(
        request=request,
        name="checkout.html",
        context={
            "page_title": "Thanh Toán Đơn Hàng - Kính Mắt Kim Chi",
            "active_nav": "cart",
            "current_user": user
        }
    )

@router.get("/orders/success/{order_code}", response_class=HTMLResponse)
def page_order_success(request: Request, order_code: str, db: Session = Depends(get_db)):
    user = get_current_user_from_cookie(request, db)
    if not user:
        return RedirectResponse(url=f"/login?next=/orders/success/{order_code}", status_code=status.HTTP_303_SEE_OTHER)

    order = crud.get_order_by_code(db, order_code)
    if not order:
        raise HTTPException(status_code=404, detail="Không tìm thấy đơn hàng")

    return templates.TemplateResponse(
        request=request,
        name="order_success.html",
        context={
            "page_title": f"Đặt Hàng Thành Công #{order.order_code} - Kính Mắt Kim Chi",
            "active_nav": "orders",
            "current_user": user,
            "order": order
        }
    )

@router.get("/orders/track", response_class=HTMLResponse)
def page_order_track(request: Request, db: Session = Depends(get_db)):
    user = get_current_user_from_cookie(request, db)
    if not user:
        return RedirectResponse(url="/login?next=/orders/track", status_code=status.HTTP_303_SEE_OTHER)

    return templates.TemplateResponse(
        request=request,
        name="order_track.html",
        context={
            "page_title": "Tra Cứu Đơn Hàng - Kính Mắt Kim Chi",
            "active_nav": "orders",
            "current_user": user
        }
    )

@router.get("/profile", response_class=HTMLResponse)
def page_customer_profile(request: Request, db: Session = Depends(get_db)):
    user = get_current_user_from_cookie(request, db)
    if not user:
        return RedirectResponse(url="/login?next=/profile", status_code=status.HTTP_303_SEE_OTHER)

    user_orders = crud.get_orders_by_user(db, user.id)

    return templates.TemplateResponse(
        request=request,
        name="profile.html",
        context={
            "page_title": "Hồ Sơ Cá Nhân & Đơn Hàng - Kính Mắt Kim Chi",
            "active_nav": "profile",
            "current_user": user,
            "user_orders": user_orders
        }
    )


# ==================== SECURED ADMIN DASHBOARD ====================

@router.get("/admin", response_class=HTMLResponse)
def page_admin_dashboard(request: Request, db: Session = Depends(get_db)):
    crud.ensure_default_accounts(db)
    user = get_current_user_from_cookie(request, db)
    if not user:
        return RedirectResponse(url="/login?next=/admin", status_code=status.HTTP_303_SEE_OTHER)
    
    if user.role != "admin":
        return templates.TemplateResponse(
            request=request,
            name="login.html",
            context={
                "page_title": "Đăng Nhập Quản Trị Viên - Kính Mắt Kim Chi",
                "active_nav": "login",
                "current_user": user,
                "next_url": "/admin",
                "initial_tab": "login",
                "error_message": f"Tài khoản hiện tại ({user.email}) là Khách hàng. Vui lòng đăng nhập tài khoản Quản trị viên (admin) để vào Bảng quản trị!",
                "success_message": None
            },
            status_code=status.HTTP_403_FORBIDDEN
        )

    stats = crud.get_admin_dashboard_stats(db)
    frames = crud.get_frames(db, limit=100)
    orders = crud.get_orders(db, limit=50)

    return templates.TemplateResponse(
        request=request,
        name="admin.html",
        context={
            "page_title": "Quản Trị Hệ Thống - Kính Mắt Kim Chi",
            "active_nav": "admin",
            "current_user": user,
            "admin_username": user.full_name,
            "stats": stats,
            "frames": frames,
            "orders": orders
        }
    )
