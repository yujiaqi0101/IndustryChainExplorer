#!/usr/bin/env bash
# 根目录便捷启动：前端（Streamlit）
# 用法: bash start_frontend.sh [port]
set -e
dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec bash "$dir/scripts/start_frontend.sh" "$@"
