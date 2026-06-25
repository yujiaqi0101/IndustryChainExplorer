#!/usr/bin/env bash
# 一键启动前后端（开发模式）
# 用法：bash scripts/dev.sh
# 后端 http://127.0.0.1:8000  前端 http://localhost:8501
# 停止：Ctrl+C（会同时杀掉两个）

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$ROOT_DIR"

# 探测 Python：找第一个能同时 import fastapi/uvicorn/streamlit 的
find_python() {
    local candidates=(
        "$ROOT_DIR/.venv/Scripts/python.exe"
        "C:/Users/AAA/.workbuddy/binaries/python/envs/default/Scripts/python.exe"
        "D:/Program Files/Python312/python.exe"
        "python"
    )
    for py in "${candidates[@]}"; do
        if [ "$py" = "python" ]; then
            command -v python >/dev/null 2>&1 || continue
        elif [ ! -f "$py" ]; then
            continue
        fi
        if "$py" -c "import fastapi, uvicorn, streamlit" >/dev/null 2>&1; then
            echo "$py"
            return
        fi
    done
    echo "python"
}

PYTHON="$(find_python)"
BACKEND_PORT="${BACKEND_PORT:-8000}"
FRONTEND_PORT="${FRONTEND_PORT:-8501}"

# 依赖校验
if ! "$PYTHON" -c "import fastapi, uvicorn, streamlit" >/dev/null 2>&1; then
    echo "[ERROR] 未找到完整依赖，请先安装："
    echo "  $PYTHON -m pip install fastapi \"uvicorn[standard]\" streamlit"
    exit 1
fi

cleanup() {
    echo ""
    echo "正在停止服务..."
    [ -n "$BACKEND_PID" ] && kill "$BACKEND_PID" 2>/dev/null
    exit 0
}
trap cleanup INT TERM

echo "=========================================="
echo "  IndustryChainExplorer 开发模式"
echo "=========================================="
echo "  Python   : $PYTHON"
echo "  后端地址 : http://127.0.0.1:$BACKEND_PORT"
echo "  后端文档 : http://127.0.0.1:$BACKEND_PORT/docs"
echo "  前端地址 : http://localhost:$FRONTEND_PORT"
echo "  停止     : Ctrl+C"
echo "=========================================="
echo ""

echo "[1/2] 启动后端 (FastAPI)..."
"$PYTHON" -m uvicorn api.app:app --host 127.0.0.1 --port "$BACKEND_PORT" &
BACKEND_PID=$!

sleep 2

echo "[2/2] 启动前端 (Streamlit)..."
"$PYTHON" -m streamlit run ui/streamlit/app.py \
    --server.port "$FRONTEND_PORT" \
    --server.headless true

cleanup
