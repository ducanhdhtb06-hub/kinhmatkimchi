import os
import sys
import json

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)
if os.path.join(project_root, "app") not in sys.path:
    sys.path.insert(0, os.path.join(project_root, "app"))

from app.main import app as fastapi_app

async def app(scope, receive, send):
    if scope.get("type") == "http":
        headers_dict = {k.decode('latin1'): v.decode('latin1') for k, v in scope.get("headers", [])}
        
        # Test endpoint to see exact Vercel scope & headers
        if scope.get("path") == "/_debug_scope" or headers_dict.get("x-matched-path") == "/_debug_scope":
            body = json.dumps({
                "path": scope.get("path"),
                "raw_path": scope.get("raw_path", b"").decode('latin1'),
                "query_string": scope.get("query_string", b"").decode('latin1'),
                "headers": headers_dict
            }, indent=2).encode('utf-8')
            
            await send({
                'type': 'http.response.start',
                'status': 200,
                'headers': [[b'content-type', b'application/json']]
            })
            await send({
                'type': 'http.response.body',
                'body': body
            })
            return

    await fastapi_app(scope, receive, send)

handler = app
