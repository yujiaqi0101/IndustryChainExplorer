#!/usr/bin/env bash
# 根目录便捷启动：一键前后端（开发模式）
# 用法: bash dev.sh
set -e
dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec bash "$dir/scripts/dev.sh" "$@"
