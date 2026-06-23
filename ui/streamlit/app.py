"""Industry Layer Explorer 产业链浏览器 UI（Layered Value Chain）。

核心模型是 Layer（层），不是 Tree 也不是 Graph。

视图优先级：
    Layer View（默认主视图）- 分层价值链，一眼看清整个产业
    Graph View（辅助视图）- 关系图，可切换

五大模块：
    1. Browse  浏览 - 默认首页，分层价值链（Layer View）
    2. Search  搜索 - 统一搜索，结果作为入口
    3. Graph   图谱 - 独立关系图（Graph View）
    4. Data    数据 - 导入/导出/重建索引
    5. Settings 设置 - 主题/缓存/数据目录

启动：
    streamlit run ui/streamlit/app.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from repository import ChainRepository
from search import Searcher
from services import ExplorerService, UserDataStore

CHAINS_DIR = ROOT / "chains"
USER_DATA_PATH = ROOT / "data" / "user_data.json"
EXPORT_DIR = ROOT / "data" / "exports"


# ======================================================================
# 服务初始化
# ======================================================================
@st.cache_resource
def get_services():
    """初始化数据与服务（带缓存）。"""
    repo = ChainRepository(CHAINS_DIR)
    chain_map = repo.load()
    return {
        "map": chain_map,
        "explorer": ExplorerService(chain_map),
        "searcher": Searcher(chain_map),
        "user_data": UserDataStore(USER_DATA_PATH),
    }


def _reset_cache() -> None:
    """清除 Streamlit 缓存。"""
    st.cache_resource.clear()
    st.session_state.pop("selected_node", None)


# ======================================================================
# 主入口
# ======================================================================
def main() -> None:
    st.set_page_config(
        page_title="Industry Layer Explorer 产业链浏览器",
        page_icon="🗂",
        layout="wide",
    )

    services = get_services()

    # 会话状态初始化
    if "module" not in st.session_state:
        st.session_state.module = "browse"
    if "selected_node" not in st.session_state:
        st.session_state.selected_node = None  # (name,)

    _render_top_nav()

    module = st.session_state.module
    if module == "browse":
        _render_browse(services)
    elif module == "search":
        _render_search(services)
    elif module == "graph":
        _render_graph_module(services)
    elif module == "data":
        _render_data(services)
    elif module == "settings":
        _render_settings(services)


# ======================================================================
# 顶部导航
# ======================================================================
def _render_top_nav() -> None:
    """顶部五模块导航。"""
    col1, col2, col3, col4, col5, col6 = st.columns([2, 1, 1, 1, 1, 1])

    with col1:
        st.markdown("### 🗚 Industry Layer Explorer")

    modules = [
        ("browse", "📁 浏览"),
        ("search", "🔍 搜索"),
        ("graph", "🕸 图谱"),
        ("data", "💾 数据"),
        ("settings", "⚙️ 设置"),
    ]

    for idx, (key, label) in enumerate(modules):
        col = [col2, col3, col4, col5, col6][idx]
        with col:
            if st.button(label, key=f"nav_{key}", use_container_width=True):
                st.session_state.module = key
                st.rerun()


# ======================================================================
# 模块 1：Browse（浏览）- 默认首页，Layer View
# ======================================================================
def _render_browse(services) -> None:
    """浏览模块：分层价值链（Layer View，主视图）。"""
    explorer = services["explorer"]

    # 如果选中了节点，显示详情页
    if st.session_state.selected_node:
        _render_detail_page(services, st.session_state.selected_node)
        return

    # 否则显示分层价值链
    st.markdown("## 📁 分层价值链（Layer View）")
    st.markdown("---")

    chains = explorer.layer_view()
    if not chains:
        st.warning("暂无产业数据")
        return

    for chain_data in chains:
        _render_value_chain(services, chain_data)


def _render_value_chain(services, chain_data: dict) -> None:
    """渲染一个产业包的分层价值链。"""
    industry = chain_data.get("industry", "")
    description = chain_data.get("description", "")
    layers = chain_data.get("layers", [])

    st.markdown(f"### 🏭 {industry}")
    if description:
        st.caption(description)

    # 分层展示
    for layer in layers:
        layer_title = layer.get("title", "")
        items = layer.get("items", [])

        st.markdown(f"**{layer_title}**")
        if not items:
            st.caption("（无）")
            continue

        # 横向排列条目
        cols = st.columns(min(len(items), 4))
        for i, item in enumerate(items):
            with cols[i % len(cols)]:
                name = item.get("name", "")
                summary = item.get("summary", "")
                if st.button(name, key=f"layer_{industry}_{layer_title}_{name}"):
                    st.session_state.selected_node = (name,)
                    st.rerun()
                if summary:
                    st.caption(summary[:30] + "..." if len(summary) > 30 else summary)
        st.markdown("---")


# ======================================================================
# 模块 2：Search（搜索）
# ======================================================================
def _render_search(services) -> None:
    """搜索模块：统一搜索，结果作为入口。"""
    searcher = services["searcher"]

    st.markdown("## 🔍 搜索")
    query = st.text_input(
        "输入条目或公司名称",
        placeholder="例如：光模块、中际旭创、DSP",
        label_visibility="collapsed",
    )

    if not query:
        st.info("请输入搜索关键词")
        return

    results = searcher.search(query)
    if not results:
        st.warning(f"未找到匹配: {query}")
        return

    # 按类型分组
    by_type: dict[str, list] = {}
    for r in results:
        by_type.setdefault(r.type, []).append(r)

    type_icons = {
        "Item": "🔹",
        "Company": "🏢",
    }

    for t, items in by_type.items():
        icon = type_icons.get(t, "🔹")
        st.markdown(f"### {icon} {t}")
        for r in items:
            col1, col2 = st.columns([4, 1])
            with col1:
                if st.button(r.name, key=f"search_{r.id}"):
                    st.session_state.selected_node = (r.name,)
                    st.session_state.module = "browse"
                    st.rerun()
            with col2:
                layer = r.layer if hasattr(r, "layer") else ""
                st.caption(layer)
        st.markdown("---")


# ======================================================================
# 模块 3：Graph（图谱）- 辅助视图
# ======================================================================
def _render_graph_module(services) -> None:
    """图谱模块：独立关系图（Graph View，辅助视图）。"""
    explorer = services["explorer"]

    st.markdown("## 🕸 关系图谱（Graph View - 辅助视图）")

    col1, col2, col3 = st.columns([3, 1, 1])
    with col1:
        all_items = explorer.list_all_items()
        item_names = [n["name"] for n in all_items]
        selected = st.selectbox(
            "选择中心节点",
            options=item_names,
            index=0 if item_names else None,
        )
    with col2:
        depth = st.selectbox("展开深度", [1, 2, 3], index=0)
    with col3:
        show_companies = st.checkbox("🏢 显示公司", value=False)

    if not selected:
        st.info("请选择节点")
        return

    graph = explorer.graph_data(
        selected, depth=depth, show_companies=show_companies
    )
    if not graph:
        st.warning(f"未找到节点: {selected}")
        return

    st.caption(f"节点数: {len(graph['nodes'])}  |  关系数: {len(graph['edges'])}")

    _render_vis_network(graph, services)


def _render_vis_network(graph: dict, services) -> None:
    """使用 vis-network 渲染关系图。"""
    vis_js_path = ROOT / "lib" / "vis-9.1.2" / "vis-network.min.js"
    vis_css_path = ROOT / "lib" / "vis-9.1.2" / "vis-network.css"

    if not vis_js_path.exists():
        st.error("未找到 vis-network 库")
        st.json(graph)
        return

    vis_js = vis_js_path.read_text(encoding="utf-8")
    vis_css = vis_css_path.read_text(encoding="utf-8")

    # 节点颜色映射
    type_colors = {
        "Item": "#3B82F6",
        "Company": "#10B981",
    }

    nodes_js = []
    for n in graph["nodes"]:
        color = type_colors.get(n.get("type", ""), "#9CA3AF")
        nodes_js.append({
            "id": n["id"],
            "label": n["label"],
            "title": n.get("layer", n["label"]),
            "color": {"background": color, "border": color},
            "font": {"color": "white"},
        })

    edges_js = [
        {
            "from": e["from"],
            "to": e["to"],
            "label": e.get("label", ""),
            "arrows": "to",
        }
        for e in graph["edges"]
    ]

    html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>{vis_css}</style>
    <style>
        body {{ margin: 0; padding: 0; }}
        #mynetwork {{
            width: 100%;
            height: 500px;
            border: 1px solid #e5e7eb;
            border-radius: 8px;
        }}
    </style>
    <script>{vis_js}</script>
</head>
<body>
    <div id="mynetwork"></div>
    <script>
        var nodes = new vis.DataSet({json.dumps(nodes_js, ensure_ascii=False)});
        var edges = new vis.DataSet({json.dumps(edges_js, ensure_ascii=False)});
        var container = document.getElementById('mynetwork');
        var data = {{ nodes: nodes, edges: edges }};
        var options = {{
            nodes: {{ shape: 'box', margin: 10, font: {{ size: 14 }} }},
            edges: {{ font: {{ size: 12, align: 'middle' }}, color: '#9CA3AF', smooth: {{ type: 'continuous' }} }},
            physics: {{ stabilization: true, barnesHut: {{ gravitationalConstant: -2000 }} }},
            interaction: {{ hover: true, zoomView: true, dragView: true }}
        }};
        var network = new vis.Network(container, data, options);
    </script>
</body>
</html>
"""
    st.components.v1.html(html, height=520, scrolling=False)

    # 节点列表
    st.markdown("#### 节点列表")
    cols = st.columns(4)
    for i, n in enumerate(graph["nodes"]):
        with cols[i % 4]:
            if st.button(n["label"], key=f"graph_node_{n['id']}"):
                st.session_state.selected_node = (n["label"],)
                st.session_state.module = "browse"
                st.rerun()


# ======================================================================
# 模块 4：Data（数据管理）
# ======================================================================
def _render_data(services) -> None:
    """数据管理模块：导入/导出/重建索引。"""
    explorer = services["explorer"]

    st.markdown("## 💾 数据管理")

    stats = explorer.stats()
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("产业包", stats.get("chains", 0))
    with col2:
        st.metric("条目数", stats.get("items", 0))
    with col3:
        st.metric("公司数", stats.get("companies", 0))
    with col4:
        st.metric("关系数", stats.get("relations", 0))

    st.markdown("---")

    # 导出 JSON
    st.markdown("### 📤 导出数据")
    export_col1, export_col2 = st.columns(2)
    with export_col1:
        if st.button("导出全部条目 JSON", use_container_width=True):
            EXPORT_DIR.mkdir(parents=True, exist_ok=True)
            all_items = explorer.list_all_items()
            export_path = EXPORT_DIR / "items_export.json"
            export_path.write_text(
                json.dumps(all_items, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            st.success(f"已导出 {len(all_items)} 个条目到 {export_path}")
    with export_col2:
        if st.button("导出关系 JSON", use_container_width=True):
            EXPORT_DIR.mkdir(parents=True, exist_ok=True)
            chain_map = services["map"]
            all_relations = [
                {
                    "source": r.source,
                    "target": r.target,
                    "relation": r.relation.value,
                    "description": r.description,
                    "reference": r.reference,
                }
                for r in chain_map.relations
            ]
            export_path = EXPORT_DIR / "relations_export.json"
            export_path.write_text(
                json.dumps(all_relations, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            st.success(f"已导出 {len(all_relations)} 条关系到 {export_path}")

    st.markdown("---")

    # 重建索引
    st.markdown("### 🔄 重建索引")
    if st.button("重新加载数据", use_container_width=True):
        with st.spinner("正在重建索引..."):
            _reset_cache()
            st.success("数据已重新加载，索引已重建")


# ======================================================================
# 模块 5：Settings（设置）
# ======================================================================
def _render_settings(services) -> None:
    """设置模块：主题/缓存/数据目录。"""
    st.markdown("## ⚙️ 设置")

    st.markdown("### 🎨 主题")
    theme = st.selectbox("选择主题", ["浅色（默认）", "深色", "跟随系统"])
    st.info(f"当前主题: {theme}")

    st.markdown("---")

    st.markdown("### 🗑 缓存管理")
    if st.button("清除缓存", use_container_width=True):
        _reset_cache()
        st.success("缓存已清除")

    st.markdown("---")

    st.markdown("### 📂 数据目录")
    st.text(f"产业包目录: {CHAINS_DIR}")
    st.text(f"用户数据文件: {USER_DATA_PATH}")
    st.text(f"导出目录: {EXPORT_DIR}")


# ======================================================================
# 详情页（基于 Layer）
# ======================================================================
def _render_detail_page(services, selected: tuple) -> None:
    """详情页（基于 Layer）。

    展示：所在层、同层条目、上游层、下游层、关联公司（公司模式）。
    """
    explorer = services["explorer"]
    name = selected[0]

    # 返回按钮 + 显示公司开关
    col1, col2, col3 = st.columns([2, 2, 2])
    with col1:
        if st.button("← 返回浏览"):
            st.session_state.selected_node = None
            st.rerun()
    with col3:
        show_companies = st.checkbox(
            "🏢 显示公司",
            value=False,
            help="公司模式：显示核心公司（可折叠）"
        )

    data = explorer.get_detail(name, show_companies=show_companies)
    if data is None:
        st.error(f"未找到: {name}")
        return

    # ------------------------------------------------------------------
    # 标题 + 简介
    # ------------------------------------------------------------------
    layer = data.get("layer", {})
    layer_title = layer.get("title", "")
    st.markdown(f"## 🔹 {data['name']}")
    st.caption(f"所在层: {layer_title}  |  产业: {data.get('industry', '')}")

    if data.get("summary"):
        st.markdown(data["summary"])

    # 词典释义
    glossary = data.get("glossary", "")
    if glossary:
        st.info(f"📖 {glossary}")

    st.markdown("---")

    # ------------------------------------------------------------------
    # 上游层
    # ------------------------------------------------------------------
    upstream_layers = data.get("upstream_layers", [])
    if upstream_layers:
        st.markdown("### ⬆ 上游层")
        for layer in upstream_layers:
            _render_layer_items(services, layer)

    # ------------------------------------------------------------------
    # 同层条目
    # ------------------------------------------------------------------
    same_layer = data.get("same_layer_items", [])
    if same_layer:
        st.markdown(f"### 📦 同层条目（{layer_title}）")
        _render_item_list(services, same_layer)

    # ------------------------------------------------------------------
    # 核心公司（公司模式，可折叠）
    # ------------------------------------------------------------------
    if show_companies:
        core_companies = data.get("core_companies", [])
        if core_companies:
            with st.expander("🏢 核心公司（可折叠）", expanded=True):
                _render_company_list(core_companies)

    # ------------------------------------------------------------------
    # 下游层
    # ------------------------------------------------------------------
    downstream_layers = data.get("downstream_layers", [])
    if downstream_layers:
        st.markdown("### ⬇ 下游层")
        for layer in downstream_layers:
            _render_layer_items(services, layer)

    # ------------------------------------------------------------------
    # 关系图（辅助视图）
    # ------------------------------------------------------------------
    st.markdown("### 🕸 关系图（Graph View）")
    graph = explorer.graph_data(name, depth=1, show_companies=show_companies)
    if graph and graph["nodes"]:
        _render_vis_network(graph, services)
    else:
        st.info("暂无关系图数据")

    # ------------------------------------------------------------------
    # 附加信息
    # ------------------------------------------------------------------
    with st.expander("📎 更多信息"):
        if data.get("tags"):
            st.markdown("**标签:** " + " ".join(f"`{t}`" for t in data["tags"]))

        notes = data.get("notes", "")
        if notes:
            st.markdown("**产业说明:**")
            st.markdown(notes)

        refs = data.get("references", [])
        if refs:
            st.markdown("**引用来源:**")
            for ref in refs:
                st.markdown(f"- {ref['source']} → {ref['target']} ({ref['label']})")
                if ref.get("reference"):
                    st.caption("来源: " + "；".join(ref["reference"]))


def _render_layer_items(services, layer: dict) -> None:
    """渲染一个层的条目。"""
    layer_title = layer.get("title", "")
    items = layer.get("items", [])
    if not items:
        return
    st.markdown(f"**{layer_title}**")
    _render_item_list(services, items)


def _render_item_list(services, items: list) -> None:
    """渲染条目列表。"""
    if not items:
        st.caption("（无）")
        return
    cols = st.columns(min(len(items), 4))
    for i, item in enumerate(items):
        with cols[i % len(cols)]:
            name = item.get("name", "")
            summary = item.get("summary", "")
            if st.button(name, key=f"item_{name}_{i}"):
                st.session_state.selected_node = (name,)
                st.rerun()
            if summary:
                st.caption(summary[:30] + "..." if len(summary) > 30 else summary)


def _render_company_list(companies: list) -> None:
    """渲染公司列表。"""
    if not companies:
        st.caption("（暂无公司）")
        return
    for comp in companies:
        name = comp.get("name", "")
        code = comp.get("code", "")
        summary = comp.get("summary", "")
        st.markdown(f"**{name}** ({code})")
        if summary:
            st.caption(summary)


if __name__ == "__main__":
    main()
