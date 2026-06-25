"""Repository：加载所有 Package，构建全局对象索引，跨文件校验。

校验规则（PRD Part 06）：
    1. Object ID 全局唯一（跨包）
    2. Relation.id 全局唯一
    3. Relation.from/to 引用的对象必须存在
    4. Relation.references 引用的对象必须是 kind=reference
    5. Layout.sections[].object_ids 引用的对象必须存在
    6. entity 对象必须有 entity_type
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from ice.models import Object, ObjectKind, Package, Relation
from ice.repository.cache import Cache, package_fingerprint
from ice.repository.loader import PackageLoader


@dataclass
class ValidationResult:
    """校验结果（收集所有错误一次性报告）。"""

    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errors

    def error(self, msg: str) -> None:
        self.errors.append(msg)

    def warning(self, msg: str) -> None:
        self.warnings.append(msg)


class Repository:
    """全局仓库。

    用法：
        repo = Repository(packages_dir)
        result = repo.load()
        if not result.ok:
            for e in result.errors: print(e)
        obj = repo.get_object("dsp")
    """

    def __init__(self, packages_dir: Path, cache_dir: Path | None = None) -> None:
        self.packages_dir = Path(packages_dir)
        self.cache = Cache(cache_dir)
        self.packages: list[Package] = []
        self._object_map: dict[str, Object] = {}
        self._object_pkg: dict[str, str] = {}  # object_id → package dir_name
        self._relations: list[Relation] = []

    # -- 加载 ------------------------------------------------------------
    def load(self) -> ValidationResult:
        """加载所有 Package 并校验。支持缓存命中秒开。"""
        self.packages = []
        self._object_map = {}
        self._object_pkg = {}
        self._relations = []
        result = ValidationResult()

        if not self.packages_dir.exists():
            result.warning(f"packages 目录不存在: {self.packages_dir}")
            return result

        for pkg_dir in sorted(self.packages_dir.iterdir()):
            if not pkg_dir.is_dir():
                continue
            fp = package_fingerprint(pkg_dir)
            cached = self.cache.get(f"pkg_{pkg_dir.name}", fp)
            if cached is not None and isinstance(cached, Package):
                self.packages.append(cached)
                self._index_package(cached, result)
                continue
            try:
                pkg = PackageLoader(pkg_dir).load()
            except Exception as e:
                result.error(f"[{pkg_dir.name}] 加载失败: {e}")
                continue
            self.packages.append(pkg)
            self._index_package(pkg, result)
            self.cache.set(f"pkg_{pkg_dir.name}", fp, pkg)

        self._validate_references(result)
        return result

    def _index_package(self, pkg: Package, result: ValidationResult) -> None:
        for obj in pkg.objects:
            if obj.id in self._object_map:
                prev = self._object_pkg.get(obj.id, "?")
                result.error(f"[{pkg.dir_name}] 对象ID重复: {obj.id}（已在 {prev} 中定义）")
                continue
            self._object_map[obj.id] = obj
            self._object_pkg[obj.id] = pkg.dir_name
        self._relations.extend(pkg.relations)

    def _validate_references(self, result: ValidationResult) -> None:
        # relation.id 唯一
        rel_ids: set[str] = set()
        for r in self._relations:
            if r.id in rel_ids:
                result.error(f"关系ID重复: {r.id}")
            rel_ids.add(r.id)
            # from/to 存在
            if r.from_ not in self._object_map:
                result.error(f"[{r.id}] from 引用的对象不存在: {r.from_}")
            if r.to not in self._object_map:
                result.error(f"[{r.id}] to 引用的对象不存在: {r.to}")
            # references 指向的对象必须是 kind=reference
            for ref_id in r.references:
                ref_obj = self._object_map.get(ref_id)
                if ref_obj is None:
                    result.error(f"[{r.id}] reference 引用的对象不存在: {ref_id}")
                elif ref_obj.kind != ObjectKind.REFERENCE:
                    result.error(
                        f"[{r.id}] reference 引用的对象 {ref_id} 不是 reference 类型（实际为 {ref_obj.kind.value}）"
                    )
        # layout 引用存在
        for pkg in self.packages:
            if pkg.layout is None:
                continue
            for sec in pkg.layout.sections:
                for oid in sec.object_ids:
                    if oid not in self._object_map:
                        result.error(f"[{pkg.dir_name}] layout.{sec.id} 引用的对象不存在: {oid}")
        # entity 必须有 entity_type
        for obj in self._object_map.values():
            if obj.kind == ObjectKind.ENTITY and obj.entity_type is None:
                result.error(f"对象 {obj.id} (entity) 缺少 entity_type")

    # -- 查询 ------------------------------------------------------------
    def get_object(self, object_id: str) -> Object | None:
        return self._object_map.get(object_id)

    def get_package_of(self, object_id: str) -> Package | None:
        name = self._object_pkg.get(object_id)
        if name is None:
            return None
        return next((p for p in self.packages if p.dir_name == name), None)

    def all_objects(self) -> list[Object]:
        return list(self._object_map.values())

    def all_relations(self) -> list[Relation]:
        return list(self._relations)

    def relations_of(self, object_id: str) -> list[Relation]:
        return [r for r in self._relations if r.from_ == object_id or r.to == object_id]

    def stats(self) -> dict[str, Any]:
        kind_count: dict[str, int] = {}
        for o in self._object_map.values():
            kind_count[o.kind.value] = kind_count.get(o.kind.value, 0) + 1
        return {
            "packages": len(self.packages),
            "objects": len(self._object_map),
            "relations": len(self._relations),
            "by_kind": kind_count,
        }
