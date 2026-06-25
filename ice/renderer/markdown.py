"""Markdown 渲染器：对象详情、搜索结果。

适配 Part 06：移除 metadata 段，references 替代 citations。
"""

from __future__ import annotations

from typing import Any


def render_object_detail(data: dict[str, Any]) -> str:
    """渲染对象详情为 Markdown。"""
    lines: list[str] = []
    lines.append(f"# {data['name']}")
    lines.append("")
    lines.append(f"**ID**: `{data['id']}`  ")
    kind_label = data.get("kind_label", data["kind"])
    lines.append(f"**类型**: {kind_label}")
    if data.get("entity_type_label"):
        lines.append(f" / {data['entity_type_label']}")
    lines.append("")
    if data.get("section"):
        lines.append(f"**所在层**: {data['section']['title']} (`{data['section']['id']}`)  ")
    if data.get("package"):
        lines.append(f"**产业包**: `{data['package']}` ({data.get('industry', '')})")
        lines.append("")
    if data.get("aliases"):
        lines.append(f"**别名**: {', '.join(data['aliases'])}")
        lines.append("")
    if data.get("summary"):
        lines.append(f"**简介**: {data['summary']}")
        lines.append("")
    if data.get("tags"):
        lines.append(f"**标签**: {', '.join(data['tags'])}")
        lines.append("")
    if data.get("code"):
        lines.append(f"**代码**: {data['code']}  **市场**: {data.get('market', '')}")
        lines.append("")
    # 上下游摘要
    up = data.get("upstream", [])
    down = data.get("downstream", [])
    lines.append(f"**上下游**: 上游 {len(up)} 个 / 下游 {len(down)} 个 / 关系 {data.get('relation_count', 0)} 条")
    lines.append("")
    if up:
        lines.append("## 上游")
        for u in up:
            refs = u.get("references", [])
            ref_tag = f"  refs={len(refs)}" if refs else ""
            lines.append(f"- {u['name']} (`{u['object_id']}`) — {u['relation_label']}{ref_tag}")
        lines.append("")
    if down:
        lines.append("## 下游")
        for d in down:
            refs = d.get("references", [])
            ref_tag = f"  refs={len(refs)}" if refs else ""
            lines.append(f"- {d['name']} (`{d['object_id']}`) — {d['relation_label']}{ref_tag}")
        lines.append("")
    return "\n".join(lines)


def render_search_results(results: list[dict[str, Any]], keyword: str) -> str:
    """渲染搜索结果为 Markdown。"""
    if not results:
        return f"未找到匹配: {keyword}"
    lines = [f"# 搜索 \"{keyword}\" — {len(results)} 个结果", ""]
    lines.append("| 对象 | 类型 | ID | 命中 | 分数 |")
    lines.append("|------|------|----|------|------|")
    for r in results:
        lines.append(
            f"| {r['name']} | {r['kind']} | `{r['object_id']}` | {r['matched']} | {r['score']} |"
        )
    return "\n".join(lines)
