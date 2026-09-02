import os
import sys

# Thêm project root vào sys.path để Vercel serverless load được module app
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from app.main import app

# Export cho Vercel ASGI handler
handler = app
