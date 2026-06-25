"""Services 层单元测试（GraphService + SearchService）。"""

from __future__ import annotations

from pathlib import Path

import pytest

from ice.repository import Repository
from ice.services import GraphService, SearchService


def _make_obj(idx: str, kind: str = "entity", entity_type: str = "component", name: str = "") -> str:
    """生成单个 object 的 YAML 片段。"""
    nm = name or idx
    if kind == "entity":
        return (
            f"- id: {idx}\n  kind: entity\n  entity_type: {entity_type}\n  name: {nm}\n"
            f"  aliases: []\n  summary: ''\n  tags: []\n"
            f"  created_at: '2026-01-01'\n  updated_at: '2026-01-01'\n"
        )
    return (
        f"- id: {idx}\n  kind: {kind}\n  name: {nm}\n"
        f"  aliases: []\n  summary: ''\n  tags: []\n"
        f"  created_at: '2026-01-01'\n  updated_at: '2026-01-01'\n"
    )


def _make_rel(rid: str, frm: str, to: str, rtype: str, refs: list[str] | None = None) -> str:
    """生成单个 relation 的 YAML 片段。"""
    ref_block = ""
    if refs:
        ref_block = "  references:\n" + "".join(f"    - {r}\n" for r in refs)
    return (
        f"- id: {rid}\n  from: {frm}\n  to: {to}\n  type: {rtype}\n"
        f"{ref_block}  created_at: '2026-01-01'\n  updated_at: '2026-01-01'\n"
    )


@pytest.fixture()
def repo_with_graph(tmp_path: Path) -> Repository:
    """构造含多类关系的测试包，验证方向语义。"""
    pkg = tmp_path / "test"
    pkg.mkdir()
    (pkg / "package.yaml").write_text("name: test\n", encoding="utf-8")
    (pkg / "objects").mkdir()
    objs = [
        _make_obj("a", "entity", "component", "A"),
        _make_obj("b", "entity", "product", "B"),
        _make_obj("c", "entity", "product", "C"),
        _make_obj("d", "entity", "product", "D"),
        _make_obj("e", "entity", "product", "E"),
        _make_obj("f", "entity", "product", "F"),
        _make_obj("ref1", "reference", name="R1"),
    ]
    (pkg / "objects" / "o.yaml").write_text("".join(objs), encoding="utf-8")
    (pkg / "relations").mkdir()
    rels = [
        _make_rel("r1", "a", "b", "supply"),       # a→b, a 上游
        _make_rel("r2", "a", "c", "produce"),      # a→c, a 上游
        _make_rel("r3", "b", "a", "use", ["ref1"]), # a→b(use语义:被用方在上游) a 上游
        _make_rel("r4", "c", "d", "integrate"),    # d→c, d 上游
        _make_rel("r5", "e", "f", "related_to"),   # 对称
        _make_rel("r6", "b", "c", "belong_to"),    # c→b, c 上游
        _make_rel("r7", "d", "e", "standardize"),  # e→d, e 上游
        _make_rel("r8", "e", "f", "compete"),      # 对称
    ]
    (pkg / "relations" / "r.yaml").write_text("".join(rels), encoding="utf-8")
    repo = Repository(tmp_path)
    result = repo.load()
    assert result.ok, result.errors
    return repo


# ============================================================
# GraphService 方向语义
# ============================================================
class TestGraphDirection:
    def test_supply_upstream(self, repo_with_graph: Repository):
        """supply: from(a) 是 to(b) 上游 → b 的上游含 a。"""
        g = GraphService(repo_with_graph)
        up = g.get_upstream("b")
        ids = {u["object_id"] for u in up}
        assert "a" in ids  # supply a→b

    def test_produce_upstream(self, repo_with_graph: Repository):
        """produce: from(a) 是 to(c) 上游 → c 的上游含 a。"""
        g = GraphService(repo_with_graph)
        up = g.get_upstream("c")
        ids = {u["object_id"] for u in up}
        assert "a" in ids  # produce a→c

    def test_use_upstream(self, repo_with_graph: Repository):
        """use: from(b) 用 to(a)，被用方 a 在上游 → b 的上游含 a。"""
        g = GraphService(repo_with_graph)
        up = g.get_upstream("b")
        ids = {u["object_id"] for u in up}
        assert "a" in ids  # use b→a, a 是 b 上游

    def test_integrate_upstream(self, repo_with_graph: Repository):
        """integrate: from(c) 集成 to(d)，被集成方 d 在上游 → c 的上游含 d。"""
        g = GraphService(repo_with_graph)
        up = g.get_upstream("c")
        ids = {u["object_id"] for u in up}
        assert "d" in ids  # integrate c→d, d 是 c 上游

    def test_belong_to_upstream(self, repo_with_graph: Repository):
        """belong_to: from(b) 属于 to(c)，c 在上游 → b 的上游含 c。"""
        g = GraphService(repo_with_graph)
        up = g.get_upstream("b")
        ids = {u["object_id"] for u in up}
        assert "c" in ids  # belong_to b→c, c 是 b 上游

    def test_standardize_upstream(self, repo_with_graph: Repository):
        """standardize: to(e) 标准化 from(d)，e 在上游 → d 的上游含 e。"""
        g = GraphService(repo_with_graph)
        up = g.get_upstream("d")
        ids = {u["object_id"] for u in up}
        assert "e" in ids  # standardize d→e, e 是 d 上游

    def test_symmetric_related(self, repo_with_graph: Repository):
        """related_to 对称：e 和 f 互为邻居。"""
        g = GraphService(repo_with_graph)
        e_neighbors = {n["object_id"] for n in g.get_neighbors("e")}
        f_neighbors = {n["object_id"] for n in g.get_neighbors("f")}
        assert "f" in e_neighbors
        assert "e" in f_neighbors

    def test_downstream_supply(self, repo_with_graph: Repository):
        """supply a→b → a 的下游含 b。"""
        g = GraphService(repo_with_graph)
        down = g.get_downstream("a")
        ids = {d["object_id"] for d in down}
        assert "b" in ids  # supply
        assert "c" in ids  # produce

    def test_references_in_neighbor(self, repo_with_graph: Repository):
        """neighbor 条目含 references 列表。"""
        g = GraphService(repo_with_graph)
        up = g.get_upstream("b")
        use_rel = [u for u in up if u["relation_type"] == "use"]
        assert use_rel
        assert use_rel[0]["references"] == ["ref1"]

    def test_get_relations(self, repo_with_graph: Repository):
        g = GraphService(repo_with_graph)
        rels = g.get_relations("a")
        # a 涉及 supply(a→b), produce(a→c), use(b→a)
        types = {r["type"] for r in rels}
        assert "supply" in types
        assert "produce" in types
        assert "use" in types
        # 每条含 from/to 字段
        assert all("from" in r and "to" in r for r in rels)


# ============================================================
# SearchService
# ============================================================
class TestSearchService:
    def test_search_by_id_exact(self, repo_with_graph: Repository):
        s = SearchService(repo_with_graph)
        hits = s.search("a")
        assert any(h.object_id == "a" and h.score == 1.0 for h in hits)

    def test_search_by_name(self, repo_with_graph: Repository):
        s = SearchService(repo_with_graph)
        hits = s.search("A")
        assert hits
        assert hits[0].object_id == "a"

    def test_search_empty_keyword(self, repo_with_graph: Repository):
        s = SearchService(repo_with_graph)
        assert s.search("") == []
        assert s.search("   ") == []

    def test_search_no_match(self, repo_with_graph: Repository):
        s = SearchService(repo_with_graph)
        assert s.search("zzzznotexist") == []

    def test_search_limit(self, repo_with_graph: Repository):
        s = SearchService(repo_with_graph)
        hits = s.search("a", limit=1)
        assert len(hits) <= 1
