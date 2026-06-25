# Industry Chain Explorer 产业链浏览器

一个面向投资研究、行业分析和知识管理的**分层价值链浏览器（Layered Value Chain Explorer）**。

## 核心模型：Layer（层）

不是 Tree，也不是 Graph，而是 **Layer（层）**。

用户搜索"光模块"，一眼看清整个产业的分层结构：

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
应用层（Application）
    AI服务器 / 数据中心 / 交换机
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
系统层（System）
    800G光模块 / 1.6T光模块 / CPO
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
器件层（Component）
    DSP / EML激光器 / VCSEL / 硅光芯片
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
材料层（Material）
    硅片 / PCB / 石英
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

## 视图优先级

- **Layer View（默认主视图）** - 分层价值链，一眼看清整个产业
- **Graph View（辅助视图）** - 关系图，可切换

## Layer 是产业自定义的

不同产业的层数完全由产业自己定义：

| 产业     | 层数 | 分层 |
|---------|------|------|
| 光模块   | 4 层 | Application / System / Component / Material |
| 机器人   | 5 层 | Application / Machine / Module / Component / Material |
| 半导体   | 6 层 | EDA / IP / Design / Foundry / Packaging / Application |

系统不固定层数，每个产业自定义。

## 项目结构

```
产业链浏览器/
├── main.py                   # CLI 入口
├── api/app.py                # FastAPI 服务
├── ui/streamlit/app.py       # Streamlit UI
├── chains/                   # 产业包
│   └── optical/              # 光模块产业包
│       ├── overview.yaml     # 产业包元信息
│       ├── layers.yaml       # 核心数据（分层）
│       ├── companies.yaml    # 公司清单（按 Layer 分组）
│       ├── relations/        # 产业关系（Graph View）
│       ├── glossary.yaml     # 名词解释
│       └── README.md
├── models/                   # 核心数据模型
│   ├── layer.py              # Layer / LayerItem / ValueChain
│   ├── node.py               # Node / NodeType
│   ├── relation.py           # Relation / RelationType
│   └── tag.py                # Tag
├── repository/               # 数据仓库（加载产业包）
├── services/                 # 业务服务
├── search/                   # 搜索引擎
├── tests/                    # 测试
└── lib/                      # 第三方前端库（vis-network）
```

## 5 种产业关系（Graph View）

- `Upstream` - 上游：A 的上游是 B（光模块 上游 DSP）
- `Downstream` - 下游：A 的下游是 B（光模块 下游 AI服务器）
- `Supplies` - 供应：A 供应给 B（DSP 供应 光模块）
- `Uses` - 使用：A 使用 B（800G 使用 DSP）
- `Related` - 关联：A 关联 B（CPO 关联 硅光）

每个关系必须包含引用来源（reference 列表，允许多个来源）。

## 快速开始

### 安装依赖

```bash
pip install -r requirements.txt
```

### CLI 模式

```bash
# 分层价值链（主视图）
python main.py layer optical

# 条目详情
python main.py detail DSP
python main.py detail 800G光模块 --companies   # 公司模式

# 搜索
python main.py search 光

# 关系图（辅助视图）
python main.py graph 光模块

# 名词解释
python main.py glossary optical

# 数据统计
python main.py stats
```

### API 模式

```bash
# 直接命令
uvicorn api.app:app --reload

# 或用启动脚本（自动探测 Python）
bash scripts/start_backend.sh        # bash
scripts\start_backend.bat            # Windows CMD
```

- `GET /layer?chain=optical` - 分层价值链
- `GET /detail/{name}` - 条目详情
- `GET /graph/{name}` - 关系图
- `GET /glossary?chain=optical` - 名词解释
- `GET /search?q=光` - 搜索
- `GET /stats` - 统计

### Streamlit UI

```bash
# 直接命令
streamlit run ui/streamlit/app.py

# 或用启动脚本
bash scripts/start_frontend.sh       # bash
scripts\start_frontend.bat           # Windows CMD
```

### 一键启动前后端（开发模式）

```bash
bash scripts/dev.sh                  # bash（Ctrl+C 同停）
scripts\dev.bat                      # Windows CMD（关窗口同停）
```

详见 `scripts/README.md`。

### 测试

```bash
pytest tests/ -v
```

## 核心理念

> 不要把产业链浏览器设计成一个"关系图浏览器"，而是设计成一个"分层价值链浏览器（Layered Value Chain Explorer）"。

Layer 比 Graph 更符合人的认知：一眼看清整个产业。
