"""Repository 层单元测试（Loader + Validator）。"""

from __future__ import annotations

from pathlib import Path

import pytest

from ice.repository import PackageLoader, Repository


# ============================================================
# 测试夹具：构造临时 package
# ============================================================
@pytest.fixture()
def tmp_package(tmp_path: Path) -> Path:
    """构造一个最小可用的 packages/ 目录，含一个 optical 包。"""
    pkg = tmp_path / "optical"
    pkg.mkdir()
    (pkg / "package.yaml").write_text(
        "name: 光模块\nindustry: 光模块\nversion: '1.0.0'\n", encoding="utf-8"
    )
    (pkg / "objects").mkdir()
    (pkg / "objects" / "entities.yaml").write_text(
        """\
- id: dsp
  kind: entity
  entity_type: component
  name: DSP
  summary: 数字信号处理芯片。
  created_at: '2026-01-01'
  updated_at: '2026-01-01'
- id: optical_module
  kind: entity
  entity_type: product
  name: 光模块
  created_at: '2026-01-01'
  updated_at: '2026-01-01'
""",
        encoding="utf-8",
    )
    (pkg / "objects" / "references.yaml").write_text(
        """\
- id: gs_report
  kind: reference
  name: 国盛报告
  created_at: '2026-01-01'
  updated_at: '2026-01-01'
""",
        encoding="utf-8",
    )
    (pkg / "relations").mkdir()
    (pkg / "relations" / "supply.yaml").write_text(
        """\
- id: rel_0001
  from: dsp
  to: optical_module
  type: supply
  references:
    - gs_report
  created_at: '2026-01-01'
  updated_at: '2026-01-01'
""",
        encoding="utf-8",
    )
    (pkg / "layout.yaml").write_text(
        """\
sections:
  - id: component
    title: 器件层
    object_ids: [dsp]
    order: 1
  - id: product
    title: 产品层
    object_ids: [optical_module]
    order: 0
""",
        encoding="utf-8",
    )
    return tmp_path


# ============================================================
# PackageLoader
# ============================================================
class TestPackageLoader:
    def test_load_full_package(self, tmp_package: Path):
        pkg = PackageLoader(tmp_package / "optical").load()
        assert pkg.dir_name == "optical"
        assert pkg.name == "光模块"
        assert len(pkg.objects) == 3
        assert len(pkg.relations) == 1
        assert pkg.layout is not None
        assert len(pkg.layout.sections) == 2

    def test_relation_from_to_type(self, tmp_package: Path):
        pkg = PackageLoader(tmp_package / "optical").load()
        r = pkg.relations[0]
        assert r.from_ == "dsp"
        assert r.to == "optical_module"
        assert r.type.value == "supply"
        assert r.references == ["gs_report"]


# ============================================================
# Repository 校验
# ============================================================
class TestRepository:
    def test_valid_load(self, tmp_package: Path):
        repo = Repository(tmp_package)
        result = repo.load()
        assert result.ok, result.errors
        assert len(repo.all_objects()) == 3
        assert len(repo.all_relations()) == 1

    def test_stats(self, tmp_package: Path):
        repo = Repository(tmp_package)
        repo.load()
        s = repo.stats()
        assert s["packages"] == 1
        assert s["objects"] == 3
        assert s["relations"] == 1
        assert s["by_kind"]["entity"] == 2
        assert s["by_kind"]["reference"] == 1

    def test_get_object(self, tmp_package: Path):
        repo = Repository(tmp_package)
        repo.load()
        obj = repo.get_object("dsp")
        assert obj is not None
        assert obj.name == "DSP"
        assert repo.get_object("not_exist") is None

    def test_relations_of(self, tmp_package: Path):
        repo = Repository(tmp_package)
        repo.load()
        rels = repo.relations_of("dsp")
        assert len(rels) == 1
        assert rels[0].from_ == "dsp"

    def test_get_package_of(self, tmp_package: Path):
        repo = Repository(tmp_package)
        repo.load()
        pkg = repo.get_package_of("dsp")
        assert pkg is not None
        assert pkg.dir_name == "optical"

    # -- 校验失败场景 ----------------------------------------------------
    def test_missing_from_object(self, tmp_package: Path):
        # 改坏一条关系的 from
        rel_file = tmp_package / "optical" / "relations" / "supply.yaml"
        rel_file.write_text(
            "- id: rel_0001\n  from: not_exist\n  to: optical_module\n  type: supply\n",
            encoding="utf-8",
        )
        repo = Repository(tmp_package)
        result = repo.load()
        assert not result.ok
        assert any("from" in e and "not_exist" in e for e in result.errors)

    def test_reference_not_reference_kind(self, tmp_package: Path):
        # references 指向 entity 而非 reference
        rel_file = tmp_package / "optical" / "relations" / "supply.yaml"
        rel_file.write_text(
            "- id: rel_0001\n  from: dsp\n  to: optical_module\n  type: supply\n"
            "  references: [dsp]\n",
            encoding="utf-8",
        )
        repo = Repository(tmp_package)
        result = repo.load()
        assert not result.ok
        assert any("不是 reference 类型" in e for e in result.errors)

    def test_entity_missing_entity_type(self, tmp_package: Path):
        ent_file = tmp_package / "optical" / "objects" / "entities.yaml"
        ent_file.write_text(
            "- id: dsp\n  kind: entity\n  name: DSP\n", encoding="utf-8"
        )
        repo = Repository(tmp_package)
        result = repo.load()
        assert not result.ok
        assert any("entity_type" in e for e in result.errors)

    def test_duplicate_object_id(self, tmp_package: Path):
        ent_file = tmp_package / "optical" / "objects" / "entities.yaml"
        ent_file.write_text(
            "- id: dsp\n  kind: entity\n  entity_type: component\n  name: DSP\n"
            "- id: dsp\n  kind: entity\n  entity_type: component\n  name: DSP2\n",
            encoding="utf-8",
        )
        repo = Repository(tmp_package)
        result = repo.load()
        assert not result.ok
        assert any("重复" in e for e in result.errors)

    def test_layout_missing_object(self, tmp_package: Path):
        layout_file = tmp_package / "optical" / "layout.yaml"
        layout_file.write_text(
            "sections:\n  - id: x\n    title: X\n    object_ids: [not_exist]\n    order: 0\n",
            encoding="utf-8",
        )
        repo = Repository(tmp_package)
        result = repo.load()
        assert not result.ok
        assert any("layout" in e for e in result.errors)

    def test_nonexistent_packages_dir(self, tmp_path: Path):
        repo = Repository(tmp_path / "no_such_dir")
        result = repo.load()
        assert result.ok  # 没有错误，只有 warning
        assert len(result.warnings) == 1
