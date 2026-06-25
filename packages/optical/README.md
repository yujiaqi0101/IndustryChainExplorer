# 光模块产业包（PRD Part 06 统一对象模型）

采用**统一对象模型（Object + Relation + Layout + Package）**架构。

## 目录结构

```
optical/
├── package.yaml          包元信息
├── layout.yaml           分层布局（sections → 对象ID）
├── README.md             本文件
├── objects/              对象（按 kind 分文件）
│   ├── entities.yaml     entity 对象（entity_type 分类）
│   ├── companies.yaml    company 对象
│   ├── references.yaml   reference 对象（研报/年报/白皮书）
│   └── standards.yaml    standard 对象（IEEE/OIF）
├── glossary/             名词解释对象
│   └── terms.yaml        glossary 对象（纯术语）
├── relations/            关系（按 type 分文件）
│   ├── supply.yaml       供应关系
│   ├── use.yaml          使用关系
│   ├── produce.yaml      生产关系
│   └── related_to.yaml   关联关系
└── assets/               资源
```

## 对象（Object）

统一模型，kind 决定类型：
- **entity**（16 个）：application / product / technology / component / material
- **company**（12 个）：中际旭创 / 新易盛 / Marvell / Broadcom ...
- **reference**（4 个）：国盛证券研报 / 中际旭创年报 / NVIDIA年报 / Intel白皮书
- **standard**（2 个）：IEEE 802.3bs / OIF-224G
- **glossary**（4 个）：PAM4 / PAM3 / FEC / BER

对象只描述自己，不存关系。

## 分层（layout.yaml，4 层）

| 层 | 标题 | order | 对象 |
|----|------|-------|------|
| Application | 应用层 | 0 | ai_server / data_center / switch |
| System | 系统层 | 1 | optical_module / optical_module_800g / optical_module_1_6t / cpo |
| Component | 器件层 | 2 | dsp / eml_laser / vcsel / silicon_photonics_chip |
| Material | 材料层 | 3 | silicon_wafer / pcb / quartz |

order 越大越上游。

## 关系（Relation，29 条）

关系独立成对象，绑定 reference（事实需要证据）：
- **supply**（6 条）：dsp/eml_laser/vcsel/pcb/silicon_photonics_chip → optical_module
- **use**（6 条）：ai_server/switch use optical_module；800G/1.6T use dsp/eml/硅光
- **produce**（14 条）：公司生产器件/产品
- **related_to**（3 条）：CPO 关联 硅光/光模块

## Object ID 规范

全部小写、下划线连接、无空格无中文：
dsp / optical_module / optical_module_800g / ai_server / marvell / pam4
