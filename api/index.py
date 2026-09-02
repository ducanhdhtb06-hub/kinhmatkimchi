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
        headers_dict = {k.decode('latin1').lower(): v.decode('latin1') for k, v in scope.get("headers", [])}
        
        # Capture raw path details from all potential ASGI and Vercel variables
        scope_p = scope.get("path", "")
        raw_p = scope.get("raw_path", b"").decode('latin1')
        qs = scope.get("query_string", b"").decode('latin1')
        
        # Summary for diagnostic response header
        debug_info = f"path={scope_p}|raw={raw_p}|xmatched={headers_dict.get('x-matched-path')}|xinv={headers_dict.get('x-invoke-path')}"
        
        async def custom_send(event):
            if event["type"] == "http.response.start":
                event["headers"].append([b"x-vercel-debug-scope", debug_info.encode('latin1')])
            await send(event)
            
        await _app(scope, receive, custom_send)
    else:
        await _app(scope, receive, send)

handler = app
