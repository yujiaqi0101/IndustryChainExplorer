from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

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
    page = st.radio(
        "选择页面",
        ["📊 概览", "🔍 搜索", "📦 对象浏览器", "📈 知识图谱", "✅ 验证报告"],
        index=0
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
                    col1, col2 = st.columns([1, 4])
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

                        neighbor_count = len(list(repo.graph.neighbors(obj.id)))
                        with st.expander(f"查看关联关系 ({neighbor_count})"):
                            for nbr, fact, outgoing in repo.graph.neighbors(obj.id):
                                direction = "→" if outgoing else "←"
                                st.write(f"{direction} **{fact.predicate}**: [{nbr.kind.value}] {nbr.name} (`{nbr.id}`)")
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
            st.subheader(f"🔗 关联关系 ({len(repo.graph.neighbors(obj.id))})")

            outgoing = repo.graph.outgoing(obj.id)
            incoming = repo.graph.incoming(obj.id)

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
    st.info("知识图谱可视化功能 - 展示产业链上下游关系")

    entry_points = []
    for pkg in repo.all_packages():
        entry_points.extend(pkg.entry_points)

    start_object = st.selectbox(
        "选择起始节点",
        entry_points + [o.id for o in repo.all_objects() if o.id not in entry_points],
        format_func=lambda x: f"{repo.get_object(x).name} ({x})" if repo.get_object(x) else x
    )

    depth = st.slider("展开深度", 1, 2, 1)

    if start_object:
        obj = repo.get_object(start_object)
        if obj:
            st.subheader(f"从 {obj.name} 开始的关系网络")

            nodes = {start_object: obj}
            edges = []

            current_level = {start_object}
            for level in range(depth):
                next_level = set()
                for oid in current_level:
                    for nbr, fact, outgoing in repo.graph.neighbors(oid):
                        edges.append((oid, nbr.id, fact.predicate, outgoing))
                        if nbr.id not in nodes:
                            nodes[nbr.id] = nbr
                            next_level.add(nbr.id)
                current_level = next_level

            st.write(f"**节点数**: {len(nodes)}, **关系数**: {len(edges)}")

            predicate_filter = st.multiselect(
                "按关系类型筛选",
                list(set(e[2] for e in edges)),
                default=list(set(e[2] for e in edges))
            )

            filtered_edges = [e for e in edges if e[2] in predicate_filter]

            st.subheader("关系列表")
            for src, tgt, pred, outgoing in filtered_edges:
                src_obj = nodes[src]
                tgt_obj = nodes[tgt]
                with st.container(border=True):
                    if outgoing:
                        st.markdown(f"**{src_obj.name}** → *[{pred}]* → **{tgt_obj.name}**")
                    else:
                        st.markdown(f"**{tgt_obj.name}** → *[{pred}]* → **{src_obj.name}**")
                    fact = next((f for n, f, o in repo.graph.neighbors(src) if n.id == tgt and f.predicate == pred), None)
                    if fact and fact.statement:
                        st.caption(fact.statement)

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
