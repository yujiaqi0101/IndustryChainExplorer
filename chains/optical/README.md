# 光模块产业包（Layered Value Chain）

Industry Layer Explorer 采用**分层价值链（Layered Value Chain）**架构。

## 目录结构

```
optical/
├── overview.yaml      产业包概览（名称/简介/关键词）
├── layers.yaml        分层价值链（核心，主视图）
├── companies.yaml     公司清单（按 Layer 分组）
├── relations/
│   └── relations.yaml 产业关系（Graph View，辅助视图）
├── glossary.yaml      名词解释
└── README.md         本文件
```

## 分层（4 层）

| 层 | 标题 | 条目 |
|----|------|------|
| Application | 应用层 | AI服务器 / 数据中心 / 交换机 |
| System | 系统层 | 800G光模块 / 1.6T光模块 / CPO |
| Component | 器件层 | DSP / EML激光器 / VCSEL / 硅光芯片 |
| Material | 材料层 | 硅片 / PCB / 石英 |

## 视图

- **Layer View（默认）**：分层价值链，一眼看清整个产业
- **Graph View（切换）**：关系图，DSP→光模块→交换机→AI服务器

## 公司

公司不是产业链节点，按 Layer → Item → Companies 分组。
浏览模式默认不显示公司，公司模式可展开查看。
