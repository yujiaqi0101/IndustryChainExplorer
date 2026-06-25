"""CLI 单元测试（不依赖真实数据，测试 parser 和命令分发）。"""

from __future__ import annotations

import pytest

from ice.cli import build_parser


class TestCLIParser:
    def test_search_command(self):
        parser = build_parser()
        args = parser.parse_args(["search", "dsp"])
        assert args.command == "search"
        assert args.keyword == "dsp"
        assert args.limit == 20
        assert args.json is False
        assert callable(args.func)

    def test_search_with_options(self):
        parser = build_parser()
        args = parser.parse_args(["search", "光模块", "--limit", "5", "--json"])
        assert args.keyword == "光模块"
        assert args.limit == 5
        assert args.json is True

    def test_show_command(self):
        parser = build_parser()
        args = parser.parse_args(["show", "dsp"])
        assert args.command == "show"
        assert args.object_id == "dsp"

    def test_package_command(self):
        parser = build_parser()
        args = parser.parse_args(["package"])
        assert args.command == "package"
        assert args.name is None

    def test_package_with_name(self):
        parser = build_parser()
        args = parser.parse_args(["package", "optical"])
        assert args.name == "optical"

    def test_stats_command(self):
        parser = build_parser()
        args = parser.parse_args(["stats"])
        assert args.command == "stats"

    def test_validate_command(self):
        parser = build_parser()
        args = parser.parse_args(["validate"])
        assert args.command == "validate"

    def test_upstream_command(self):
        parser = build_parser()
        args = parser.parse_args(["upstream", "dsp"])
        assert args.command == "upstream"
        assert args.object_id == "dsp"

    def test_downstream_command(self):
        parser = build_parser()
        args = parser.parse_args(["downstream", "dsp"])
        assert args.command == "downstream"
        assert args.object_id == "dsp"

    def test_no_command_fails(self):
        parser = build_parser()
        with pytest.raises(SystemExit):
            parser.parse_args([])

    def test_all_commands_have_func(self):
        """所有子命令都绑定 func 可调用。"""
        parser = build_parser()
        for cmd in ["search dsp", "show dsp", "package", "stats", "validate", "upstream dsp", "downstream dsp"]:
            args = parser.parse_args(cmd.split())
            assert callable(args.func), f"{cmd} 未绑定 func"
