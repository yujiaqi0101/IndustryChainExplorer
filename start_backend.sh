#!/usr/bin/env bash
# 根目录便捷启动：后端（FastAPI）
# 用法: bash start_backend.sh [port]
set -e
dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec bash "$dir/scripts/start_backend.sh" "$@"
