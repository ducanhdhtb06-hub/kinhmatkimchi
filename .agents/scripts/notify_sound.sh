#!/bin/bash
# Đọc stdin từ Antigravity Hook Engine
INPUT=$(cat)

# Phát chuỗi 3 tiếng chuông nhịp điệu (Beep-Beep!)
python3 -c "
import time, sys, glob

for i in range(2):
    # Phát ra terminal hiện tại và mọi pts đang mở
    for pts in glob.glob('/dev/pts/*') + ['/dev/tty']:
        try:
            with open(pts, 'w') as f:
                f.write('\a')
                f.flush()
        except Exception:
            pass
    sys.stderr.write('\a')
    sys.stderr.flush()
    time.sleep(0.15)
" 2>/dev/null || true

# Trả về kết quả JSON chuẩn Stop Hook
echo '{"decision": "allow"}'
