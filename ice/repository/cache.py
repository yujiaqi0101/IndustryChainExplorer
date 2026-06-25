"""缓存层（PRD Part 06 第十二节）。

按 Package 目录 mtime 判断是否失效，pickle 缓存 Package。
大产业链也能秒开。
"""

from __future__ import annotations

import hashlib
import pickle
from pathlib import Path
from typing import Any


def _dir_fingerprint(dir_path: Path) -> str:
    """目录指纹：所有 yaml/md 文件的路径+mtime 的 hash。"""
    h = hashlib.md5()
    for f in sorted(dir_path.rglob("*")):
        if f.is_file() and f.suffix in (".yaml", ".yml", ".md"):
            rel = f.relative_to(dir_path).as_posix()
            stat = f.stat()
            h.update(f"{rel}:{stat.st_mtime}:{stat.st_size}".encode("utf-8"))
    return h.hexdigest()


class Cache:
    """文件缓存。按 key + fingerprint 失效。"""

    def __init__(self, cache_dir: Path | None = None) -> None:
        self.dir = Path(cache_dir) if cache_dir else None
        if self.dir is not None:
            self.dir.mkdir(parents=True, exist_ok=True)

    def get(self, key: str, fingerprint: str) -> Any | None:
        """命中返回缓存值，不命中返回 None。"""
        if self.dir is None:
            return None
        meta_path = self.dir / f"{key}.meta"
        data_path = self.dir / f"{key}.pkl"
        if not meta_path.exists() or not data_path.exists():
            return None
        try:
            stored_fp = meta_path.read_text(encoding="utf-8").strip()
            if stored_fp != fingerprint:
                return None  # 指纹变化，失效
            with open(data_path, "rb") as f:
                return pickle.load(f)
        except (OSError, pickle.PickleError, EOFError):
            return None

    def set(self, key: str, fingerprint: str, value: Any) -> None:
        """写入缓存。"""
        if self.dir is None:
            return
        try:
            (self.dir / f"{key}.meta").write_text(fingerprint, encoding="utf-8")
            with open(self.dir / f"{key}.pkl", "wb") as f:
                pickle.dump(value, f, protocol=pickle.HIGHEST_PROTOCOL)
        except (OSError, pickle.PickleError):
            pass  # 缓存写入失败不影响主流程


def package_fingerprint(pkg_dir: Path) -> str:
    """单个 Package 的指纹。"""
    return _dir_fingerprint(pkg_dir)
