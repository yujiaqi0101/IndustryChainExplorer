"""加载器：从 YAML 加载 Object / Relation / Package（PRD Part 06 第一~九节）。

YAML 结构：
    objects/*.yaml          — list[Object]
    glossary/*.yaml         — list[Object]（kind=glossary）
    relations/*.yaml        — list[Relation]（字段 from/to/type/references）
    package.yaml            — PackageMeta
    layout.yaml             — Layout（sections 列表）
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, ConfigDict, ValidationError

from ice.models import Layout, Object, Package, Relation


# ============================================================
# Object 加载
# ============================================================
class ObjectLoader:
    """加载一个 Package 目录下的所有对象。

    扫描 objects/*.yaml 和 glossary/*.yaml。
    """

    def __init__(self, pkg_dir: Path) -> None:
        self.pkg_dir = Path(pkg_dir)

    def load(self) -> list[Object]:
        objects: list[Object] = []
        # objects/*.yaml
        obj_dir = self.pkg_dir / "objects"
        if obj_dir.is_dir():
            for f in sorted(obj_dir.glob("*.yaml")):
                objects.extend(self._load_file(f))
        # glossary/*.yaml
        glo_dir = self.pkg_dir / "glossary"
        if glo_dir.is_dir():
            for f in sorted(glo_dir.glob("*.yaml")):
                objects.extend(self._load_file(f))
        return objects

    @staticmethod
    def _load_file(path: Path) -> list[Object]:
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        items = _as_list(data, path)
        result: list[Object] = []
        for raw in items:
            if not isinstance(raw, dict):
                raise ValueError(f"{path}: 对象必须是 dict，得到 {type(raw).__name__}")
            try:
                result.append(Object(**raw))
            except ValidationError as e:
                raise ValueError(f"{path}: 对象校验失败\n{e}") from e
        return result


# ============================================================
# Relation 加载
# ============================================================
class RelationLoader:
    """加载一个 Package 目录下的所有关系。

    YAML 结构（Part 06 第七节）：
        - id: rel_0001
          from: dsp
          to: optical_module
          type: supply
          references:
            - gs_optical_2025
    """

    def __init__(self, pkg_dir: Path) -> None:
        self.pkg_dir = Path(pkg_dir)

    def load(self) -> list[Relation]:
        relations: list[Relation] = []
        rel_dir = self.pkg_dir / "relations"
        if not rel_dir.is_dir():
            return relations
        for f in sorted(rel_dir.glob("*.yaml")):
            relations.extend(self._load_file(f))
        return relations

    @staticmethod
    def _load_file(path: Path) -> list[Relation]:
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        if isinstance(data, dict) and "relations" in data:
            items = data["relations"]
        elif isinstance(data, list):
            items = data
        elif data is None:
            items = []
        else:
            raise ValueError(f"{path}: 期望列表或 {{relations: [...]}}，得到 {type(data).__name__}")
        result: list[Relation] = []
        for raw in items:
            if not isinstance(raw, dict):
                raise ValueError(f"{path}: 关系必须是 dict，得到 {type(raw).__name__}")
            try:
                result.append(Relation(**raw))
            except ValidationError as e:
                raise ValueError(f"{path}: 关系校验失败\n{e}") from e
        return result


# ============================================================
# Package 元信息
# ============================================================
class PackageMeta(BaseModel):
    """package.yaml 元信息。"""

    model_config = ConfigDict(extra="forbid")

    name: str
    industry: str = ""
    description: str = ""
    version: str = "1.0.0"
    keywords: list[str] = []


# ============================================================
# Package 加载
# ============================================================
class PackageLoader:
    """加载单个 Package：聚合 objects + relations + layout + 元信息。"""

    def __init__(self, pkg_dir: Path) -> None:
        self.pkg_dir = Path(pkg_dir)

    def load(self) -> Package:
        meta = self._load_meta()
        objects = ObjectLoader(self.pkg_dir).load()
        relations = RelationLoader(self.pkg_dir).load()
        layout = self._load_layout()
        readme = self._load_readme()
        return Package(
            id=self.pkg_dir.name,
            name=meta.name,
            industry=meta.industry,
            description=meta.description,
            version=meta.version,
            keywords=meta.keywords,
            objects=objects,
            relations=relations,
            layout=layout,
            readme=readme,
            dir_name=self.pkg_dir.name,
        )

    def _load_meta(self) -> PackageMeta:
        path = self.pkg_dir / "package.yaml"
        if not path.exists():
            return PackageMeta(name=self.pkg_dir.name)
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        try:
            return PackageMeta(**data)
        except ValidationError as e:
            raise ValueError(f"{path}: package.yaml 校验失败\n{e}") from e

    def _load_layout(self) -> Layout | None:
        path = self.pkg_dir / "layout.yaml"
        if not path.exists():
            return None
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        if not data:
            return None
        # 兼容 {layout: {sections: [...]}} 包装
        if isinstance(data, dict) and "sections" not in data and "layout" in data:
            data = data["layout"]
        try:
            return Layout(**data)
        except ValidationError as e:
            raise ValueError(f"{path}: layout.yaml 校验失败\n{e}") from e

    def _load_readme(self) -> str:
        path = self.pkg_dir / "README.md"
        if path.exists():
            return path.read_text(encoding="utf-8")
        return ""


# ============================================================
# 工具
# ============================================================
def _as_list(data: Any, src: Path) -> list[Any]:
    if data is None:
        return []
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        if "objects" in data and isinstance(data["objects"], list):
            return data["objects"]
    raise ValueError(f"{src}: 期望列表，得到 {type(data).__name__}")
