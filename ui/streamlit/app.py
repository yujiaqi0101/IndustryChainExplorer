from __future__ import annotations

import json
import sys
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ice.repository import KnowledgeRepository

st.set_page_config(
    page_title="Industry Knowledge OS",
    page_icon="🔗",
    layout="wide",
    initial_sidebar_state="expanded",
)


KIND_COLORS = {
    "concept": "#3b82f6",
    "organization": "#10b981",
    "document": "#f59e0b",
}

KIND_EMOJIS = {
    "concept": "💡",
    "organization": "🏢",
    "document": "📄",
}


def render_echarts_graph(nodes: dict, edges: list, center_id: str | None = None, height: int = 600) -> str | None:
    if not nodes:
        return None

    echarts_nodes = []
    node_id_map = {}
    for idx, (oid, obj) in enumerate(nodes.items()):
        node_id_map[oid] = idx
        size = 40 if oid == center_id else 25
        color = KIND_COLORS.get(obj.kind.value, "#6b7280")
        symbol_size = size
        echarts_nodes.append({
            "id": idx,
            "name": obj.name,
            "value": oid,
            "symbolSize": symbol_size,
            "itemStyle": {
                "color": color,
                "borderColor": "#fff",
                "borderWidth": 2,
            },
            "label": {
                "show": True,
                "position": "bottom",
                "fontSize": 11 if oid == center_id else 10,
                "fontWeight": "bold" if oid == center_id else "normal",
                "color": "#1f2937",
            },
            "emphasis": {
                "scale": True,
                "itemStyle": {
                    "shadowBlur": 10,
                    "shadowColor": "rgba(0,0,0,0.3)",
                },
                "label": {
                    "fontSize": 13,
                    "fontWeight": "bold",
                },
            },
            "tooltip": {
                "show": True,
                "formatter": f"{KIND_EMOJIS.get(obj.kind.value, '')} {obj.name}<br/>ID: {oid}<br/>类型: {obj.kind.value}",
            },
        })

    echarts_links = []
    seen_edges = set()
    for src, tgt, pred, outgoing in edges:
        if src not in node_id_map or tgt not in node_id_map:
            continue
        edge_key = (src, tgt, pred) if outgoing else (tgt, src, pred)
        if edge_key in seen_edges:
            continue
        seen_edges.add(edge_key)
        source_idx = node_id_map[src]
        target_idx = node_id_map[tgt]
        if not outgoing:
            source_idx, target_idx = target_idx, source_idx
        echarts_links.append({
            "source": source_idx,
            "target": target_idx,
            "label": {
                "show": True,
                "formatter": pred,
                "fontSize": 9,
                "color": "#6b7280",
            },
            "lineStyle": {
                "color": "#94a3b8",
                "width": 1.5,
                "curveness": 0.1,
                "opacity": 0.7,
            },
            "symbol": ["none", "arrow"],
            "symbolSize": [0, 8],
            "emphasis": {
                "lineStyle": {
                    "width": 3,
                    "color": "#3b82f6",
                    "opacity": 1,
                },
                "label": {
                    "fontSize": 11,
                    "fontWeight": "bold",
                    "color": "#1e40af",
                },
            },
        })

    initial_zoom = 1.0
    if len(nodes) > 30:
        initial_zoom = 0.7
    elif len(nodes) > 15:
        initial_zoom = 0.85

    graph_data = json.dumps({"nodes": echarts_nodes, "links": echarts_links})

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <script src="https://cdn.jsdelivr.net/npm/echarts@5.4.3/dist/echarts.min.js"></script>
        <style>
            body {{ margin: 0; padding: 0; background: transparent; }}
            #graph-container {{ width: 100%; height: {height}px; }}
        </style>
    </head>
    <body>
        <div id="graph-container"></div>
        <script>
            var chart = echarts.init(document.getElementById('graph-container'), null, {{renderer: 'canvas'}});
            var data = {graph_data};

            var option = {{
                tooltip: {{
                    trigger: 'item',
                    backgroundColor: 'rgba(255,255,255,0.95)',
                    borderColor: '#e5e7eb',
                    borderWidth: 1,
                    textStyle: {{ color: '#1f2937' }},
                }},
                series: [
                    {{
                        type: 'graph',
                        layout: 'force',
                        data: data.nodes,
                        links: data.links,
                        roam: true,
                        zoom: {initial_zoom},
                        draggable: true,
                        force: {{
                            repulsion: 350,
                            gravity: 0.08,
                            edgeLength: [100, 250],
                            friction: 0.6,
                        }},
                        edgeSymbol: ['none', 'arrow'],
                        edgeSymbolSize: [0, 8],
                        edgeLabel: {{
                            fontSize: 9,
                            color: '#6b7280',
                        }},
                        lineStyle: {{
                            opacity: 0.7,
                            width: 1.5,
                            curveness: 0.1,
                        }},
                        emphasis: {{
                            focus: 'adjacency',
                            lineStyle: {{ width: 3 }},
                        }},
                        legend: {{
                            show: false,
                        }},
                    }}
                ]
            }};

            chart.setOption(option);

            window.addEventListener('resize', function() {{
                chart.resize();
            }});

            chart.on('click', function(params) {{
                if (params.dataType === 'node') {{
                    window.parent.postMessage({{
                        type: 'nodeClick',
                        nodeId: params.data.value,
                        nodeName: params.data.name
                    }}, '*');
                }}
            }});
        </script>
    </body>
    </html>
    """
    return html


def build_subgraph(repo, center_id: str, depth: int = 1, predicate_filter: list[str] | None = None):
    nodes = {}
    edges = []

    center_obj = repo.get_object(center_id)
    if not center_obj:
        return nodes, edges

    nodes[center_id] = center_obj

    current_level = {center_id}
    visited = {center_id}

    for _ in range(depth):
        next_level = set()
        for oid in current_level:
            for nbr, fact, outgoing in repo.graph.neighbors(oid):
                if predicate_filter and fact.predicate not in predicate_filter:
                    continue
                edges.append((oid, nbr.id, fact.predicate, outgoing))
                if nbr.id not in visited:
                    nodes[nbr.id] = nbr
                    visited.add(nbr.id)
                    next_level.add(nbr.id)
        current_level = next_level

    return nodes, edges


@st.cache_resource
def load_repo():
    repo = KnowledgeRepository(ROOT)
    report = repo.load(strict=False)
    return repo, report


repo, report = load_repo()

st.title("🔗 Industry Knowledge OS")
st.caption("产业知识操作系统 v2.0 - 知识中心架构")

with st.sidebar:
    st.header("导航")

    pages = ["📊 概览", "🔍 搜索", "📦 对象浏览器", "📈 知识图谱", "✅ 验证报告"]
    default_index = 0
    if "page" in st.session_state:
        target_page = st.session_state["page"]
        if target_page in pages:
            default_index = pages.index(target_page)
            del st.session_state["page"]

    page = st.radio(
        "选择页面",
        pages,
        index=default_index
    )

    st.divider()
    stats = repo.stats()
    st.metric("对象数量", stats["objects_parsed"])
    st.metric("事实数量", stats["facts_parsed"])
    st.metric("产业包", stats["package_count"])
    st.metric("质量评分", f"{report.quality_score()}/100")

if page == "📊 概览":
    st.header("📊 知识库概览")

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("概念 (Concept)", len([o for o in repo.all_objects() if o.kind.value == "concept"]))
    with col2:
        st.metric("组织 (Organization)", len([o for o in repo.all_objects() if o.kind.value == "organization"]))
    with col3:
        st.metric("文档 (Document)", len([o for o in repo.all_objects() if o.kind.value == "document"]))
    with col4:
        st.metric("语义关系", stats["facts_parsed"])

    st.divider()

    st.subheader("产业包")
    for pkg in repo.all_packages():
        with st.expander(f"📦 {pkg.name} (v{pkg.version})"):
            st.write(f"**ID**: {pkg.id}")
            st.write(f"**描述**: {pkg.description}")
            st.write(f"**入口点**: {', '.join(pkg.entry_points)}")
            st.write("**分层结构**:")
            for layer in sorted(pkg.layers, key=lambda l: l.order):
                st.write(f"  - L{layer.order} {layer.name} ({layer.id})")

elif page == "🔍 搜索":
    st.header("🔍 知识搜索")
    query = st.text_input("输入关键词搜索", placeholder="例如：光模块, 中际旭创, DSP")

    if query:
        results = repo.search(query)
        if results:
            st.success(f"找到 {len(results)} 个结果")
            for obj in results:
                with st.container(border=True):
                    col1, col2, col3 = st.columns([1, 5, 1])
                    with col1:
                        kind_emoji = {"concept": "💡", "organization": "🏢", "document": "📄"}.get(obj.kind.value, "❓")
                        st.write(f"{kind_emoji} **{obj.kind.value}**")
                    with col2:
                        st.markdown(f"### [{obj.id}] {obj.name}")
                        if obj.summary:
                            st.write(obj.summary)
                        if obj.aliases:
                            st.caption(f"别名: {', '.join(obj.aliases)}")
                        if obj.tags:
                            st.caption(f"标签: {', '.join(obj.tags)}")
                    with col3:
                        neighbor_count = len(list(repo.graph.neighbors(obj.id)))
                        st.metric("关系数", neighbor_count)
                        if st.button("📈 图谱", key=f"graph_{obj.id}", use_container_width=True):
                            st.session_state["jump_to_graph"] = obj.id
                            st.session_state["page"] = "📈 知识图谱"
                            st.rerun()

                        with st.expander(f"查看关系 ({neighbor_count})"):
                            for nbr, fact, outgoing in repo.graph.neighbors(obj.id):
                                direction = "→" if outgoing else "←"
                                st.write(f"{direction} **{fact.predicate}**: [{nbr.kind.value}] {nbr.name}")
                                st.caption(fact.statement)
        else:
            st.warning("未找到相关结果")

elif page == "📦 对象浏览器":
    st.header("📦 对象浏览器")

    kind_filter = st.multiselect(
        "按类型筛选",
        ["concept", "organization", "document"],
        default=["concept", "organization", "document"],
        format_func=lambda x: {"concept": "💡 概念", "organization": "🏢 组织", "document": "📄 文档"}[x]
    )

    objects = [o for o in repo.all_objects() if o.kind.value in kind_filter]

    object_options = {f"[{o.kind.value}] {o.name} ({o.id})": o.id for o in sorted(objects, key=lambda x: x.name)}
    selected_id = st.selectbox("选择对象", list(object_options.keys()))

    if selected_id:
        obj_id = object_options[selected_id]
        obj = repo.get_object(obj_id)

        if obj:
            st.divider()
            kind_emoji = {"concept": "💡", "organization": "🏢", "document": "📄"}.get(obj.kind.value, "❓")
            st.subheader(f"{kind_emoji} {obj.name}")

            col1, col2 = st.columns(2)
            with col1:
                st.write(f"**ID**: `{obj.id}`")
                st.write(f"**类型**: {obj.kind.value}")
                if obj.aliases:
                    st.write(f"**别名**: {', '.join(obj.aliases)}")
            with col2:
                if obj.tags:
                    st.write(f"**标签**: {', '.join(obj.tags)}")
                if obj.deprecated_ids:
                    st.write(f"**废弃ID**: {', '.join(obj.deprecated_ids)}")

            if obj.summary:
                st.markdown("---")
                st.write(f"**摘要**: {obj.summary}")

            st.markdown("---")
            neighbor_count = len(list(repo.graph.neighbors(obj.id)))
            st.subheader(f"🔗 关联关系图谱 ({neighbor_count})")
            st.caption("以当前对象为中心的关系网络 - 滚轮缩放，拖拽节点")

            obj_nodes, obj_edges = build_subgraph(repo, obj.id, depth=1)

            if obj_nodes and len(obj_nodes) > 1:
                obj_graph_html = render_echarts_graph(obj_nodes, obj_edges, center_id=obj.id, height=450)
                if obj_graph_html:
                    components.html(obj_graph_html, height=470, scrolling=False)
            else:
                st.info("该对象暂无关联关系")

            with st.expander("查看关系详情列表"):
                outgoing = list(repo.graph.outgoing(obj.id))
                incoming = list(repo.graph.incoming(obj.id))

                if outgoing:
                    st.write("**出向关系 (→)**:")
                    for nbr, fact in outgoing:
                        with st.container(border=True):
                            st.markdown(f"**[{fact.predicate}]** → [{nbr.id}] {nbr.name} `{nbr.kind.value}`")
                            if fact.statement:
                                st.caption(fact.statement)

                if incoming:
                    st.write("**入向关系 (←)**:")
                    for nbr, fact in incoming:
                        with st.container(border=True):
                            st.markdown(f"[{nbr.id}] {nbr.name} `{nbr.kind.value}` → **[{fact.predicate}]**")
                            if fact.statement:
                                st.caption(fact.statement)

elif page == "📈 知识图谱":
    st.header("📈 知识图谱")
    st.caption("力导向关系图可视化 - 支持缩放、平移、拖拽节点、点击查看详情")

    entry_points = []
    for pkg in repo.all_packages():
        entry_points.extend(pkg.entry_points)
    all_object_ids = entry_points + [o.id for o in repo.all_objects() if o.id not in entry_points]

    default_start_idx = 0
    if "jump_to_graph" in st.session_state:
        target_id = st.session_state["jump_to_graph"]
        if target_id in all_object_ids:
            default_start_idx = all_object_ids.index(target_id)
        del st.session_state["jump_to_graph"]

    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        start_object = st.selectbox(
            "选择起始节点",
            all_object_ids,
            index=default_start_idx,
            format_func=lambda x: f"{repo.get_object(x).name} ({x})" if repo.get_object(x) else x
        )
    with col2:
        depth = st.slider("展开深度", 1, 3, 1)
    with col3:
        st.caption("💡 操作提示")
        st.caption("滚轮缩放 · 拖拽平移 · 点击节点")

    if start_object:
        obj = repo.get_object(start_object)
        if obj:
            nodes, edges = build_subgraph(repo, start_object, depth=depth)

            if edges:
                all_predicates = list(set(e[2] for e in edges))
                predicate_filter = st.multiselect(
                    "按关系类型筛选",
                    all_predicates,
                    default=all_predicates
                )
                nodes, edges = build_subgraph(repo, start_object, depth=depth, predicate_filter=predicate_filter)

            col_a, col_b, col_c, col_d = st.columns(4)
            with col_a:
                st.metric("中心节点", obj.name)
            with col_b:
                st.metric("节点总数", len(nodes))
            with col_c:
                st.metric("关系总数", len(edges))
            with col_d:
                center_kind = obj.kind.value
                st.metric("节点类型", f"{KIND_EMOJIS.get(center_kind, '')} {center_kind}")

            graph_html = render_echarts_graph(nodes, edges, center_id=start_object, height=650)
            if graph_html:
                components.html(graph_html, height=670, scrolling=False)

            st.divider()
            st.subheader("节点图例")
            leg1, leg2, leg3 = st.columns(3)
            with leg1:
                st.markdown(f"<span style='display:inline-block;width:14px;height:14px;background:{KIND_COLORS['concept']};border-radius:50%;margin-right:6px;vertical-align:middle;'></span> 💡 概念 (Concept) - 技术、产品、材料、应用等", unsafe_allow_html=True)
            with leg2:
                st.markdown(f"<span style='display:inline-block;width:14px;height:14px;background:{KIND_COLORS['organization']};border-radius:50%;margin-right:6px;vertical-align:middle;'></span> 🏢 组织 (Organization) - 企业、机构等", unsafe_allow_html=True)
            with leg3:
                st.markdown(f"<span style='display:inline-block;width:14px;height:14px;background:{KIND_COLORS['document']};border-radius:50%;margin-right:6px;vertical-align:middle;'></span> 📄 文档 (Document) - 报告、文献等", unsafe_allow_html=True)

elif page == "✅ 验证报告":
    st.header("✅ 知识库验证报告")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("错误 ❌", report.error_count(), delta_color="inverse")
    with col2:
        st.metric("警告 ⚠️", report.warning_count(), delta_color="inverse")
    with col3:
        st.metric("质量评分", f"{report.quality_score()}/100")

    st.divider()

    errors = report.errors()
    warnings = report.warnings()
    infos = report.infos()

    if errors:
        st.subheader("❌ 错误")
        for issue in errors:
            st.error(str(issue))

    if warnings:
        st.subheader("⚠️ 警告")
        for issue in warnings:
            st.warning(str(issue))

    if infos:
        st.subheader("ℹ️ 信息")
        for issue in infos:
            st.info(str(issue))

    if not errors and not warnings and not infos:
        st.success("🎉 知识库验证通过，没有问题！")

st.divider()
st.caption(f"Industry Knowledge OS v2.0 | Pipeline加载完成 | 0错误 | {repo.timings()}")
