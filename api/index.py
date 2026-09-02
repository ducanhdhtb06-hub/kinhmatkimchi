import os
import sys

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)
if os.path.join(project_root, "app") not in sys.path:
    sys.path.insert(0, os.path.join(project_root, "app"))

from urllib.parse import unquote
from app.main import app as _app

async def app(scope, receive, send):
    if scope.get("type") == "http":
        headers = dict(scope.get("headers", []))
        
        # 1. Đọc URL gốc từ header Vercel
        matched = (
            headers.get(b"x-matched-path") or 
            headers.get(b"x-vercel-matched-path") or 
            headers.get(b"x-forwarded-uri")
        )
        
        if matched:
            raw_target = unquote(matched.decode('latin1').split("?")[0])
        else:
            raw_target = scope.get("path", "/")

        # 2. Loại bỏ tiền tố Vercel Serverless index file
        for prefix in ["/api/index.py", "/api/index"]:
            if raw_target.startswith(prefix + "/"):
                raw_target = raw_target[len(prefix):]
            elif raw_target == prefix:
                raw_target = "/"

        if not raw_target.startswith("/"):
            raw_target = "/" + raw_target
            
        while "//" in raw_target:
            raw_target = raw_target.replace("//", "/")

        scope["path"] = raw_target
        scope["raw_path"] = raw_target.encode("utf-8")

    await _app(scope, receive, send)

handler = app
