"""ICE 产业链浏览器入口（薄包装，转发到 ice.cli）。

用法：
    python main.py search dsp
    python main.py show dsp
    python main.py validate
    python main.py stats

完整命令见：python -m ice.cli --help
"""

from __future__ import annotations

from ice.cli import main

if __name__ == "__main__":
    raise SystemExit(main())
