"""Industry Layer Explorer 测试（Layered Value Chain 分层价值链）。

核心模型是 Layer（层），不是 Tree 也不是 Graph。

验证：
    - Layer/LayerItem/ValueChain 分层模型
    - 5 种产业关系（Upstream/Downstream/Supplies/Uses/Related）
    - Layer View（主视图）：分层价值链
    - Graph View（辅助视图）：关系图
    - 公司独立设计：按 Layer → Item 分组
    - 详情页基于 Layer：所在层、同层条目、上下游层
    - 词典（glossary.yaml）
    - 搜索与标签
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from models import Layer, LayerItem, ValueChain, Relation, RelationType
from repository import ChainRepository, ChainMap, CompanyInfo
from search import Searcher
from services import ExplorerService

CHAINS_DIR = ROOT / "chains"


@pytest.fixture()
def chain_map() -> ChainMap:
    repo = ChainRepository(CHAINS_DIR)
    return repo.load()


@pytest.fixture()
def explorer(chain_map) -> ExplorerService:
    return ExplorerService(chain_map)


# ======================================================================
# Layer 模型
# ======================================================================
def test_layer_item_creation():
    """LayerItem 创建。"""
    item = LayerItem(name="DSP", summary="数字信号处理芯片")
    assert item.name == "DSP"
    assert item.summary == "数字信号处理芯片"
    assert item.tags == []


def test_layer_item_from_string():
    """LayerItem 从字符串构建。"""
    item = LayerItem.from_dict("DSP")
    assert item.name == "DSP"
    assert item.summary == ""


def test_layer_item_from_dict():
    """LayerItem 从 dict 构建。"""
    item = LayerItem.from_dict(
        {"name": "DSP", "summary": "数字信号处理", "tags": ["芯片"]}
    )
    assert item.name == "DSP"
    assert item.summary == "数字信号处理"
    assert item.tags == ["芯片"]


def test_layer_creation():
    """Layer 创建。"""
    layer = Layer(id="component", title="器件层", order=2)
    assert layer.id == "component"
    assert layer.title == "器件层"
    assert layer.order == 2
    assert layer.items == []


def test_layer_has_and_find():
    """Layer 包含与查找。"""
    layer = Layer(
        id="component", title="器件层",
        items=[LayerItem(name="DSP"), LayerItem(name="EML激光器")],
    )
    assert layer.has("DSP")
    assert not layer.has("不存在")
    assert layer.find("DSP") is not None
    assert layer.find("不存在") is None
    assert layer.item_names == ["DSP", "EML激光器"]


def test_layer_from_dict():
    """Layer 从 dict 构建（自动 order）。"""
    data = {
        "id": "application",
        "title": "应用层",
        "items": ["AI服务器", {"name": "交换机"}],
    }
    layer = Layer.from_dict(data, order=0)
    assert layer.id == "application"
    assert layer.title == "应用层"
    assert layer.order == 0
    assert len(layer.items) == 2
    assert layer.items[0].name == "AI服务器"
    assert layer.items[1].name == "交换机"


def test_value_chain_creation():
    """ValueChain 创建。"""
    vc = ValueChain(industry="光模块")
    assert vc.industry == "光模块"
    assert vc.layers == []
    assert vc.layer_count == 0


def test_value_chain_find_item():
    """ValueChain 查找条目所在层。"""
    vc = ValueChain(
        industry="光模块",
        layers=[
            Layer(id="application", title="应用层", order=0,
                  items=[LayerItem(name="AI服务器")]),
            Layer(id="component", title="器件层", order=2,
                  items=[LayerItem(name="DSP")]),
        ],
    )
    found = vc.find_item("DSP")
    assert found is not None
    layer, item = found
    assert layer.id == "component"
    assert item.name == "DSP"
    assert vc.find_item("不存在") is None


def test_value_chain_layer_of():
    """ValueChain 查找条目所在层。"""
    vc = ValueChain(
        industry="光模块",
        layers=[
            Layer(id="application", title="应用层", order=0,
                  items=[LayerItem(name="AI服务器")]),
            Layer(id="component", title="器件层", order=2,
                  items=[LayerItem(name="DSP")]),
        ],
    )
    layer = vc.layer_of("DSP")
    assert layer is not None
    assert layer.id == "component"
    assert vc.layer_of("不存在") is None


def test_value_chain_all_items():
    """ValueChain 所有条目。"""
    vc = ValueChain(
        industry="光模块",
        layers=[
            Layer(id="application", title="应用层", order=0,
                  items=[LayerItem(name="AI服务器"), LayerItem(name="交换机")]),
            Layer(id="component", title="器件层", order=2,
                  items=[LayerItem(name="DSP")]),
        ],
    )
    assert vc.all_items() == ["AI服务器", "交换机", "DSP"]


def test_value_chain_upstream_downstream_layers():
    """ValueChain 上游层/下游层。

    Layer 顺序：Application(0) → System(1) → Component(2) → Material(3)
    上游 = order 更大的层（材料是器件的上游）。
    下游 = order 更小的层（应用是器件的下游）。
    """
    vc = ValueChain(
        industry="光模块",
        layers=[
            Layer(id="application", title="应用层", order=0,
                  items=[LayerItem(name="AI服务器")]),
            Layer(id="system", title="系统层", order=1,
                  items=[LayerItem(name="800G光模块")]),
            Layer(id="component", title="器件层", order=2,
                  items=[LayerItem(name="DSP")]),
            Layer(id="material", title="材料层", order=3,
                  items=[LayerItem(name="硅片")]),
        ],
    )

    # DSP 在器件层（order=2）
    upstream = vc.upstream_layers("DSP")
    assert len(upstream) == 1
    assert upstream[0].id == "material"

    downstream = vc.downstream_layers("DSP")
    assert len(downstream) == 2
    assert downstream[0].id == "application"
    assert downstream[1].id == "system"


def test_value_chain_from_dict():
    """ValueChain 从 dict 构建。"""
    data = {
        "industry": "光模块",
        "layers": [
            {"id": "application", "title": "应用层", "items": ["AI服务器"]},
            {"id": "component", "title": "器件层", "items": [{"name": "DSP"}]},
        ],
    }
    vc = ValueChain.from_dict(data)
    assert vc.industry == "光模块"
    assert vc.layer_count == 2
    assert vc.layers[0].order == 0
    assert vc.layers[1].order == 1
    assert vc.all_items() == ["AI服务器", "DSP"]


# ======================================================================
# 5 种产业关系
# ======================================================================
def test_relation_5_types():
    """5 种产业关系。"""
    types = {r.value for r in RelationType}
    assert types == {
        "Upstream", "Downstream",
        "Supplies", "Uses", "Related",
    }


def test_relation_no_structural_types():
    """移除了 Parent/Child/Contains/Produces 结构关系。"""
    types = {r.value for r in RelationType}
    assert "Parent" not in types
    assert "Child" not in types
    assert "Contains" not in types
    assert "Produces" not in types


def test_relation_reference_is_list():
    """reference 是列表字段（允许多个来源）。"""
    rel = Relation(
        source="DSP", target="光模块",
        relation="Supplies",
        reference=["国盛证券研报", "中际旭创年报"],
    )
    assert isinstance(rel.reference, list)
    assert len(rel.reference) == 2


def test_relation_default_empty_reference():
    """默认 reference 为空列表。"""
    rel = Relation(source="a", target="b", relation="Upstream")
    assert rel.reference == []


def test_relation_label():
    """关系有中文标签。"""
    assert RelationType.UPSTREAM.label == "上游"
    assert RelationType.SUPPLIES.label == "供应"
    assert RelationType.USES.label == "使用"


def test_relation_category():
    """关系分类。"""
    assert RelationType.UPSTREAM.category == "上游关系"
    assert RelationType.SUPPLIES.category == "上游关系"
    assert RelationType.DOWNSTREAM.category == "下游关系"
    assert RelationType.USES.category == "使用关系"
    assert RelationType.RELATED.category == "关联关系"


# ======================================================================
# 数据加载（产业包）
# ======================================================================
def test_repository_loads(chain_map):
    assert len(chain_map.value_chains) > 0
    assert len(chain_map.relations) > 0
    assert len(chain_map.chain_index) > 0


def test_value_chains_loaded(chain_map):
    """分层价值链（layers.yaml）已加载。"""
    assert "optical" in chain_map.value_chains
    vc = chain_map.value_chains["optical"]
    assert vc.industry == "光模块"
    assert vc.layer_count == 4  # Application/System/Component/Material


def test_layers_loaded(chain_map):
    """光模块产业包应有 4 个层。"""
    vc = chain_map.value_chains["optical"]
    layer_ids = [l.id for l in vc.layers]
    assert layer_ids == ["application", "system", "component", "material"]
    # 检查层标题
    for layer in vc.layers:
        assert layer.title


def test_layer_items_loaded(chain_map):
    """层内条目已加载。"""
    vc = chain_map.value_chains["optical"]
    component = vc.find_layer("component")
    assert component is not None
    assert component.has("DSP")
    assert component.has("EML激光器")
    assert component.has("VCSEL")


def test_companies_loaded(chain_map):
    """公司数据（companies.yaml）已加载，按 Layer 分组。"""
    assert "optical" in chain_map.companies
    comp_map = chain_map.companies["optical"]
    # 应有 System 层
    assert "System" in comp_map
    # 800G光模块 应有公司
    assert "800G光模块" in comp_map["System"]
    comps = comp_map["System"]["800G光模块"]
    names = [c.name for c in comps]
    assert "中际旭创" in names


def test_glossary_loaded(chain_map):
    """词典（glossary.yaml）已加载。"""
    assert "optical" in chain_map.glossary
    terms = chain_map.glossary["optical"]
    assert "DSP" in terms
    assert "VCSEL" in terms
    assert "CPO" in terms


def test_chain_index(chain_map):
    """产业包索引：optical 应包含条目。"""
    assert "optical" in chain_map.chain_index
    assert "DSP" in chain_map.chain_index["optical"]
    assert "光模块" not in chain_map.chain_index["optical"]  # 光模块是产业名不是条目


def test_chain_meta(chain_map):
    """产业包元信息（overview.yaml）。"""
    assert "optical" in chain_map.chain_meta
    meta = chain_map.chain_meta["optical"]
    assert meta["name"] == "光模块"
    assert meta["parent"] == "光通信"
    assert "AI" in meta["keywords"]


def test_chain_notes(chain_map):
    """产业包说明（README.md）。"""
    assert "optical" in chain_map.chain_notes
    assert len(chain_map.chain_notes["optical"]) > 0


def test_find_chain_of(chain_map):
    """查找条目所属产业包。"""
    assert chain_map.find_chain_of("DSP") == "optical"
    assert chain_map.find_chain_of("800G光模块") == "optical"
    assert chain_map.find_chain_of("不存在") is None


def test_find_value_chain_of(chain_map):
    """查找条目所属 ValueChain。"""
    vc = chain_map.find_value_chain_of("DSP")
    assert vc is not None
    assert vc.industry == "光模块"


# ======================================================================
# 公司独立设计
# ======================================================================
def test_company_info_creation():
    """CompanyInfo 创建。"""
    comp = CompanyInfo(code="300308", name="中际旭创", summary="光模块龙头")
    assert comp.code == "300308"
    assert comp.name == "中际旭创"
    assert comp.summary == "光模块龙头"


def test_company_info_from_string():
    """CompanyInfo 从字符串构建。"""
    comp = CompanyInfo.from_dict("中际旭创")
    assert comp.name == "中际旭创"
    assert comp.code == ""


def test_company_info_to_dict():
    """CompanyInfo 转 dict。"""
    comp = CompanyInfo(code="300308", name="中际旭创")
    d = comp.to_dict()
    assert d["code"] == "300308"
    assert d["name"] == "中际旭创"


def test_companies_of_item(chain_map):
    """查询某条目的公司。"""
    comps = chain_map.companies_of_item("optical", "800G光模块")
    assert len(comps) > 0
    names = [c.name for c in comps]
    assert "中际旭创" in names


def test_get_company_by_name(chain_map):
    """按名称查找公司。"""
    comp = chain_map.get_company_by_name("中际旭创")
    assert comp is not None
    assert comp.code == "300308"


# ======================================================================
# 词典
# ======================================================================
def test_lookup_term(chain_map):
    """查找名词释义。"""
    text = chain_map.lookup_term("DSP")
    assert text
    assert "数字信号处理" in text


def test_lookup_term_not_found(chain_map):
    """查找不存在的名词。"""
    assert chain_map.lookup_term("不存在的名词XYZ") == ""


def test_get_glossary(chain_map):
    """获取产业包词典。"""
    terms = chain_map.get_glossary("optical")
    assert "DSP" in terms
    assert "VCSEL" in terms


# ======================================================================
# Layer View（主视图）
# ======================================================================
def test_layer_view_all(explorer):
    """分层价值链视图（所有产业包）。"""
    chains = explorer.layer_view()
    assert len(chains) > 0
    optical = next(c for c in chains if c["chain"] == "optical")
    assert optical["industry"] == "光模块"
    assert len(optical["layers"]) == 4


def test_layer_view_single(explorer):
    """分层价值链视图（指定产业包）。"""
    chains = explorer.layer_view("optical")
    assert len(chains) == 1
    assert chains[0]["chain"] == "optical"
    assert chains[0]["industry"] == "光模块"


def test_layer_view_structure(explorer):
    """分层视图结构：layers → items。"""
    chains = explorer.layer_view("optical")
    optical = chains[0]
    for layer in optical["layers"]:
        assert "id" in layer
        assert "title" in layer
        assert "items" in layer
        assert isinstance(layer["items"], list)


def test_layer_view_not_found(explorer):
    """不存在的产业包。"""
    chains = explorer.layer_view("不存在的产业包")
    assert chains == []


# ======================================================================
# 详情页（基于 Layer）
# ======================================================================
def test_detail_item(explorer):
    """条目详情：DSP。"""
    data = explorer.get_detail("DSP")
    assert data is not None
    assert data["name"] == "DSP"
    assert data["chain"] == "optical"
    assert data["industry"] == "光模块"
    # 所在层
    assert data["layer"]["id"] == "component"
    assert data["layer"]["title"] == "器件层"
    # 同层条目
    same_layer_names = [it["name"] for it in data["same_layer_items"]]
    assert "EML激光器" in same_layer_names
    assert "VCSEL" in same_layer_names
    assert "DSP" not in same_layer_names  # 排除自己
    # 上游层（材料层）
    upstream = data["upstream_layers"]
    assert len(upstream) == 1
    assert upstream[0]["id"] == "material"
    # 下游层（应用层 + 系统层）
    downstream = data["downstream_layers"]
    assert len(downstream) == 2
    # 词典
    assert data["glossary"]
    assert "数字信号处理" in data["glossary"]


def test_detail_browsing_mode_no_companies(explorer):
    """浏览模式（默认）：不显示公司。"""
    data = explorer.get_detail("800G光模块")
    assert data is not None
    assert data["show_companies"] is False
    assert data["core_companies"] == []


def test_detail_company_mode_shows_companies(explorer):
    """公司模式：显示公司。"""
    data = explorer.get_detail("800G光模块", show_companies=True)
    assert data is not None
    assert data["show_companies"] is True
    assert len(data["core_companies"]) > 0
    comp_names = [c["name"] for c in data["core_companies"]]
    assert "中际旭创" in comp_names


def test_detail_not_found(explorer):
    assert explorer.get_detail("不存在的节点XYZ") is None


def test_detail_has_layer_fields(explorer):
    """详情页必须有 Layer 相关字段。"""
    data = explorer.get_detail("DSP")
    assert data is not None
    for key in ("layer", "upstream_layers", "downstream_layers", "same_layer_items"):
        assert key in data


def test_detail_references(explorer):
    """详情页应聚合引用来源。"""
    data = explorer.get_detail("光模块")
    # 光模块不是条目，而是产业名 → 应返回 None
    # 改用 DSP
    data = explorer.get_detail("DSP")
    assert data is not None
    refs = data.get("references", [])
    if refs:
        for ref in refs:
            assert "source" in ref
            assert "target" in ref
            assert "relation" in ref


# ======================================================================
# 无限跳转（Wikipedia 式）
# ======================================================================
def test_infinite_navigation(explorer):
    """验证 Wikipedia 式无限跳转：DSP → 同层 → EML激光器。"""
    dsp = explorer.get_detail("DSP")
    assert dsp is not None
    same_layer_names = [it["name"] for it in dsp["same_layer_items"]]
    assert "EML激光器" in same_layer_names

    eml = explorer.get_detail("EML激光器")
    assert eml is not None
    assert eml["layer"]["id"] == "component"


# ======================================================================
# 列表
# ======================================================================
def test_list_chains(explorer):
    chains = explorer.list_chains()
    assert len(chains) > 0
    names = [c["name"] for c in chains]
    assert "optical" in names


def test_list_all_items(explorer):
    items = explorer.list_all_items()
    assert len(items) > 0
    names = [it["name"] for it in items]
    assert "DSP" in names
    assert "800G光模块" in names


def test_list_all_items_structure(explorer):
    """条目结构。"""
    items = explorer.list_all_items()
    for it in items:
        assert "name" in it
        assert "chain" in it
        assert "layer" in it
        assert "layer_id" in it


# ======================================================================
# 搜索
# ======================================================================
def test_search_by_name(chain_map):
    searcher = Searcher(chain_map)
    results = searcher.search("DSP")
    assert len(results) > 0
    names = [r.name for r in results]
    assert "DSP" in names


def test_search_by_prefix(chain_map):
    searcher = Searcher(chain_map)
    results = searcher.search("光")
    assert len(results) > 0
    names = [r.name for r in results]
    # 应找到 800G光模块 / 1.6T光模块 / EML激光器 等
    assert any("光模块" in n for n in names)


def test_search_company(chain_map):
    """搜索公司。"""
    searcher = Searcher(chain_map)
    results = searcher.search("中际旭创")
    assert len(results) > 0
    assert results[0].name == "中际旭创"
    assert results[0].type == "Company"


def test_search_by_code(chain_map):
    """通过股票代码搜索公司。"""
    searcher = Searcher(chain_map)
    results = searcher.search("300308")
    assert len(results) > 0
    assert results[0].name == "中际旭创"


def test_search_empty(chain_map):
    searcher = Searcher(chain_map)
    assert searcher.search("") == []
    assert searcher.search("不存在的关键词XYZ123") == []


# ======================================================================
# 标签系统
# ======================================================================
def test_list_all_tags(explorer):
    tags = explorer.list_all_tags()
    assert len(tags) > 0
    tag_names = [t["name"] for t in tags]
    assert "AI" in tag_names


def test_list_all_tags_simple(explorer):
    tags = explorer.list_all_tags_simple()
    assert "AI" in tags


def test_search_by_tag(explorer):
    results = explorer.search_by_tag("AI")
    assert len(results) > 0
    names = [r["name"] for r in results]
    assert "AI服务器" in names


# ======================================================================
# 词典 API
# ======================================================================
def test_glossary_all(explorer):
    """所有名词解释。"""
    terms = explorer.glossary()
    assert "DSP" in terms
    assert "VCSEL" in terms


def test_glossary_by_chain(explorer):
    """指定产业包名词解释。"""
    terms = explorer.glossary("optical")
    assert "DSP" in terms
    assert "CPO" in terms


# ======================================================================
# Graph View（辅助视图）
# ======================================================================
def test_graph_data_basic(explorer):
    graph = explorer.graph_data("DSP")
    assert graph is not None
    assert graph["center"] == "DSP"
    assert len(graph["nodes"]) > 0
    assert len(graph["edges"]) > 0
    node_ids = [n["id"] for n in graph["nodes"]]
    assert "DSP" in node_ids


def test_graph_data_node_fields(explorer):
    graph = explorer.graph_data("DSP")
    for n in graph["nodes"]:
        assert "id" in n
        assert "label" in n
        assert "type" in n


def test_graph_data_depth(explorer):
    """depth=2 应比 depth=1 节点更多。"""
    g1 = explorer.graph_data("DSP", depth=1)
    g2 = explorer.graph_data("DSP", depth=2)
    assert len(g2["nodes"]) >= len(g1["nodes"])


def test_graph_data_with_companies(explorer):
    """公司模式：关系图应包含公司节点。"""
    g = explorer.graph_data("800G光模块", show_companies=True)
    assert g is not None
    types = [n.get("type") for n in g["nodes"]]
    assert "Company" in types


def test_graph_data_not_found(explorer):
    """不存在的节点。"""
    assert explorer.graph_data("不存在的节点XYZ") is None


# ======================================================================
# 统计
# ======================================================================
def test_stats(explorer):
    stats = explorer.stats()
    assert stats["chains"] > 0
    assert stats["items"] > 0
    assert stats["companies"] > 0
    assert stats["relations"] > 0
    assert stats["glossary_terms"] > 0


def test_hot_industries(explorer):
    industries = explorer.hot_industries(limit=5)
    assert len(industries) > 0


# ======================================================================
# 用户数据存储
# ======================================================================
def test_user_data_favorites(tmp_path):
    from services import UserDataStore
    store = UserDataStore(tmp_path / "user.json")
    store.add_favorite("DSP")
    assert store.is_favorite("DSP")
    assert "DSP" in store.list_favorites()

    store.toggle_favorite("DSP")
    assert not store.is_favorite("DSP")


def test_user_data_notes(tmp_path):
    from services import UserDataStore
    store = UserDataStore(tmp_path / "user.json")
    store.set_note("DSP", "光模块核心芯片")
    assert store.get_note("DSP") == "光模块核心芯片"


def test_user_data_recent(tmp_path):
    from services import UserDataStore
    store = UserDataStore(tmp_path / "user.json")
    store.add_recent("DSP", "DSP", "Item")
    store.add_recent("EML", "EML激光器", "Item")
    recent = store.list_recent()
    assert len(recent) == 2
    assert recent[0]["name"] == "EML激光器"
