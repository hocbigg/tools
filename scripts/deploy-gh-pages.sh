#!/usr/bin/env bash
set -e

# ----------------------------------------------------------------------
# 1. Khởi tạo & Kiểm tra tham số
# ----------------------------------------------------------------------
if [ -z "$1" ]; then
    echo "Usage: ./deploy.sh <repo_directory> [--force-update]"
    exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TARGET_ARG="$1"
FORCE_UPDATE=false

if [ "$2" = "--force-update" ]; then
    FORCE_UPDATE=true
fi

# Chuyển TARGET_ARG thành đường dẫn tuyệt đối
REPO_DIR="$(cd "$TARGET_ARG" 2>/dev/null && pwd || true)"

if [ -z "$REPO_DIR" ] || [ ! -d "$REPO_DIR/.git" ]; then
    echo "❌ Lỗi: '$TARGET_ARG' không phải là git repository hợp lệ."
    exit 1
fi

TARGET_BRANCH="gh-pages"
BUILD_SCRIPT="$SCRIPT_DIR/build.py" # Tên file python build của bạn

if [ ! -f "$BUILD_SCRIPT" ]; then
    echo "❌ Lỗi: Không tìm thấy trình build tại '$BUILD_SCRIPT'."
    exit 1
fi

# ----------------------------------------------------------------------
# 2. Thiết lập dọn dẹp tự động (Trap cleanup)
# ----------------------------------------------------------------------
TMP_DIR=""
INITIAL_BRANCH=""

cleanup() {
    # Xoá thư mục tạm nếu còn tồn tại
    if [ -n "$TMP_DIR" ] && [ -d "$TMP_DIR" ]; then
        rm -rf "$TMP_DIR"
    fi
    # Đảm bảo luôn quay lại branch ban đầu nếu script bị ngắt giữa chừng
    if [ -n "$INITIAL_BRANCH" ] && [ -d "$REPO_DIR" ]; then
        cd "$REPO_DIR"
        CURRENT=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || true)
        if [ "$CURRENT" != "$INITIAL_BRANCH" ]; then
            git checkout "$INITIAL_BRANCH" --quiet 2>/dev/null || true
        fi
    fi
}
trap cleanup EXIT

cd "$REPO_DIR"
INITIAL_BRANCH=$(git rev-parse --abbrev-ref HEAD)

# ----------------------------------------------------------------------
# 3. Kiểm tra trạng thái Git
# ----------------------------------------------------------------------
if [[ "$INITIAL_BRANCH" != "main" ]]; then
    echo "❌ Lỗi: Bạn đang ở branch '$INITIAL_BRANCH'. Vui lòng checkout về 'main' trước khi deploy."
    exit 1
fi

if ! git diff-index --quiet HEAD --; then
    echo "❌ Lỗi: Working tree trên branch 'main' chưa sạch (còn uncommitted changes)."
    echo "Vui lòng commit hoặc stash trước khi deploy để tránh mất code."
    exit 1
fi

# Tìm Remote (mặc định 'origin' nếu chưa cấu hình upstream)
UPSTREAM=$(git rev-parse --abbrev-ref --symbolic-full-name @{u} 2>/dev/null || true)
if [ -n "$UPSTREAM" ]; then
    REMOTE=${UPSTREAM%%/*}
else
    REMOTE="origin"
fi

MAIN_COMMIT=$(git rev-parse HEAD)

# ----------------------------------------------------------------------
# 4. Kiểm tra cache commit (Không cần checkout branch)
# ----------------------------------------------------------------------
LAST_COMMIT=$(git show "$TARGET_BRANCH:.last_build_commit" 2>/dev/null || true)

if [ "$LAST_COMMIT" = "$MAIN_COMMIT" ] && [ "$FORCE_UPDATE" = false ]; then
    echo "ℹ️  Không có thay đổi mới trên main ($MAIN_COMMIT). Bỏ qua deploy."
    exit 0
fi

# ----------------------------------------------------------------------
# 5. Tiến hành Build ra thư mục tạm độc lập
# ----------------------------------------------------------------------
echo "🚀 Đang build trang..."
TMP_DIR=$(mktemp -d)

# Chạy build script từ thư mục cha ($SCRIPT_DIR) để tránh bị lặp đường dẫn
(cd "$SCRIPT_DIR" && python3 "$BUILD_SCRIPT" "$TARGET_ARG")

OUT_DIR="$REPO_DIR/out"

if [ ! -d "$OUT_DIR" ]; then
    echo "❌ Lỗi: Thư mục output '$OUT_DIR' không tồn tại sau khi build."
    exit 1
fi

# Copy kết quả sang thư mục tạm an toàn
cp -r "$OUT_DIR"/. "$TMP_DIR"/

# ----------------------------------------------------------------------
# 6. Đưa lên nhánh gh-pages
# ----------------------------------------------------------------------
echo "📦 Chuyển sang branch $TARGET_BRANCH..."

# Đồng bộ thông tin branch từ remote (nếu có)
git fetch "$REMOTE" "$TARGET_BRANCH:$TARGET_BRANCH" 2>/dev/null || true

# Kiểm tra nếu branch gh-pages chưa tồn tại thì tạo orphan branch mới
if git show-ref --quiet --heads "$TARGET_BRANCH"; then
    git checkout "$TARGET_BRANCH"
else
    echo "Tạo mới branch $TARGET_BRANCH..."
    git checkout --orphan "$TARGET_BRANCH"
fi

echo "🧹 Dọn dẹp nội dung cũ trên $TARGET_BRANCH..."
git rm -rf . --quiet 2>/dev/null || true
# Xoá các file ẩn nếu có (trừ .git)
find . -maxdepth 1 ! -name '.' ! -name '..' ! -name '.git' -exec rm -rf {} +

echo "📋 Copy nội dung mới vào $TARGET_BRANCH..."
cp -r "$TMP_DIR"/. .

# Lưu vết commit main đã build
echo "$MAIN_COMMIT" > .last_build_commit

git add .

# Kiểm tra commit và tiến hành Force Push
if git diff-index --quiet HEAD --; then
    if [ "$FORCE_UPDATE" = true ]; then
        echo "⚠️  Nội dung file không đổi, nhưng tiến hành push do có --force-update..."
        git commit --allow-empty -m "Force deploy @ $MAIN_COMMIT ($(date '+%Y-%m-%d %H:%M:%S'))"
        echo "🚀 Đang force push lên $REMOTE $TARGET_BRANCH..."
        git push --force "$REMOTE" "$TARGET_BRANCH"
    else
        echo "ℹ️  Nội dung build hoàn toàn giống commit trước đó, bỏ qua push."
    fi
else
    git commit -m "Deploy from main @ $MAIN_COMMIT ($(date '+%Y-%m-%d %H:%M:%S'))"
    echo "🚀 Đang force push lên $REMOTE $TARGET_BRANCH..."
    git push --force "$REMOTE" "$TARGET_BRANCH"
fi

echo "↩️  Quay lại branch '$INITIAL_BRANCH'..."
git checkout "$INITIAL_BRANCH"

echo "✨ Deploy hoàn tất thành công!"