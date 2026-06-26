from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .repository import KnowledgeRepository


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="ice",
        description="Industry Chain Explorer - 产业知识操作系统"
    )
    parser.add_argument(
        "--root", "-r",
        type=Path,
        default=Path.cwd(),
        help="项目根目录（默认当前目录）"
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="遇到验证错误时立即失败"
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    validate_parser = subparsers.add_parser("validate", help="验证知识库")
    stats_parser = subparsers.add_parser("stats", help="显示统计信息")

    show_parser = subparsers.add_parser("show", help="显示对象详情")
    show_parser.add_argument("object_id", help="对象ID")

    search_parser = subparsers.add_parser("search", help="搜索对象")
    search_parser.add_argument("query", help="搜索关键词")

    neighbors_parser = subparsers.add_parser("neighbors", help="显示对象邻居")
    neighbors_parser.add_argument("object_id", help="对象ID")

    args = parser.parse_args()

    repo = KnowledgeRepository(args.root)
    report = repo.load(strict=args.strict)

    if args.command == "validate":
        print(report.format())
        return 1 if report.has_errors() else 0

    if args.command == "stats":
        stats = repo.stats()
        print("=" * 50)
        print("Knowledge Repository Statistics")
        print("=" * 50)
        for k, v in stats.items():
            print(f"  {k:25s}: {v}")
        print("=" * 50)
        print(report.format())
        return 1 if report.has_errors() else 0

    if args.command == "show":
        obj = repo.get_object(args.object_id)
        if obj is None:
            print(f"Error: Object '{args.object_id}' not found", file=sys.stderr)
            return 1
        print(f"ID: {obj.id}")
        print(f"Name: {obj.name}")
        print(f"Kind: {obj.kind.value}")
        if obj.aliases:
            print(f"Aliases: {', '.join(obj.aliases)}")
        if obj.tags:
            print(f"Tags: {', '.join(obj.tags)}")
        if obj.summary:
            print(f"Summary: {obj.summary}")
        return 0

    if args.command == "search":
        results = repo.search(args.query)
        if not results:
            print(f"No results found for '{args.query}'")
            return 0
        print(f"Found {len(results)} results:")
        for obj in results:
            print(f"  {obj.id:25s} [{obj.kind.value:12s}] {obj.name}")
        return 0

    if args.command == "neighbors":
        obj = repo.get_object(args.object_id)
        if obj is None:
            print(f"Error: Object '{args.object_id}' not found", file=sys.stderr)
            return 1
        neighbors = repo.graph.neighbors(args.object_id)
        print(f"Neighbors of '{obj.name}' ({obj.id}): {len(neighbors)}")
        print("-" * 60)
        for nbr, fact, outgoing in neighbors:
            direction = "->" if outgoing else "<-"
            print(f"  {direction} [{fact.predicate:12s}] {nbr.id:25s} {nbr.name}")
        return 0

    return 0


if __name__ == "__main__":
    sys.exit(main())
