"""Domain 模型单元测试（ice.models）。"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from ice.models import (
    EntityType,
    Layout,
    Object,
    ObjectKind,
    Package,
    Relation,
    RelationType,
    Section,
    validate_object_id,
)


# ============================================================
# Object ID 校验
# ============================================================
class TestObjectId:
    def test_valid_id(self):
        assert validate_object_id("dsp") == "dsp"
        assert validate_object_id("optical_module") == "optical_module"
        assert validate_object_id("ai_server_800g") == "ai_server_800g"

    @pytest.mark.parametrize("bad", ["DSP", "Dsp", "digital signal processor", "中文", "1abc", "dsp-", ""])
    def test_invalid_id(self, bad):
        with pytest.raises(ValueError):
            validate_object_id(bad)

    def test_object_rejects_invalid_id(self):
        with pytest.raises(ValidationError):
            Object(id="DSP", kind="entity", name="DSP")


# ============================================================
# ObjectKind 6 种
# ============================================================
class TestObjectKind:
    def test_six_kinds(self):
        assert len(ObjectKind) == 6
        values = {k.value for k in ObjectKind}
        assert values == {"entity", "company", "glossary", "reference", "organization", "standard"}

    def test_organization_kind_exists(self):
        obj = Object(id="oif", kind="organization", name="OIF")
        assert obj.kind == ObjectKind.ORGANIZATION
        assert obj.kind_label() == "机构"


# ============================================================
# EntityType 6 种
# ============================================================
class TestEntityType:
    def test_six_types(self):
        assert len(EntityType) == 6
        values = {t.value for t in EntityType}
        assert values == {"industry", "product", "component", "material", "technology", "application"}


# ============================================================
# Object 基础
# ============================================================
class TestObject:
    def test_minimal_entity(self):
        obj = Object(id="dsp", kind="entity", entity_type="component", name="DSP")
        assert obj.id == "dsp"
        assert obj.kind == ObjectKind.ENTITY
        assert obj.entity_type == EntityType.COMPONENT
        assert obj.aliases == []
        assert obj.tags == []

    def test_no_metadata_field(self):
        """Part 06 未定义 metadata，必须不存在。"""
        obj = Object(id="dsp", kind="entity", entity_type="component", name="DSP")
        assert not hasattr(obj, "metadata")

    def test_extra_field_forbidden(self):
        with pytest.raises(ValidationError):
            Object(id="dsp", kind="entity", entity_type="component", name="DSP", metadata={"k": "v"})

    def test_company_optional_fields(self):
        obj = Object(id="marvell", kind="company", name="Marvell", code="MRVL", market="US")
        assert obj.code == "MRVL"
        assert obj.market == "US"

    def test_reference_optional_fields(self):
        obj = Object(
            id="gs_optical_2025", kind="reference", name="报告",
            title="深度报告", author="国盛", published_date="2025",
        )
        assert obj.title == "深度报告"
        assert obj.is_reference()

    def test_kind_label(self):
        assert Object(id="x", kind="entity", entity_type="product", name="X").kind_label() == "实体"
        assert Object(id="x", kind="glossary", name="X").kind_label() == "术语"


# ============================================================
# RelationType 10 种
# ============================================================
class TestRelationType:
    def test_ten_types(self):
        assert len(RelationType) == 10
        values = {t.value for t in RelationType}
        assert values == {
            "supply", "use", "produce", "integrate", "replace",
            "compete", "belong_to", "related_to", "standardize", "research",
        }

    def test_no_related_value(self):
        """旧版 related 已改为 related_to。"""
        with pytest.raises(ValueError):
            RelationType("related")

    def test_new_types_exist(self):
        assert RelationType("belong_to") == RelationType.BELONG_TO
        assert RelationType("standardize") == RelationType.STANDARDIZE
        assert RelationType("research") == RelationType.RESEARCH


# ============================================================
# Relation 字段 from_/to/type/references
# ============================================================
class TestRelation:
    def test_from_alias(self):
        """YAML 字段 from 映射到属性 from_。"""
        r = Relation(id="rel_0001", **{"from": "dsp", "to": "optical_module", "type": "supply"})
        assert r.from_ == "dsp"
        assert r.to == "optical_module"
        assert r.type == RelationType.SUPPLY

    def test_populate_by_name(self):
        """也允许用 from_ 构造。"""
        r = Relation(id="rel_0001", from_="dsp", to="optical_module", type="supply")
        assert r.from_ == "dsp"

    def test_references_is_id_list(self):
        """references 是 id 列表，非 Citation 对象。"""
        r = Relation(
            id="rel_0001", **{"from": "dsp", "to": "optical_module", "type": "supply"},
            references=["gs_optical_2025", "zjxc_2024_annual"],
        )
        assert r.references == ["gs_optical_2025", "zjxc_2024_annual"]
        assert all(isinstance(x, str) for x in r.references)

    def test_no_citations_field(self):
        r = Relation(id="rel_0001", **{"from": "dsp", "to": "optical_module", "type": "supply"})
        assert not hasattr(r, "citations")

    def test_citations_forbidden(self):
        with pytest.raises(ValidationError):
            Relation(
                id="rel_0001", **{"from": "dsp", "to": "optical_module", "type": "supply"},
                citations=[{"reference_id": "x"}],
            )

    def test_endpoint_id_validation(self):
        with pytest.raises(ValidationError):
            Relation(id="rel_0001", **{"from": "DSP", "to": "optical_module", "type": "supply"})

    def test_label(self):
        r = Relation(id="rel_0001", **{"from": "dsp", "to": "optical_module", "type": "supply"})
        assert r.label() == "供应"

    def test_serialize_uses_alias(self):
        """序列化时 from_ 应输出为 from。"""
        r = Relation(id="rel_0001", **{"from": "dsp", "to": "optical_module", "type": "supply"})
        dumped = r.model_dump(by_alias=True)
        assert "from" in dumped
        assert dumped["from"] == "dsp"
        assert dumped["type"] == "supply"


# ============================================================
# Layout + Section
# ============================================================
class TestLayout:
    def test_section_of(self):
        layout = Layout(sections=[
            Section(id="app", title="应用层", object_ids=["ai_server", "switch"], order=0),
            Section(id="comp", title="器件层", object_ids=["dsp"], order=2),
        ])
        sec = layout.section_of("dsp")
        assert sec is not None
        assert sec.id == "comp"
        assert layout.section_of("not_exist") is None

    def test_ordered_sections(self):
        layout = Layout(sections=[
            Section(id="comp", title="器件层", order=2),
            Section(id="app", title="应用层", order=0),
        ])
        ordered = layout.ordered_sections()
        assert ordered[0].id == "app"
        assert ordered[1].id == "comp"


# ============================================================
# Package
# ============================================================
class TestPackage:
    def test_relations_of(self):
        pkg = Package(
            id="optical", name="光模块",
            objects=[Object(id="dsp", kind="entity", entity_type="component", name="DSP")],
            relations=[
                Relation(id="r1", **{"from": "dsp", "to": "optical_module", "type": "supply"}),
                Relation(id="r2", **{"from": "marvell", "to": "dsp", "type": "produce"}),
            ],
        )
        rels = pkg.relations_of("dsp")
        assert len(rels) == 2
