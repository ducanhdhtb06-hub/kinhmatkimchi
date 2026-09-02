import os
import sys

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from urllib.parse import parse_qs, urlencode, unquote
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles

try:
    from app.database import engine, Base, init_db_if_needed
    from app.routes import api, web
except (ImportError, ModuleNotFoundError):
    from database import engine, Base, init_db_if_needed
    from routes import api, web

app = FastAPI(
    title="Kính Mắt Kim Chi - Eyewear E-commerce & Computer Vision",
    description="Nền tảng thương mại điện tử kính mắt thông minh tích hợp AR Virtual Try-On",
    version="2.0.0"
)

# Chuẩn hóa đường dẫn Serverless Vercel ở tầng ASGI Middleware
class VercelPathMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            query_bytes = scope.get("query_string", b"")
            qs = query_bytes.decode("latin1")
            params = parse_qs(qs, keep_blank_values=True)
            
            if "p" in params:
                p_val = unquote(params.pop("p")[0])
                if not p_val or p_val == "/":
                    clean_path = "/"
                else:
                    clean_path = p_val if p_val.startswith("/") else "/" + p_val
                
                while "//" in clean_path:
                    clean_path = clean_path.replace("//", "/")
                    
                scope["path"] = clean_path
                scope["raw_path"] = clean_path.encode("utf-8")
                scope["query_string"] = urlencode(params, doseq=True).encode("latin1")
            else:
                path = scope.get("path", "/")
                for prefix in ["/api/index.py", "/api/index"]:
                    if path.startswith(prefix + "/"):
                        path = path[len(prefix):]
                        break
                    elif path == prefix:
                        path = "/"
                        break

                if not path.startswith("/"):
                    path = "/" + path
                while "//" in path:
                    path = path.replace("//", "/")

                scope["path"] = path
                scope["raw_path"] = path.encode("utf-8")

        await self.app(scope, receive, send)

app.add_middleware(VercelPathMiddleware)

init_db_if_needed()

# Static Files Directory
static_dir = os.path.join(current_dir, "static")
uploads_dir = os.path.join(static_dir, "uploads")
try:
    os.makedirs(uploads_dir, exist_ok=True)
except OSError:
    pass

if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Mount Routers
app.include_router(api.router)
app.include_router(web.router)

@app.get("/_debug_url")
def debug_url(request: Request):
    return {
        "url": str(request.url),
        "path": request.scope.get("path"),
        "raw_path": request.scope.get("raw_path", b"").decode("latin1"),
        "query_string": request.scope.get("query_string", b"").decode("latin1"),
        "headers": dict(request.headers)
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
