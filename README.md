# Industry Chain Explorer (ICE) 产业链知识操作系统

一个面向投资研究、行业分析的**知识中心型产业链浏览器**，采用本体-事实分离的知识表示架构，支持可扩展的多产业链知识库。

> **v2.0 架构升级**：从M1分层模型升级为知识中心架构，引入RDF三元组建模、本体层、自动验证管线和五层质量校验。

---

## 核心理念

不是 Tree，也不是 Graph，而是 **知识驱动的分层价值链浏览器**：

- **知识层分离**：本体（Ontology）、事实（Facts）、视图（Package Layout）三层解耦
- **数据可溯源**：所有事实必须关联引用来源，保证投研数据可信度
- **自动验证**：加载时自动执行5层验证，保证数据质量
- **多产业支持**：通过Package机制支持光模块、机器人、半导体等不同产业链

光模块产业链分层示例：
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
应用层（Application）
    AI服务器 / 数据中心 / 交换机
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
产品层（Product）
    800G光模块 / 1.6T光模块 / CPO
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
器件层（Component）
    DSP / EML激光器 / VCSEL / 硅光芯片
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
材料层（Material）
    硅片 / PCB / 石英
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
技术层（Technology）
    PAM4 / PAM3 / FEC / 硅光集成
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## 架构概览（v2.0 知识中心）

```
┌─────────────────────────────────────────────────────────┐
│                    Presentation Layer                    │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │
│  │  Streamlit   │  │   FastAPI    │  │     CLI      │   │
│  │      UI      │  │  REST API    │  │              │   │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘   │
└─────────┼─────────────────┼─────────────────┼───────────┘
          │                 │                 │
┌─────────▼─────────────────▼─────────────────▼───────────┐
│                  Knowledge Repository                    │
│  ┌────────────────────────────────────────────────────┐  │
│  │  Bootstrap Pipeline (7 stages)                     │  │
│  │  Discover → Load → Parse → Validate → Link         │  │
│  │           → Index → Graph                          │  │
│  └────────────────────────────────────────────────────┘  │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐ │
│  │ Objects  │  │  Facts   │  │ Ontology │  │ Packages │ │
│  │ (Nodes)  │  │(Triples) │  │  (Schema)│  │ (Layout) │ │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘ │
│  ┌────────────────────────────────────────────────────┐  │
│  │  Knowledge Graph + Search Index                    │  │
│  └────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

---

## 数据模型

### 三层知识结构

| 层级 | 目录 | 说明 | 格式 |
|------|------|------|------|
| **Ontology（本体层）** | `ontology/` | 分类体系 + 谓词定义 | taxonomy.yaml + predicates.yaml |
| **Knowledge（知识层）** | `knowledge/` | 对象（概念/组织/文献）+ 事实（三元组） | objects/*.yaml + facts/fact_*.yaml |
| **Package（产业包层）** | `packages/` | 产业定义、入口点、分层布局 | {package_id}/package.yaml |

### 核心实体

- **Object（对象/节点）**：分为三类：
  - `concept` - 概念/产品/技术/材料
  - `organization` - 公司/机构/标准组织
  - `document` - 研究报告/年报/白皮书/标准

- **Fact（事实/边）**：RDF风格三元组 `(subject, predicate, object)`，必须带citations引用来源

- **Predicate（谓词/关系类型）**：内置14种关系：
  - 分类/组成：`is_a`（属于）、`part_of`（组成部分）
  - 供应链：`produce`（生产）、`supply`（供应）、`use`（使用）
  - 技术：`apply_to`（应用于）、`replace`（替代）、`depends_on`（依赖）、`integrate`（集成）
  - 商业：`compete_with`（竞争）、`research_on`（研究）
  - 其他：`related_to`（相关）、`defined_by`（由...定义）、`published_by`（由...发布）

详细格式规范见 **[数据包格式定义](./docs/1.数据包格式定义.md)**。

---

## 当前数据统计（光模块产业包）

| 指标 | 数量 |
|------|------|
| 概念对象 | 30 |
| 公司组织 | 10 |
| 引用文献 | 6 |
| 事实三元组 | 50 |
| 产业链分层 | 5层（技术→材料→器件→产品→应用） |
| 验证质量分 | 97/100 |

---

## 项目结构

```
IndustryChainExplorer/
├── main.py                   # CLI 入口
├── api/                      # FastAPI REST API
│   └── app.py
├── ui/streamlit/             # Streamlit Web UI
│   └── app.py
├── ice/                      # 核心引擎 (ICE Core)
│   ├── models/               # Pydantic 数据模型
│   │   ├── object.py         # Object 模型（三种类型）
│   │   ├── fact.py           # Fact 三元组模型
│   │   ├── package.py        # Package 产业包模型
│   │   ├── ontology.py       # 本体模型（分类/谓词）
│   │   ├── graph.py          # 知识图
│   │   └── validation.py     # 验证报告模型
│   ├── pipeline/             # 加载管线
│   │   └── stages/           # 7个管线阶段：discover/load/parse/validate/link/index/graph
│   ├── repository/           # KnowledgeRepository 统一入口
│   └── cli.py                # CLI 命令实现
├── ontology/                 # 全局本体层
│   ├── taxonomy.yaml         # 分类体系
│   └── predicates.yaml       # 谓词/关系类型定义
├── knowledge/                # 知识层（全局共享）
│   ├── objects/              # 对象（每个文件一个对象）
│   └── facts/                # 事实（每个文件一个三元组）
├── packages/                 # 产业包层（视图定义）
│   └── optical/              # 光模块产业包
│       └── package.yaml      # 分层配置/入口点/元信息
├── scripts/                  # 启动脚本
│   ├── start_frontend.bat/sh
│   ├── start_backend.bat/sh
│   └── dev.bat/sh            # 一键启动前后端
├── tests/                    # 单元测试
└── docs/                     # 文档
    └── 1.数据包格式定义.md   # 数据包格式规范
```

---

## 快速开始

### 安装依赖

```bash
pip install -r requirements.txt
```

### 启动前端（Streamlit Web UI）

```bash
# Windows
scripts\start_frontend.bat

# Linux/Mac
bash scripts/start_frontend.sh

# 或直接运行
streamlit run ui/streamlit/app.py --server.port 8501
```

打开浏览器访问 **http://localhost:8501**

前端包含5个功能页面：
- 📊 **概览**：知识库统计、产业分层结构
- 🔍 **搜索**：关键词搜索对象（ID/名称/别名）
- 📦 **对象浏览器**：按类型筛选，查看对象详情和关联关系
- 📈 **知识图谱**：从入口点展开关系网络，支持深度1-2层
- ✅ **验证报告**：加载验证结果，质量评分

### 启动后端（FastAPI）

```bash
# Windows
scripts\start_backend.bat

# Linux/Mac
bash scripts/start_backend.sh

# 或直接运行
uvicorn api.app:app --reload --port 8000
```

API端点：
- `GET /stats` - 知识库统计
- `GET /objects` - 对象列表
- `GET /objects/{id}` - 对象详情
- `GET /search?q=关键词` - 搜索
- `GET /graph/{id}?depth=1` - 对象关系图
- `GET /validation` - 验证报告

### 一键启动开发模式

```bash
scripts\dev.bat     # Windows
bash scripts/dev.sh # Linux/Mac
```
前后端同时启动，关闭窗口自动停止所有进程。

### CLI 命令行模式

```bash
# 查看知识库统计
python main.py stats

# 搜索对象
python main.py search 光模块

# 查看对象详情
python main.py detail optical_module

# 查看对象关系图
python main.py graph optical_module --depth 1

# 产业分层视图
python main.py layer optical
```

### 运行测试

```bash
pytest tests/ -v
```

---

## 验证机制

知识库加载时自动执行七层管线，其中验证阶段执行5层检查：

1. **Schema 校验**：所有YAML字段符合Pydantic模型定义，禁止额外字段
2. **引用完整性**：Fact中引用的subject/object/citations必须存在
3. **谓词约束**：主语/宾语类型必须符合谓词定义的类型范围
4. **分类校验**：对象分类必须存在于分类体系中
5. **质量提示**：
   - 🔴 Error：必须修复
   - 🟡 Warning：建议修复（如缺少citations）
   - ℹ️ Info：可选改进（如建议加summary/aliases）

当前光模块数据包验证结果：0错误，0警告，质量分 **97/100**。

---

## 添加新产业链

1. 在 `ontology/` 扩展分类和谓词（如需要新的关系类型）
2. 在 `knowledge/objects/` 添加新概念/公司/文献对象
3. 在 `knowledge/facts/` 添加事实三元组（注意`citations`不能为空）
4. 在 `packages/{new_industry}/` 创建产业包目录和 `package.yaml`，定义分层配置和入口点
5. 重启服务，系统自动发现并加载新数据

详细规范请阅读 **[数据包格式定义](./docs/1.数据包格式定义.md)**。

---

## 版本历史

### v2.0.0 (当前) - 知识中心架构
- ✅ 重构为知识中心架构：本体/知识/包三层分离
- ✅ RDF三元组事实模型，所有事实可溯源
- ✅ 七层加载管线 + 五层验证机制
- ✅ Streamlit前端重写，5个功能页面
- ✅ FastAPI REST API
- ✅ 光模块产业包完整数据（44对象/50事实）

### v1.x - 分层模型初始版本
- 基础分层价值链视图
- 单文件产业包格式
- 简单CLI界面
