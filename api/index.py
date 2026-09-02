import os
import sys

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)
if os.path.join(project_root, "app") not in sys.path:
    sys.path.insert(0, os.path.join(project_root, "app"))

from app.main import app as _app

async def app(scope, receive, send):
    if scope.get("type") == "http":
        headers = dict(scope.get("headers", []))
        
        # Lấy URL ban đầu từ các header đặc trưng của Vercel
        matched = (
            headers.get(b"x-matched-path") or 
            headers.get(b"x-vercel-matched-path") or 
            headers.get(b"x-forwarded-uri") or
            headers.get(b"x-invoke-path")
        )
        
        if matched:
            orig = matched.decode('latin1').split("?")[0]
            # Loại bỏ prefix /api/index hoặc /api nếu có
            for prefix in ["/api/index.py", "/api/index"]:
                if orig.startswith(prefix + "/"):
                    orig = orig[len(prefix):]
                elif orig == prefix:
                    orig = "/"
            if not orig.startswith("/"):
                orig = "/" + orig
            scope["path"] = orig
            scope["raw_path"] = orig.encode("utf-8")
        else:
            # Fallback nếu không có header
            p = scope.get("path", "/")
            if p in ["/api/index.py", "/api/index", "/api"]:
                scope["path"] = "/"
                scope["raw_path"] = b"/"

    await _app(scope, receive, send)

handler = app
