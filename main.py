"""Industry Layer Explorer 产业链浏览器 v5.0（Layered Value Chain）。

一个面向投资研究、行业分析和知识管理的产业链浏览器。
核心模型是 Layer（层），不是 Tree 也不是 Graph。

分层价值链（Layered Value Chain）：
    Layer View（默认主视图）- layers.yaml，ValueChain
    Graph View（辅助视图）- relations.yaml，Relation

命令行接口：

浏览（主视图）：
    python main.py layer                   # 分层价值链（所有产业包）
    python main.py layer optical           # 指定产业包分层视图
    python main.py detail 光模块            # 条目详情（浏览模式）
    python main.py detail 光模块 --companies  # 公司模式（显示公司）

搜索：
    python main.py search 光               # 搜索条目/公司

图谱（辅助视图）：
    python main.py graph 光模块             # 关系图数据
    python main.py graph 光模块 --depth 2   # 两层展开
    python main.py graph 光模块 --companies # 公司模式

词典：
    python main.py glossary                # 所有名词解释
    python main.py glossary optical        # 指定产业包名词解释

数据：
    python main.py stats                   # 数据统计
    python main.py reload                  # 重新加载数据
    python main.py export items            # 导出条目 JSON
    python main.py export relations        # 导出关系 JSON
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from repository import ChainRepository
from search import Searcher
from services import ExplorerService

ROOT_DIR = Path(__file__).parent
CHAINS_DIR = ROOT_DIR / "chains"
EXPORT_DIR = ROOT_DIR / "data" / "exports"


def _get_repo() -> ChainRepository:
    return ChainRepository(CHAINS_DIR)


def _dump(obj) -> None:
    print(json.dumps(obj, ensure_ascii=False, indent=2, default=str))


def main() -> int:
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        return 0

    cmd = args[0]
    repo = _get_repo()
    chain_map = repo.load()
    explorer = ExplorerService(chain_map)

    # -- 数据统计 --
    if cmd == "stats":
        stats = explorer.stats()
        print("Industry Layer Explorer 数据统计：")
        for k, v in stats.items():
            print(f"  {k}: {v}")
        return 0

    # -- 重新加载 --
    if cmd == "reload":
        chain_map = repo.load()
        print("数据已重新加载：")
        for k, v in explorer.stats().items():
            print(f"  {k}: {v}")
        return 0

    # -- 产业包列表 --
    if cmd == "chains":
        _dump(explorer.list_chains())
        return 0

    # -- 分层价值链（主视图）--
    if cmd == "layer":
        chain = args[1] if len(args) >= 2 else None
        _dump(explorer.layer_view(chain))
        return 0

    # -- 条目详情（支持 --companies 公司模式）--
    if cmd == "detail" and len(args) >= 2:
        show_companies = "--companies" in args
        result = explorer.get_detail(args[1], show_companies=show_companies)
        if result is None:
            print(f"未找到: {args[1]}")
            return 1
        _dump(result)
        return 0

    # -- 搜索 --
    if cmd == "search" and len(args) >= 2:
        searcher = Searcher(chain_map)
        results = searcher.search(args[1])
        _dump([r.to_dict() for r in results])
        return 0

    # -- 关系图（辅助视图）--
    if cmd == "graph" and len(args) >= 2:
        depth = 1
        if "--depth" in args:
            idx = args.index("--depth")
            if idx + 1 < len(args):
                depth = int(args[idx + 1])
        show_companies = "--companies" in args
        result = explorer.graph_data(
            args[1], depth=depth, show_companies=show_companies
        )
        if result is None:
            print(f"未找到: {args[1]}")
            return 1
        _dump(result)
        return 0

    # -- 名词解释 --
    if cmd == "glossary":
        chain = args[1] if len(args) >= 2 else None
        _dump(explorer.glossary(chain))
        return 0

    # -- 导出数据 --
    if cmd == "export" and len(args) >= 2:
        EXPORT_DIR.mkdir(parents=True, exist_ok=True)
        if args[1] == "items":
            all_items = explorer.list_all_items()
            export_path = EXPORT_DIR / "items_export.json"
            export_path.write_text(
                json.dumps(all_items, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            print(f"已导出 {len(all_items)} 个条目到 {export_path}")
            return 0
        elif args[1] == "relations":
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
            print(f"已导出 {len(all_relations)} 条关系到 {export_path}")
            return 0

    print(f"未知命令: {cmd}")
    print(__doc__)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
