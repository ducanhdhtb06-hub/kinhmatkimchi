import os
import sys
from urllib.parse import parse_qs

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)
if os.path.join(project_root, "app") not in sys.path:
    sys.path.insert(0, os.path.join(project_root, "app"))

from app.main import app as _app

async def app(scope, receive, send):
    if scope.get("type") == "http":
        # 1. Đọc tham số path từ Vercel query string
        query_string = scope.get("query_string", b"").decode("utf-8")
        params = parse_qs(query_string)
        if "path" in params and params["path"]:
            new_path = params["path"][0]
            if not new_path.startswith("/"):
                new_path = "/" + new_path
            while "//" in new_path:
                new_path = new_path.replace("//", "/")
            scope["path"] = new_path
            scope["raw_path"] = new_path.encode("utf-8")
        else:
            # 2. Đọc header x-matched-path nếu có
            headers = dict(scope.get("headers", []))
            matched_path = headers.get(b"x-matched-path", b"").decode("utf-8")
            if matched_path:
                orig_path = matched_path.split("?")[0]
                for prefix in ["/api/index.py", "/api/index"]:
                    if orig_path.startswith(prefix + "/"):
                        orig_path = orig_path[len(prefix):]
                    elif orig_path == prefix:
                        orig_path = "/"
                scope["path"] = orig_path
                scope["raw_path"] = orig_path.encode("utf-8")

    await _app(scope, receive, send)

handler = app
