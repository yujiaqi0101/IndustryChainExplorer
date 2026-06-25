"""ICE CLI（PRD Part 06 第十二节）。

命令：
    ice search <keyword>       搜索对象
    ice show <object_id>       对象详情（Markdown）
    ice package [name]         产业包信息
    ice stats                  数据统计
    ice validate               校验数据完整性
    ice upstream <object_id>   上游对象
    ice downstream <object_id> 下游对象

用法：
    python -m ice.cli search dsp
    python -m ice.cli show dsp
    python -m ice.cli validate
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from ice.renderer import render_object_detail, render_search_results
from ice.repository import Repository
from ice.services import GraphService, SearchService

PACKAGES_DIR = ROOT_DIR / "packages"
CACHE_DIR = ROOT_DIR / ".cache"


def _get_services() -> tuple[Repository, GraphService, SearchService]:
    repo = Repository(PACKAGES_DIR, cache_dir=CACHE_DIR)
    result = repo.load()
    if not result.ok:
        print("数据校验失败：", file=sys.stderr)
        for e in result.errors:
            print(f"  - {e}", file=sys.stderr)
    return repo, GraphService(repo), SearchService(repo)


def _build_object_detail(repo: Repository, graph: GraphService, object_id: str) -> dict[str, Any] | None:
    obj = repo.get_object(object_id)
    if obj is None:
        return None
    pkg = repo.get_package_of(object_id)
    section = None
    if pkg and pkg.layout:
        sec = pkg.layout.section_of(object_id)
        if sec:
            section = {"id": sec.id, "title": sec.title, "order": sec.order}
    up = graph.get_upstream(object_id)
    down = graph.get_downstream(object_id)
    return {
        "id": obj.id,
        "kind": obj.kind.value,
        "kind_label": obj.kind_label(),
        "entity_type": obj.entity_type.value if obj.entity_type else "",
        "entity_type_label": obj.entity_type_label(),
        "name": obj.name,
        "aliases": list(obj.aliases),
        "summary": obj.summary,
        "tags": list(obj.tags),
        "code": obj.code,
        "market": obj.market,
        "package": pkg.dir_name if pkg else None,
        "industry": pkg.industry if pkg else "",
        "section": section,
        "upstream": up,
        "downstream": down,
        "relation_count": len(repo.relations_of(object_id)),
    }


def cmd_search(args: argparse.Namespace) -> int:
    _, _, search = _get_services()
    hits = search.search(args.keyword, limit=args.limit)
    results = [h.to_dict() for h in hits]
    if args.json:
        print(json.dumps(results, ensure_ascii=False, indent=2))
        return 0
    print(render_search_results(results, args.keyword))
    return 0 if results else 1


def cmd_show(args: argparse.Namespace) -> int:
    repo, graph, _ = _get_services()
    data = _build_object_detail(repo, graph, args.object_id)
    if data is None:
        print(f"未找到对象: {args.object_id}", file=sys.stderr)
        return 1
    if args.json:
        print(json.dumps(data, ensure_ascii=False, indent=2, default=str))
        return 0
    print(render_object_detail(data))
    return 0


def cmd_package(args: argparse.Namespace) -> int:
    repo, _, _ = _get_services()
    if args.name:
        pkg = next((p for p in repo.packages if p.dir_name == args.name), None)
        if pkg is None:
            print(f"未找到产业包: {args.name}", file=sys.stderr)
            return 1
        sections = [s.id for s in pkg.layout.ordered_sections()] if pkg.layout else []
        print(json.dumps({
            "id": pkg.id, "name": pkg.name, "industry": pkg.industry,
            "version": pkg.version, "objects": len(pkg.objects),
            "relations": len(pkg.relations), "sections": sections,
        }, ensure_ascii=False, indent=2))
        return 0
    print(f"共 {len(repo.packages)} 个产业包：")
    for p in repo.packages:
        secs = [s.id for s in p.layout.ordered_sections()] if p.layout else []
        print(f"  {p.dir_name}  ({p.industry})  对象={len(p.objects)}  关系={len(p.relations)}  层={secs}")
    return 0


def cmd_stats(args: argparse.Namespace) -> int:
    repo, _, _ = _get_services()
    print(json.dumps(repo.stats(), ensure_ascii=False, indent=2))
    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    repo = Repository(PACKAGES_DIR)
    result = repo.load()
    if result.warnings:
        for w in result.warnings:
            print(f"[warn] {w}")
    if result.errors:
        print(f"校验失败，{len(result.errors)} 个错误：")
        for e in result.errors:
            print(f"  - {e}")
        return 1
    print(f"校验通过。{repo.stats()}")
    return 0


def cmd_upstream(args: argparse.Namespace) -> int:
    _, graph, _ = _get_services()
    up = graph.get_upstream(args.object_id)
    if not up:
        print(f"无上游或对象不存在: {args.object_id}")
        return 1
    print(f"上游 {len(up)} 个：")
    for u in up:
        refs = u.get("references", [])
        print(f"  {u['name']}  ({u['object_id']})  {u['relation_label']}  refs={len(refs)}")
    return 0


def cmd_downstream(args: argparse.Namespace) -> int:
    _, graph, _ = _get_services()
    down = graph.get_downstream(args.object_id)
    if not down:
        print(f"无下游或对象不存在: {args.object_id}")
        return 1
    print(f"下游 {len(down)} 个：")
    for d in down:
        refs = d.get("references", [])
        print(f"  {d['name']}  ({d['object_id']})  {d['relation_label']}  refs={len(refs)}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="ice", description="ICE 产业链浏览器")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("search", help="搜索对象")
    p.add_argument("keyword")
    p.add_argument("--limit", type=int, default=20)
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=cmd_search)

    p = sub.add_parser("show", help="对象详情")
    p.add_argument("object_id")
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=cmd_show)

    p = sub.add_parser("package", help="产业包信息")
    p.add_argument("name", nargs="?")
    p.set_defaults(func=cmd_package)

    p = sub.add_parser("stats", help="数据统计")
    p.set_defaults(func=cmd_stats)

    p = sub.add_parser("validate", help="校验数据完整性")
    p.set_defaults(func=cmd_validate)

    p = sub.add_parser("upstream", help="上游对象")
    p.add_argument("object_id")
    p.set_defaults(func=cmd_upstream)

    p = sub.add_parser("downstream", help="下游对象")
    p.add_argument("object_id")
    p.set_defaults(func=cmd_downstream)

    return parser


def main() -> int:
    args = build_parser().parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
