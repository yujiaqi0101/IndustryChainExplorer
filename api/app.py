"""Industry Layer Explorer API（Layered Value Chain 分层价值链）。

核心模型是 Layer（层），不是 Tree 也不是 Graph。

视图优先级：
    Layer View（默认主视图）- /layer
    Graph View（辅助视图）- /graph

接口：
    GET  /                          服务信息
    GET  /stats                     数据统计
    GET  /search?q=光               搜索
    GET  /chains                    产业包列表
    GET  /items                     所有条目
    GET  /layer                     分层价值链（主视图）
        ?chain=optical              指定产业包
    GET  /detail/{name}             条目详情（基于 Layer）
        ?show_companies=true        公司模式
    GET  /graph/{name}              关系图（辅助视图）
        ?depth=2                    展开深度
        ?show_companies=true        公司模式
    GET  /glossary                  名词解释
        ?chain=optical              指定产业包
    GET  /tags                      所有标签
    GET  /tags/{tag}                按标签查找
    GET  /hot                       热门产业

    GET  /user/data                 用户数据全部
    GET  /user/favorites            收藏列表
    POST /user/favorites/{node_id}  添加收藏
    DELETE /user/favorites/{node_id} 取消收藏
    GET  /user/notes/{node_id}      获取笔记
    POST /user/notes/{node_id}      保存笔记
    GET  /user/recent               最近浏览
    GET  /user/paths                知识路径列表
    POST /user/paths                保存知识路径

启动：
    uvicorn api.app:app --reload
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from repository import ChainRepository
from search import Searcher
from services import ExplorerService, UserDataStore

CHAINS_DIR = ROOT / "chains"
USER_DATA_PATH = ROOT / "data" / "user_data.json"

_repo = ChainRepository(CHAINS_DIR)
_chain_map = _repo.load()
_explorer = ExplorerService(_chain_map)
_searcher = Searcher(_chain_map)
_user_data = UserDataStore(USER_DATA_PATH)

app = FastAPI(title="Industry Layer Explorer API", version="5.0")


# ======================================================================
# 浏览接口
# ======================================================================
@app.get("/")
def root() -> dict:
    return {"service": "Industry Layer Explorer", "version": "5.0"}


@app.get("/stats")
def stats() -> dict:
    return _explorer.stats()


@app.get("/search")
def search(q: str = Query(..., description="关键词")) -> dict:
    results = _searcher.search(q)
    return {"query": q, "count": len(results), "results": [r.to_dict() for r in results]}


@app.get("/chains")
def list_chains() -> dict:
    """产业包列表。"""
    return {"chains": _explorer.list_chains()}


@app.get("/items")
def list_items() -> dict:
    """所有条目（跨产业包）。"""
    return {"items": _explorer.list_all_items()}


@app.get("/layer")
def layer_view(chain: str | None = Query(None, description="产业包名")) -> dict:
    """分层价值链（默认主视图）。

    从 layers.yaml 加载的分层视图，一眼看清整个产业。
    每个产业自定义层数（光模块4层，机器人5层，半导体6层）。
    """
    return {"chains": _explorer.layer_view(chain)}


@app.get("/detail/{name}")
def get_detail(
    name: str,
    show_companies: bool = Query(False, description="公司模式（显示公司）"),
) -> dict:
    """条目详情（基于 Layer）。

    展示：所在层、同层条目、上游层、下游层、关联公司（公司模式）。
    """
    result = _explorer.get_detail(name, show_companies=show_companies)
    if result is None:
        raise HTTPException(status_code=404, detail=f"未找到: {name}")
    return result


@app.get("/graph/{name}")
def graph_data(
    name: str,
    depth: int = Query(1, ge=1, le=3, description="展开深度"),
    show_companies: bool = Query(False, description="公司模式（显示公司）"),
) -> dict:
    """关系图数据（辅助视图，vis-network 格式）。

    基于 relations.yaml 构建 Graph。
    """
    result = _explorer.graph_data(name, depth=depth, show_companies=show_companies)
    if result is None:
        raise HTTPException(status_code=404, detail=f"未找到: {name}")
    return result


@app.get("/glossary")
def glossary(chain: str | None = Query(None, description="产业包名")) -> dict:
    """名词解释（glossary.yaml）。"""
    return {"terms": _explorer.glossary(chain)}


@app.get("/tags")
def list_tags() -> dict:
    """所有标签。"""
    return {"tags": _explorer.list_all_tags()}


@app.get("/tags/{tag}")
def search_by_tag(tag: str) -> dict:
    """按标签查找条目。"""
    results = _explorer.search_by_tag(tag)
    return {"tag": tag, "count": len(results), "results": results}


@app.get("/hot")
def hot_industries(limit: int = Query(10, ge=1, le=50)) -> dict:
    """热门产业。"""
    return {"industries": _explorer.hot_industries(limit)}


# ======================================================================
# 用户数据接口（收藏/笔记/最近浏览/知识路径）
# ======================================================================
@app.get("/user/data")
def user_data_all() -> dict:
    """用户数据全部。"""
    return _user_data.all()


# -- 收藏 -------------------------------------------------------------
@app.get("/user/favorites")
def list_favorites() -> dict:
    return {"favorites": _user_data.list_favorites()}


@app.post("/user/favorites/{node_id}")
def add_favorite(node_id: str) -> dict:
    _user_data.add_favorite(node_id)
    return {"id": node_id, "favorite": True}


@app.delete("/user/favorites/{node_id}")
def remove_favorite(node_id: str) -> dict:
    _user_data.remove_favorite(node_id)
    return {"id": node_id, "favorite": False}


# -- 笔记 -------------------------------------------------------------
@app.get("/user/notes/{node_id}")
def get_note(node_id: str) -> dict:
    return {"id": node_id, "note": _user_data.get_note(node_id)}


class NoteBody(BaseModel):
    text: str


@app.post("/user/notes/{node_id}")
def set_note(node_id: str, body: NoteBody) -> dict:
    _user_data.set_note(node_id, body.text)
    return {"id": node_id, "note": body.text}


# -- 最近浏览 ---------------------------------------------------------
@app.get("/user/recent")
def list_recent(limit: int = Query(20, ge=1, le=100)) -> dict:
    return {"recent": _user_data.list_recent(limit)}


class RecentBody(BaseModel):
    id: str
    name: str
    type: str


@app.post("/user/recent")
def add_recent(body: RecentBody) -> dict:
    _user_data.add_recent(body.id, body.name, body.type)
    return {"ok": True}


# -- 知识路径 ---------------------------------------------------------
@app.get("/user/paths")
def list_paths() -> dict:
    return {"paths": _user_data.list_paths()}


class PathNode(BaseModel):
    id: str
    name: str
    type: str


class PathBody(BaseModel):
    name: str
    trail: list[PathNode]


@app.post("/user/paths")
def save_path(body: PathBody) -> dict:
    path_id = _user_data.save_path(
        body.name,
        [n.model_dump() for n in body.trail],
    )
    return {"id": path_id, "ok": True}


@app.delete("/user/paths/{path_id}")
def delete_path(path_id: str) -> dict:
    _user_data.delete_path(path_id)
    return {"ok": True}
