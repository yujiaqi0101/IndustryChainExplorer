# M2 - Knowledge Repository 架构重构实施计划

## 概述

本阶段将项目从"产业链浏览器"升级为"产业知识操作系统（Industry Knowledge OS）"，核心是从 Package-centric 架构转向 Knowledge-centric 架构。

**核心思想**：Repository 保存事实（Facts），Package 只是观察事实的视角（View）。

---

## 架构总览

### 三层架构

```
Knowledge Layer          →  objects/, facts/, references/, taxonomy/, ontology/
Presentation Layer       →  packages/ (entry points, layouts, themes)
Application Layer        →  ice/ pipeline, services, CLI, API
```

### 启动 Pipeline

```
Discovery → Load → Parse → Validate(5层) → Link → Index → Build Graph → Ready
```

---

## 任务清单

### Phase 0: 分支准备
- [ ] 提交当前 M1 代码到 main 分支并推送远端
- [ ] 创建新分支 `Knowledge Repository`
- [ ] 清理旧代码目录（chains/, models/, repository/, search/, services/, ui/, lib/）

### Phase 1: 目录结构创建
- [ ] 创建 `knowledge/` 目录
  - [ ] `knowledge/objects/` - 所有对象（按 kind 分子目录？不，扁平存储，每个对象一个YAML）
  - [ ] `knowledge/facts/` - 所有事实（三元组）
  - [ ] `knowledge/references/` - 所有证据文献
  - [ ] `knowledge/media/` - 媒体资源
- [ ] 创建 `ontology/` 目录
  - [ ] `ontology/taxonomy.yaml` - 分类体系
  - [ ] `ontology/predicates.yaml` - 谓词定义及约束
  - [ ] `ontology/validation.yaml` - 验证规则
- [ ] 重构 `packages/` 目录
  - [ ] Package 只保留 package.yaml（入口点、layout、theme）
  - [ ] 移除 objects/ 和 relations/ 目录
- [ ] 重构 `ice/` 目录
  - [ ] `ice/models/` - 核心领域模型
  - [ ] `ice/ontology/` - Ontology 加载与约束检查
  - [ ] `ice/pipeline/` - Pipeline 各 Stage 实现
  - [ ] `ice/repository/` - Knowledge Repository 实现
  - [ ] `ice/services/` - 图服务、搜索服务
  - [ ] `ice/cli.py` - 命令行入口
  - [ ] `ice/renderer/` - 渲染器

### Phase 2: 核心模型实现

#### 2.1 Object 模型
三种 Kind：
- **concept** - 产业概念（光模块、DSP、VCSEL、AI服务器、PAM4等）
- **organization** - 组织（Marvell、Broadcom、中际旭创、Cisco、IEEE等）
- **document** - 文献（研报、年报、标准文档等）

Object 字段：
```yaml
id: dsp                    # 语义化ID，一旦发布不可修改
kind: concept              # concept/organization/document
name: DSP                  # 显示名称
aliases:                   # 别名，用于搜索
  - Digital Signal Processor
summary: 数字信号处理器     # 简介
tags: [芯片, 光通信]        # 标签
deprecated_ids: []         # 废弃ID映射
created_at: 2026-06-26
updated_at: 2026-06-26
```

Organization 扩展字段：
- organization_type: company / research_institute / standard_org / ...
- code: 股票代码
- market: 上市市场

Document 扩展字段：
- document_type: research_report / annual_report / standard / ...
- title: 文档标题
- author: 作者
- published_date: 发布日期
- source_url: 来源链接

> **重要**：Object 不再有 type/entity_type 字段！分类通过 Fact 的 `is_a` 谓词表达。

#### 2.2 Fact 模型（原 Relation）
三元组模型（Subject-Predicate-Object）：

```yaml
id: fact_00001
subject: dsp               # 主体 Object ID
predicate: supply          # 谓词
object: optical_module     # 客体 Object ID
statement: DSP是800G光模块的核心芯片  # 自然语言陈述
qualifiers:                # 限定符（扩展点）
  bandwidth: 800G
  year: 2026
citations:                 # 引用证据（reference对象ID列表）
  - ref_gs2025
weight: 0.9                # 关系强度（可选）
created_at: 2026-06-26
updated_at: 2026-06-26
```

#### 2.3 Ontology 模型

**predicates.yaml** - 谓词定义及约束：
```yaml
predicates:
  is_a:
    name: 属于
    subject: [concept, organization, document]
    object: [concept]  # taxonomy category也是concept
    inverse: has_instance
  part_of:
    name: 是...的一部分
    subject: [concept]
    object: [concept]
    inverse: contains
  contains:
    name: 包含
    subject: [concept]
    object: [concept]
    inverse: part_of
  produce:
    name: 生产
    subject: [organization]
    object: [concept]
    inverse: produced_by
  produced_by:
    name: 由...生产
    subject: [concept]
    object: [organization]
    inverse: produce
  supply:
    name: 供应
    subject: [concept, organization]
    object: [concept]
    inverse: supplied_by
  supplied_by:
    name: 由...供应
    subject: [concept]
    object: [concept, organization]
    inverse: supply
  use:
    name: 使用
    subject: [concept, organization]
    object: [concept]
    inverse: used_by
  used_by:
    name: 被...使用
    subject: [concept]
    object: [concept, organization]
    inverse: use
  apply_to:
    name: 应用于
    subject: [concept, technology]
    object: [concept, product]
    inverse: applies
  replace:
    name: 替代
    subject: [concept]
    object: [concept]
    inverse: replaced_by
  compete_with:
    name: 与...竞争
    subject: [concept, organization]
    object: [concept, organization]
    symmetric: true
  depends_on:
    name: 依赖
    subject: [concept]
    object: [concept]
  defined_by:
    name: 由...定义
    subject: [concept]
    object: [document]
  published_by:
    name: 由...发布
    subject: [document]
    object: [organization]
  research_on:
    name: 研究
    subject: [organization]
    object: [concept]
  related_to:
    name: 相关
    subject: [concept, organization, document]
    object: [concept, organization, document]
    symmetric: true
```

**taxonomy.yaml** - 分类体系：
```yaml
categories:
  # 产业分类
  industry:
    name: 产业
    parent: null
  communication:
    name: 通信
    parent: industry
  optical_communication:
    name: 光通信
    parent: communication
  
  # 技术/产品/材料/应用分类
  technology:
    name: 技术
    parent: null
  component:
    name: 器件
    parent: null
  semiconductor:
    name: 半导体
    parent: component
  material:
    name: 材料
    parent: null
  product:
    name: 产品
    parent: null
  application:
    name: 应用
    parent: null
  
  # 组织类型
  organization_type:
    name: 组织类型
    parent: null
  company:
    name: 公司
    parent: organization_type
  research_institute:
    name: 研究机构
    parent: organization_type
  standard_organization:
    name: 标准组织
    parent: organization_type
  
  # 文献类型
  document_type:
    name: 文献类型
    parent: null
  research_report:
    name: 研报
    parent: document_type
  annual_report:
    name: 年报
    parent: document_type
  standard:
    name: 标准
    parent: document_type
```

#### 2.4 Package 模型（视图）
Package 不再拥有知识，只是观察视角：

```yaml
id: optical
name: 光模块产业链
version: 1.0.0
description: 光模块产业链知识库
entry_points:               # 入口对象（浏览起点）
  - optical_module
default_layout: layered     # 默认布局方式
layers:                     # Layer 布局配置
  - id: application
    name: 应用层
    categories: [application]
  - id: product
    name: 产品层
    categories: [product]
  - id: component
    name: 器件层
    categories: [component, semiconductor]
  - id: material
    name: 材料层
    categories: [material]
theme: blue                 # 主题
keywords: [光模块, 光通信, DSP]
```

### Phase 3: Pipeline 架构实现

#### 3.1 BootstrapContext
```python
class BootstrapContext:
    # 发现阶段
    manifest: FileManifest
    # Ontology
    ontology: Ontology
    # 原始数据
    raw_objects: dict[str, dict]
    raw_facts: dict[str, dict]
    raw_references: dict[str, dict]
    raw_packages: dict[str, dict]
    # 解析后
    objects: dict[str, Object]
    facts: dict[str, Fact]
    references: dict[str, Object]
    packages: dict[str, Package]
    # 索引
    indexes: SearchIndexes
    # 图
    graph: KnowledgeGraph
    # 报告
    validation_report: ValidationReport
    # 统计
    stats: dict[str, Any]
```

#### 3.2 Stage 接口
```python
class PipelineStage(Protocol):
    name: str
    def run(self, ctx: BootstrapContext) -> BootstrapContext: ...
```

#### 3.3 各 Stage 实现

| Stage | 职责 |
|-------|------|
| **DiscoverStage** | 扫描目录，生成文件 Manifest（objects/facts/references/packages/ontology） |
| **LoadStage** | 读取所有 YAML 文件为 Python dict |
| **OntologyLoadStage** | 加载 taxonomy.yaml 和 predicates.yaml，构建 Ontology 对象 |
| **ParseStage** | 将 dict 解析为 Pydantic 模型（Object/Fact/Package） |
| **ValidateStage** | 执行五层验证（见下文） |
| **LinkStage** | 将 Fact 中的 subject/object 字符串ID替换为 Object 引用 |
| **IndexStage** | 构建搜索索引（ID索引、Alias索引、Name索引、Tag索引） |
| **GraphStage** | 构建知识图谱邻接表 |
| **CacheStage** | （可选）序列化缓存到磁盘 |

#### 3.4 五层 Validator 实现

| 层级 | 验证内容 | 错误级别 |
|------|---------|---------|
| **Schema Validator** | 字段存在、类型正确、必填项、ID格式 | ERROR |
| **Ontology Validator** | Predicate存在、Subject/Object类型符合约束、非法谓词 | ERROR |
| **Reference Validator** | Object存在、Predicate存在、Citation存在 | ERROR |
| **Business Validator** | 禁止自引用、禁止重复Fact、禁止循环part_of | ERROR |
| **Quality Validator** | Summary过短、无Citation、无Alias、输出质量评分 | WARNING/INFO |

#### 3.5 ValidationReport
收集所有错误/警告/信息，不立即退出：
```python
class ValidationReport:
    errors: list[ValidationIssue]
    warnings: list[ValidationIssue]
    infos: list[ValidationIssue]
    
    def has_errors(self) -> bool: ...
    def error_count(self) -> int: ...
    def warning_count(self) -> int: ...
    def quality_score(self) -> int:  # 0-100
```

### Phase 4: 数据迁移（手动整理）

将现有 `packages/optical/` 下的数据手动迁移到新结构：

1. **knowledge/objects/** - 每个对象一个YAML文件
   - 现有 entities.yaml 拆分为独立文件
   - 现有 companies.yaml 拆分为独立文件（kind=organization）
   - 现有 references.yaml 和 standards.yaml 拆分为独立文件（kind=document）
   - 现有 glossary/terms.yaml 拆分为独立文件（kind=concept）

2. **knowledge/facts/** - 每个Fact一个YAML文件
   - 现有 relations/*.yaml 转换为 Fact 三元组格式
   - 为实体添加 `is_a` Fact 来表达分类（替代原来的 entity_type）
   - 添加 statement 自然语言描述
   - 保留 citations 引用

3. **ontology/** - 创建 taxonomy.yaml 和 predicates.yaml

4. **packages/optical/** - 重构为视图配置
   - 重写 package.yaml，只保留 entry_points、layers、theme
   - 保留 layout.yaml
   - 删除 objects/ 和 relations/ 目录

### Phase 5: 服务层与API更新

- [ ] KnowledgeRepository - 提供对象/Fact查询接口
- [ ] GraphService - 图遍历、上下游查询
- [ ] SearchService - 基于Index的搜索
- [ ] CLI 更新 - 适配新架构
- [ ] FastAPI 更新 - 适配新架构
- [ ] Renderer 更新 - Markdown/图数据渲染

### Phase 6: 测试
- [ ] 单元测试覆盖所有模型
- [ ] 单元测试覆盖每个 Pipeline Stage
- [ ] 单元测试覆盖五层 Validator
- [ ] 集成测试：完整 Pipeline 运行
- [ ] 测试数据迁移后的完整性
- [ ] 所有现有测试更新并通过

---

## Check List（验收标准）

### 架构合规性
- [ ] 目录结构符合三层架构（Knowledge/Presentation/Application）
- [ ] Object 只有 3 种 kind：concept / organization / document
- [ ] Object 没有 type/entity_type 字段，分类通过 is_a Fact 表达
- [ ] Fact 使用三元组（subject-predicate-object）模型
- [ ] Fact 有 statement、qualifiers、citations 字段
- [ ] Ontology 从 ontology/ 目录加载，包含 taxonomy 和 predicates
- [ ] Predicate 带有 subject/object 类型约束
- [ ] Package 不包含 objects/relations，只含视图配置

### Pipeline 合规性
- [ ] 启动流程严格按 8 个 Stage 执行
- [ ] BootstrapContext 在各 Stage 间传递
- [ ] DiscoverStage 先生成 Manifest 再加载
- [ ] Loader 只做 YAML → dict，不做验证
- [ ] Parser 做 dict → Pydantic，只检查Schema
- [ ] Validator 分五层执行
- [ ] LinkStage 建立对象引用
- [ ] IndexStage 建立独立搜索索引
- [ ] GraphStage 最后构建图

### 验证合规性
- [ ] Schema/Ontology/Reference/Business/Quality 五层验证全部实现
- [ ] ValidationReport 收集所有问题，不提前终止
- [ ] 错误/警告/信息分级
- [ ] 质量评分输出（0-100）
- [ ] 禁止自引用、重复Fact、非法循环

### 数据合规性
- [ ] optical 产业包所有对象迁移完成
- [ ] 所有关系转换为 Fact 格式
- [ ] 分类通过 is_a Fact 表达
- [ ] 每个 Fact 有 statement 字段
- [ ] Citations 正确引用 document 对象

### 测试合规性
- [ ] 所有模型有单元测试
- [ ] 所有 Pipeline Stage 有单元测试
- [ ] 五层 Validator 都有测试用例
- [ ] 完整 Pipeline 集成测试通过
- [ ] CLI 命令正常工作
- [ ] API 服务正常启动
