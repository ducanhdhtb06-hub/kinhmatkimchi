import os
import sys

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)
if os.path.join(project_root, "app") not in sys.path:
    sys.path.insert(0, os.path.join(project_root, "app"))

from urllib.parse import parse_qs, urlencode, unquote
from app.main import app as _app

async def app(scope, receive, send):
    if scope.get("type") == "http":
        query_bytes = scope.get("query_string", b"")
        qs = query_bytes.decode("latin1")
        params = parse_qs(qs, keep_blank_values=True)
        
        if "p" in params:
            p_val = unquote(params.pop("p")[0])
            if not p_val or p_val == "/":
                clean_path = "/"
            else:
                clean_path = p_val if p_val.startswith("/") else "/" + p_val
            
            # Clean duplicate slashes
            while "//" in clean_path:
                clean_path = clean_path.replace("//", "/")
                
            scope["path"] = clean_path
            scope["raw_path"] = clean_path.encode("utf-8")
            
            # Khôi phục các query param còn lại (nếu có)
            remaining_qs = urlencode(params, doseq=True)
            scope["query_string"] = remaining_qs.encode("latin1")
        else:
            # Fallback nếu gọi trực tiếp
            raw = scope.get("path", "/")
            for prefix in ["/api/index.py", "/api/index"]:
                if raw.startswith(prefix + "/"):
                    raw = raw[len(prefix):]
                elif raw == prefix:
                    raw = "/"
            scope["path"] = raw
            scope["raw_path"] = raw.encode("utf-8")

    await _app(scope, receive, send)

handler = app
