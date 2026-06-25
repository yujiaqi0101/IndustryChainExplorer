#!/usr/bin/env bash
# 后端启动脚本（FastAPI + Uvicorn）
# 用法：bash scripts/start_backend.sh [port]
# 默认端口 8000

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$ROOT_DIR"

# 探测 Python：按候选顺序找第一个能 import fastapi+uvicorn 的
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
            py="python"
        elif [ ! -f "$py" ]; then
            continue
        fi
        # 依赖检查
        if "$py" -c "import fastapi, uvicorn" >/dev/null 2>&1; then
            echo "$py"
            return
        fi
    done
    echo "python"  # 兜底，让报错信息更明确
}

PYTHON="$(find_python)"
PORT="${1:-8000}"
HOST="127.0.0.1"

# 依赖校验
if ! "$PYTHON" -c "import fastapi, uvicorn" >/dev/null 2>&1; then
    echo "[ERROR] 未找到 fastapi/uvicorn，请先安装："
    echo "  $PYTHON -m pip install fastapi \"uvicorn[standard]\" streamlit"
    exit 1
fi

echo "=========================================="
echo "  IndustryChainExplorer 后端启动"
echo "=========================================="
echo "  Python : $PYTHON"
echo "  目录   : $ROOT_DIR"
echo "  地址   : http://$HOST:$PORT"
echo "  文档   : http://$HOST:$PORT/docs"
echo "  停止   : Ctrl+C"
echo "=========================================="

exec "$PYTHON" -m uvicorn api.app:app --reload --host "$HOST" --port "$PORT"
