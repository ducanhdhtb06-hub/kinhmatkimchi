#!/bin/bash
# ==============================================================================
# SCRIPT TỰ ĐỘNG ĐẨY MÃ NGUỒN LÊN GOOGLE CLOUD RUN (OPTISTYLE PRO)
# ==============================================================================

set -e

# 1. Nạp Google Cloud SDK vào PATH
if [ -f "/home/anh/google-cloud-sdk/path.bash.inc" ]; then
    source "/home/anh/google-cloud-sdk/path.bash.inc"
fi

echo "======================================================================"
echo "🚀 BẮT ĐẦU TRIỂN KHAI OPTISTYLE PRO LÊN GOOGLE CLOUD RUN"
echo "======================================================================"

# 2. Kiểm tra đăng nhập Google
CURRENT_ACCOUNT=$(gcloud auth list --filter=status:ACTIVE --format="value(account)" 2>/dev/null || echo "")

if [ -z "$CURRENT_ACCOUNT" ]; then
    echo "🔑 Đang mở trình duyệt để xác thực tài khoản Google của bạn..."
    gcloud auth login --no-launch-browser
else
    echo "✅ Đang sử dụng tài khoản Google: $CURRENT_ACCOUNT"
fi

# 3. Lấy hoặc chọn Project ID
PROJECT_ID=$(gcloud config get-value project 2>/dev/null || echo "")

if [ -z "$PROJECT_ID" ] || [ "$PROJECT_ID" == "(unset)" ]; then
    echo ""
    echo "📋 Danh sách các Project trên Google Cloud của bạn:"
    gcloud projects list || true
    echo ""
    read -p "👉 Vui lòng nhập Project ID của bạn: " USER_PROJECT_ID
    gcloud config set project "$USER_PROJECT_ID"
    PROJECT_ID="$USER_PROJECT_ID"
fi

echo "🎯 Project hiện tại: $PROJECT_ID"

# 4. Kích hoạt các API cần thiết trên Google Cloud (Cloud Run & Cloud Build)
echo "⚡ Đang kích hoạt Google Cloud Run API & Cloud Build API..."
gcloud services enable run.googleapis.com cloudbuild.googleapis.com artifactregistry.googleapis.com || true

# 5. Triển khai ứng dụng lên Cloud Run
echo ""
echo "📦 Đang đóng gói container và triển khai lên máy chủ Google (Singapore - asia-southeast1)..."
gcloud run deploy optistyle-pro \
    --source . \
    --region asia-southeast1 \
    --allow-unauthenticated \
    --memory 2Gi \
    --cpu 2 \
    --port 8000 \
    --timeout 300

echo ""
echo "======================================================================"
echo "🎉 TRIỂN KHAI THÀNH CÔNG LÊN GOOGLE CLOUD RUN!"
echo "👉 Truy cập đường link HTTPS hiển thị ở trên để sử dụng web bán kính mắt AI!"
echo "======================================================================"
