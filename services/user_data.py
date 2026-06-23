"""用户数据存储（PRD Part 02）。

支持：
    - 收藏（Favorites）
    - 笔记（Notes）
    - 最近浏览（Recent）
    - 知识路径（Knowledge Path）

存储位置：data/user_data.json
设计原则：纯文件驱动，Git 友好，可人工编辑。
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


class UserDataStore:
    """用户数据存储（收藏/笔记/最近浏览/知识路径）。"""

    def __init__(self, data_path: str | Path = "data/user_data.json") -> None:
        self.path = Path(data_path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._data: dict[str, Any] = self._load()

    # -- 加载/保存 --------------------------------------------------------
    def _load(self) -> dict[str, Any]:
        if not self.path.exists():
            return {
                "favorites": [],      # 收藏节点 ID 列表
                "notes": {},          # {node_id: note_text}
                "recent": [],         # 最近浏览 [{id, name, type, ts}]
                "paths": [],         # 知识路径 [{id, name, trail, ts}]
            }
        try:
            with self.path.open("r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            return {"favorites": [], "notes": {}, "recent": [], "paths": []}

    def _save(self) -> None:
        with self.path.open("w", encoding="utf-8") as f:
            json.dump(self._data, f, ensure_ascii=False, indent=2)

    # -- 收藏 -------------------------------------------------------------
    def add_favorite(self, node_id: str) -> None:
        if node_id not in self._data["favorites"]:
            self._data["favorites"].append(node_id)
            self._save()

    def remove_favorite(self, node_id: str) -> None:
        if node_id in self._data["favorites"]:
            self._data["favorites"].remove(node_id)
            self._save()

    def is_favorite(self, node_id: str) -> bool:
        return node_id in self._data["favorites"]

    def list_favorites(self) -> list[str]:
        return list(self._data["favorites"])

    def toggle_favorite(self, node_id: str) -> bool:
        """切换收藏状态，返回当前是否已收藏。"""
        if self.is_favorite(node_id):
            self.remove_favorite(node_id)
            return False
        self.add_favorite(node_id)
        return True

    # -- 笔记 -------------------------------------------------------------
    def get_note(self, node_id: str) -> str:
        return self._data["notes"].get(node_id, "")

    def set_note(self, node_id: str, text: str) -> None:
        text = text.strip()
        if text:
            self._data["notes"][node_id] = text
        else:
            self._data["notes"].pop(node_id, None)
        self._save()

    def list_notes(self) -> dict[str, str]:
        return dict(self._data["notes"])

    # -- 最近浏览 ---------------------------------------------------------
    def add_recent(self, node_id: str, name: str, node_type: str) -> None:
        """记录最近浏览（去重，最新在前）。"""
        recent = self._data["recent"]
        recent = [r for r in recent if r["id"] != node_id]
        recent.insert(0, {
            "id": node_id,
            "name": name,
            "type": node_type,
            "ts": datetime.now().strftime("%Y-%m-%d %H:%M"),
        })
        self._data["recent"] = recent[:50]  # 最多 50 条
        self._save()

    def list_recent(self, limit: int = 20) -> list[dict[str, Any]]:
        return list(self._data["recent"][:limit])

    def clear_recent(self) -> None:
        self._data["recent"] = []
        self._save()

    # -- 知识路径 ---------------------------------------------------------
    def save_path(
        self, name: str, trail: list[dict[str, str]]
    ) -> str:
        """保存知识路径。

        Args:
            name: 路径名称（如 "AI → GPU → 光模块"）
            trail: 路径节点列表 [{id, name, type}]

        Returns:
            path_id
        """
        path_id = f"path_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self._data["paths"].insert(0, {
            "id": path_id,
            "name": name,
            "trail": trail,
            "ts": datetime.now().strftime("%Y-%m-%d %H:%M"),
        })
        self._data["paths"] = self._data["paths"][:100]  # 最多 100 条
        self._save()
        return path_id

    def list_paths(self, limit: int = 20) -> list[dict[str, Any]]:
        return list(self._data["paths"][:limit])

    def get_path(self, path_id: str) -> dict[str, Any] | None:
        for p in self._data["paths"]:
            if p["id"] == path_id:
                return p
        return None

    def delete_path(self, path_id: str) -> None:
        self._data["paths"] = [
            p for p in self._data["paths"] if p["id"] != path_id
        ]
        self._save()

    # -- 全部数据 ---------------------------------------------------------
    def all(self) -> dict[str, Any]:
        return {
            "favorites": list(self._data["favorites"]),
            "notes": dict(self._data["notes"]),
            "recent": list(self._data["recent"]),
            "paths": list(self._data["paths"]),
        }
