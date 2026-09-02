import os
import sys

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)
if os.path.join(project_root, "app") not in sys.path:
    sys.path.insert(0, os.path.join(project_root, "app"))

from urllib.parse import parse_qs, unquote
from app.main import app as _app

async def app(scope, receive, send):
    if scope.get("type") == "http":
        # 1. Đọc tham số path từ Vercel query string
        query_string = scope.get("query_string", b"").decode("latin1")
        params = parse_qs(query_string)
        if "path" in params and params["path"]:
            new_path = unquote(params["path"][0])
            if not new_path.startswith("/"):
                new_path = "/" + new_path
            while "//" in new_path:
                new_path = new_path.replace("//", "/")
            scope["path"] = new_path
            scope["raw_path"] = new_path.encode("utf-8")
        else:
            # 2. Đọc header x-matched-path nếu có
            headers = dict(scope.get("headers", []))
            matched_path = headers.get(b"x-matched-path") or headers.get(b"x-vercel-matched-path") or headers.get(b"x-forwarded-uri")
            if matched_path:
                orig_path = unquote(matched_path.decode('latin1').split("?")[0])
                for prefix in ["/api/index.py", "/api/index"]:
                    if orig_path.startswith(prefix + "/"):
                        orig_path = orig_path[len(prefix):]
                    elif orig_path == prefix:
                        orig_path = "/"
                if not orig_path.startswith("/"):
                    orig_path = "/" + orig_path
                while "//" in orig_path:
                    orig_path = orig_path.replace("//", "/")
                scope["path"] = orig_path
                scope["raw_path"] = orig_path.encode("utf-8")
            else:
                p = scope.get("path", "/")
                if p in ["/api/index.py", "/api/index", "/api"]:
                    scope["path"] = "/"
                    scope["raw_path"] = b"/"

    await _app(scope, receive, send)

handler = app
