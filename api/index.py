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
        path = scope.get("path", "/")
        for prefix in ["/api/index.py", "/api/index"]:
            if path.startswith(prefix):
                path = path[len(prefix):]
                if not path.startswith("/"):
                    path = "/" + path
                scope["path"] = path
                scope["raw_path"] = path.encode("utf-8")
                break
    await _app(scope, receive, send)

# Also keep handler for AWS Lambda / Vercel legacy
handler = app
