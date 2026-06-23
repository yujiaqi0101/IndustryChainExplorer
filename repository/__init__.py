"""数据加载层（Layered Value Chain 分层价值链）。

Repository 负责：
    chains/{产业包}/ 分层目录 YAML
        ↓
    ValueChain（分层价值链，核心） + Relation（产业关系，辅助）
        ↓
    ChainMap（内存索引）

分层价值链架构：
    Layer View（主视图）- layers.yaml，ValueChain
    Graph View（辅助视图）- relations.yaml，Relation
    公司按 Layer 分组 - companies.yaml
    名词解释 - glossary.yaml

不依赖数据库，纯文件驱动，Git 友好。
产业包优先：新增行业只需新增目录，程序无需修改。
"""

from .chain_repo import ChainMap, ChainRepository, CompanyInfo

__all__ = ["ChainMap", "ChainRepository", "CompanyInfo"]
