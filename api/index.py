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
        
        # 1. Đọc header x-matched-path từ Vercel
        matched = (
            headers.get(b"x-matched-path") or 
            headers.get(b"x-vercel-matched-path") or 
            headers.get(b"x-forwarded-uri")
        )
        
        if matched:
            raw = unquote(matched.decode('latin1').split("?")[0])
        else:
            raw = scope.get("path", "/")

        for prefix in ["/api/index.py", "/api/index"]:
            if raw.startswith(prefix + "/"):
                raw = raw[len(prefix):]
            elif raw == prefix:
                raw = "/"

        if not raw.startswith("/"):
            raw = "/" + raw

        while "//" in raw:
            raw = raw.replace("//", "/")

        scope["path"] = raw
        scope["raw_path"] = raw.encode("utf-8")

    await _app(scope, receive, send)

handler = app
