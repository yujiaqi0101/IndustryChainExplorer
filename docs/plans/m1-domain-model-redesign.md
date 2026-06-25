# M1 Domain Model 重构计划（Part 06 严格遵从版）

> 本轮目标：把上一轮 src/ 实现严格对齐 Part 06 字面规范，重组为 ice/ 包。
> 上一轮做了 6 处"改进"，本轮按用户决策回退到 Part 06 原文规范。

## 一、与上一轮 src/ 实现的差异（必须对齐）

| # | 维度 | 上一轮 src/ 现状 | Part 06 字面要求 | 本轮动作 |
|---|------|----------------|-----------------|---------|
| 1 | 包目录 | `src/{domain,loader,service,renderer,cli}/` | `ice/{models,repository,services}/` | 重组为 ice/ |
| 2 | Relation 字段 | `source/target/relation_type` | `from/to/type` | 改字段名（from_+alias） |
| 3 | 证据绑定 | `citations: [Citation]` 对象（page/quote） | `references: [id]` id 列表 | 降级为 id 列表 |
| 4 | RelationType | 7 种（缺 belong_to/standardize/research，related_to→related） | 10 种（supply/use/produce/integrate/replace/compete/belong_to/related_to/standardize/research） | 补齐 10 种，related→related_to |
| 5 | ObjectKind | 5 种（缺 organization） | 6 种（entity/company/glossary/reference/organization/standard） | 补齐 organization |
| 6 | Object.metadata | 有 `metadata: dict` | Part 06 未提及 | 移除 metadata 字段 |

## 二、关于 `from` 是 Python 关键字

Part 06 YAML 字段名 `from` 是 Python 关键字，不能直接做属性名。处理方式：
```python
class Relation(BaseModel):
    from_: str = Field(alias="from")   # YAML 写 from:，代码用 .from_
    to: str
    type: RelationType
    references: list[str] = []
    model_config = ConfigDict(populate_by_name=True)
```
YAML 数据严格用 `from:`，Pydantic 通过 alias 映射，代码内访问 `r.from_`。

## 三、目标目录结构

```
ice/
├── __init__.py
├── models/                   # Pydantic v2 Schema（Part 06 第一~七节）
│   ├── __init__.py
│   ├── object.py             # Object + ObjectKind(6) + EntityType(6) + validate_object_id
│   ├── relation.py           # Relation + RelationType(10) + from_/to/type/references
│   ├── layout.py             # Layout + Section
│   └── package.py            # Package
├── repository/               # Loader + Validator + Index
│   ├── __init__.py
│   ├── loader.py             # ObjectLoader + RelationLoader + PackageLoader
│   ├── validator.py          # Repository（跨文件校验）
│   └── cache.py              # pickle 缓存
├── services/                 # 业务服务
│   ├── __init__.py
│   ├── graph_service.py      # NetworkX DiGraph 上下游计算
│   └── search_service.py     # 对象搜索索引
├── renderer/
│   ├── __init__.py
│   └── markdown.py
└── cli.py                    # ice CLI 入口
```

## 四、数据迁移映射表

packages/optical 数据需按以下规则转换：

### Object（objects/*.yaml + glossary/*.yaml）
- 删除 `metadata` 字段（若有）
- 其余字段（id/kind/name/aliases/summary/tags/entity_type/created_at/updated_at）保持不变
- company 的 code/market、reference 的 title/author/published_date、standard 的 version 保留为可选字段

### Relation（relations/*.yaml）
| 旧字段 | 新字段 |
|--------|--------|
| `source` | `from` |
| `target` | `to` |
| `relation_type` | `type` |
| `citations:\n  - reference_id: xxx` | `references:\n  - xxx` |

### related_to 类型
- 旧值 `related` → 新值 `related_to`（严格遵从 Part 06 第七节）

### Layout（layout.yaml）
- 结构不变（sections/Section），保持现有格式

## 五、Tasks List

### Sprint 1 — Domain Model（ice/models/）
- [x] `object.py`：Object + ObjectKind(6, +organization) + EntityType(6) + validate_object_id，移除 metadata
- [x] `relation.py`：Relation + RelationType(10, +belong_to/standardize/research, related→related_to) + from_(alias="from")/to/type/references(list[str])
- [x] `layout.py`：Layout + Section（保持不变）
- [x] `package.py`：Package（移除 metadata 相关）
- [x] 单元测试 `tests/test_domain.py`（23 用例）

### Sprint 2 — Loader + Validator（ice/repository/）
- [x] `loader.py`：ObjectLoader + RelationLoader + PackageLoader（适配 from/to/type/references）
- [x] `validator.py`：Repository + 跨文件校验（from/to 存在性、references 指向 reference 对象、layout 引用存在）
- [x] `cache.py`：保留现有缓存逻辑
- [x] 单元测试 `tests/test_repository.py`（13 用例）

### Sprint 3 — Services（ice/services/）
- [x] `graph_service.py`：NetworkX DiGraph（from_/to 适配，RelationType 10 种方向语义）
- [x] `search_service.py`：保持不变（只索引 Object）
- [x] 单元测试 `tests/test_services.py`（15 用例，覆盖 10 种 RelationType 方向）

### Sprint 4 — Renderer + CLI（ice/renderer/, ice/cli.py）
- [x] `markdown.py`：渲染对象详情（移除 metadata 段，references 替代 citations）
- [x] `cli.py`：ice search/show/package/stats/validate/upstream/downstream
- [x] 单元测试 `tests/test_cli.py` + `tests/test_renderer.py`（16 用例）

### Sprint 5 — 数据迁移（packages/optical/）
- [x] relations/*.yaml：source→from, target→to, relation_type→type, citations→references（4 文件 29 条）
- [x] related→related_to
- [x] objects/*.yaml：确认无 metadata 字段
- [x] 端到端校验：37 对象 / 29 关系 / 零校验错误 ✓

### Sprint 6 — 清理与验证
- [x] 删除 src/ 整个目录（19 个 .py 文件）
- [x] main.py 改为薄包装调用 ice.cli
- [x] requirements.txt 确认 pydantic>=2.5
- [x] 全量测试通过（76 用例 / 0 失败）

## 六、Check List（验收标准）

- [x] `python -m ice.cli search dsp` 返回 DSP 实体 ✓
- [x] `python -m ice.cli show dsp` 输出对象详情（含上下游）✓
- [x] `python -m ice.cli validate` 零错误 ✓
- [x] `python -m ice.cli upstream optical_module` 返回上游对象 ✓
- [x] `python -m ice.cli downstream dsp` 返回下游对象 ✓
- [x] Relation YAML 文件中字段为 `from`/`to`/`type`/`references`（非 source/target/relation_type/citations）✓
- [x] ObjectKind 含 6 种（含 organization）✓
- [x] RelationType 含 10 种（含 belong_to/standardize/research）✓
- [x] Object 模型无 metadata 字段 ✓
- [x] 全量 pytest 通过（76 用例）✓
- [x] src/ 目录已删除 ✓

## 七、最终交付状态（2026-06-26）

- **测试**：76 passed in 0.48s
- **数据**：1 产业包 / 37 对象 / 29 关系
- **结构**：ice/ 包（models/repository/services/renderer/cli.py）+ main.py 薄包装
- **Part 06 合规**：6 处差异全部回退到字面规范（from/to/type/references + 10 RelationType + 6 ObjectKind + 无 metadata）

## 八、关键设计决策

1. **严格遵从 Part 06 字面**：from/to/type/references，不留"改进版"
2. **from_ + alias 处理 Python 关键字**：YAML 严格用 `from:`，代码用 `from_`
3. **references 是 id 列表**：非 Citation 对象，绑定到 Relation 而非 Object
4. **上下游不落盘**：Relation 只存 type，方向由 GraphService 按 type 语义计算
5. **10 种 RelationType 方向语义**：
   - supply/produce：from 是 to 的上游
   - use/integrate：to 是 from 的上游（被使用方在上游）
   - replace/compete/related_to：对称，无上下游
   - belong_to：from 属于 to（to 是上游/父类）
   - standardize：to 标准化 from（to 是标准，from 是被标准化对象）
   - research：对称，无上下游
6. **organization kind 预留**：本轮补齐枚举值，数据中暂无 organization 对象
