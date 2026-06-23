"""业务服务层。

Services 是浏览器的业务入口：
    User → Services → Repository → industries/

PRD Part 01 核心设计：任何对象都只有一个详情页。
对外提供统一 ExplorerService，不再按类型拆分。

PRD Part 02 新增：UserDataStore（收藏/笔记/最近浏览/知识路径）。
"""

from .explorer_service import ExplorerService
from .user_data import UserDataStore

__all__ = ["ExplorerService", "UserDataStore"]
