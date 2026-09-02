import os
import sys

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)
if os.path.join(project_root, "app") not in sys.path:
    sys.path.insert(0, os.path.join(project_root, "app"))

from app.main import app as fastapi_app

class VercelPathFixer:
    """ASGI Middleware tương thích 100% với hệ thống định tuyến Serverless của Vercel."""
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope.get("type") == "http":
            path = scope.get("path", "/")
            if path.startswith("/api/index.py"):
                sub_path = path[len("/api/index.py"):]
                scope["path"] = sub_path if sub_path.startswith("/") else "/" + sub_path
                scope["raw_path"] = scope["path"].encode("utf-8")
            elif path == "/api" or path == "/api/":
                scope["path"] = "/"
                scope["raw_path"] = b"/"
        await self.app(scope, receive, send)

app = VercelPathFixer(fastapi_app)
