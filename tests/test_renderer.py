"""Renderer 单元测试。"""

from __future__ import annotations

from ice.renderer import render_object_detail, render_search_results


class TestRenderObjectDetail:
    def test_basic_render(self):
        data = {
            "id": "dsp", "kind": "entity", "kind_label": "实体",
            "entity_type_label": "器件", "name": "DSP",
            "aliases": ["Digital Signal Processor"],
            "summary": "数字信号处理芯片",
            "tags": ["芯片", "上游"],
            "code": "300308", "market": "SZ",
            "package": "optical", "industry": "光模块",
            "section": {"id": "component", "title": "器件层", "order": 2},
            "upstream": [
                {"object_id": "marvell", "name": "Marvell",
                 "relation_label": "生产", "relation_type": "produce", "references": ["gs_optical_2025"]},
            ],
            "downstream": [
                {"object_id": "optical_module", "name": "光模块",
                 "relation_label": "供应", "relation_type": "supply", "references": []},
            ],
            "relation_count": 5,
        }
        md = render_object_detail(data)
        assert "# DSP" in md
        assert "`dsp`" in md
        assert "Digital Signal Processor" in md
        assert "## 上游" in md
        assert "## 下游" in md
        assert "Marvell" in md
        assert "光模块" in md
        assert "refs=1" in md  # upstream 含 references 计数

    def test_minimal_data(self):
        data = {"id": "x", "kind": "glossary", "name": "X"}
        md = render_object_detail(data)
        assert "# X" in md
        assert "`x`" in md

    def test_no_upstream_downstream(self):
        data = {"id": "x", "kind": "glossary", "name": "X",
                "upstream": [], "downstream": [], "relation_count": 0}
        md = render_object_detail(data)
        assert "上游 0 个" in md


class TestRenderSearchResults:
    def test_with_results(self):
        results = [
            {"object_id": "dsp", "name": "DSP", "kind": "entity", "matched": "id", "score": 1.0},
            {"object_id": "marvell", "name": "Marvell", "kind": "company", "matched": "tag", "score": 0.5},
        ]
        md = render_search_results(results, "dsp")
        assert "搜索" in md
        assert "2 个结果" in md
        assert "DSP" in md
        assert "Marvell" in md

    def test_no_results(self):
        md = render_search_results([], "notexist")
        assert "未找到" in md
