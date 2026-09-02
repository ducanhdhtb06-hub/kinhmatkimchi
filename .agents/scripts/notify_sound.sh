#!/bin/bash
# Đọc stdin JSON từ Antigravity Hook Engine
INPUT=$(cat)

# Phát tiếng chuông Bell (\a / ASCII 0x07) báo hiệu hoàn thành
printf '\a' > /dev/tty 2>/dev/null || true
printf '\a' >&2 || true

# Xuất kết quả JSON hợp lệ theo chuẩn Antigravity Stop Hook
echo '{"decision": "allow"}'
