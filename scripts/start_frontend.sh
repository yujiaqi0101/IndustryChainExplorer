#!/usr/bin/env bash
# 前端启动脚本（Streamlit）
# 用法：bash scripts/start_frontend.sh [port]
# 默认端口 8501

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$ROOT_DIR"

# 探测 Python：按候选顺序找第一个能 import streamlit 的
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
        if "$py" -c "import streamlit" >/dev/null 2>&1; then
            echo "$py"
            return
        fi
    done
    echo "python"
}

PYTHON="$(find_python)"
PORT="${1:-8501}"

# 依赖校验
if ! "$PYTHON" -c "import streamlit" >/dev/null 2>&1; then
    echo "[ERROR] 未找到 streamlit，请先安装："
    echo "  $PYTHON -m pip install streamlit"
    exit 1
fi

echo "=========================================="
echo "  IndustryChainExplorer 前端启动"
echo "=========================================="
echo "  Python : $PYTHON"
echo "  目录   : $ROOT_DIR"
echo "  地址   : http://localhost:$PORT"
echo "  停止   : Ctrl+C"
echo "=========================================="

exec "$PYTHON" -m streamlit run ui/streamlit/app.py \
    --server.port "$PORT" \
    --server.headless true
