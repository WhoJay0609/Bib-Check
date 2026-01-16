# 项目架构

本文档描述 Bib-Sanitizer 的架构设计。

## 整体架构

```
┌─────────────────────────────────────────────────────────┐
│                    bib_sanitizer.py                     │
│                      (主入口)                            │
└──────────────────────┬──────────────────────────────────┘
                       │
           ┌───────────┼───────────┐
           │           │           │
           ▼           ▼           ▼
    ┌──────────┐ ┌──────────┐ ┌──────────┐
    │  utils   │ │ sources  │ │ checkers │
    └──────────┘ └──────────┘ └──────────┘
```

## 模块说明

### 1. 主入口 (bib_sanitizer.py)

- **职责**：命令行参数解析、流程控制、配置管理
- **主要类**：`BibSanitizer`
- **流程**：解析 → 检查/修复 → 报告 → 写回

### 2. 工具模块 (utils/)

#### utils/bib_parser.py
- **职责**：BibTeX 文件的解析和写入
- **主要类**：`BibParser`
- **依赖**：`bibtexparser` 库

#### utils/report.py
- **职责**：收集和展示处理结果
- **主要类**：`Report`
- **功能**：
  - 记录更新、格式变更、失效链接
  - 生成可读的控制台报告
  - 支持导出为 JSON 格式

### 3. 数据源模块 (sources/)

#### sources/semantic_scholar.py
- **职责**：Semantic Scholar API 交互
- **主要类**：`SemanticScholarAPI`
- **功能**：
  - 通过 arXiv ID 或标题搜索论文
  - 识别正式发表版本
  - 提取标准化的元数据

#### sources/dblp.py
- **职责**：DBLP API 交互
- **主要类**：`DBLPAPI`
- **功能**：
  - 通过标题或 arXiv ID 搜索论文
  - 解析 XML 响应
  - 返回标准化结果

**扩展点**：添加新数据源只需：
1. 创建新的 API 适配器类
2. 实现 `search_paper(title, arxiv_id)` 方法
3. 返回标准化的结果字典

### 4. 检查器模块 (checkers/)

#### checkers/auto_update.py
- **职责**：自动更新 arXiv 条目
- **主要类**：`AutoUpdater`
- **流程**：
  1. 识别 arXiv-only 条目
  2. 按配置的优先级查询数据源
  3. 更新条目字段（venue、year、DOI 等）
  4. 移除 arXiv 特定字段

#### checkers/format_clean.py
- **职责**：统一会议名称格式
- **主要类**：`FormatCleaner`
- **流程**：
  1. 读取配置的映射规则
  2. 对每个条目的 venue 字段应用规则
  3. 支持精确匹配和正则匹配

#### checkers/link_check.py
- **职责**：检查链接可用性
- **主要类**：`LinkChecker`
- **流程**：
  1. 收集所有 URL 和 PDF 链接
  2. 先尝试 HEAD 请求，失败则用 GET
  3. 支持重试和超时配置
  4. 记录失效链接

## 数据流

```
输入文件 (.bib)
    │
    ▼
┌────────────┐
│ BibParser  │ 解析
└─────┬──────┘
      │
      ▼
┌────────────────────────┐
│  BibDatabase 对象      │
│  (entries 列表)        │
└──────┬─────────────────┘
       │
       ▼
┌──────────────────┐
│  AutoUpdater     │ 功能 1
│  - 识别 arXiv    │
│  - 查询 API      │
│  - 更新字段      │
└──────┬───────────┘
       │
       ▼
┌──────────────────┐
│  FormatCleaner   │ 功能 2
│  - 应用映射规则  │
│  - 统一格式      │
└──────┬───────────┘
       │
       ▼
┌──────────────────┐
│  LinkChecker     │ 功能 3
│  - 收集链接      │
│  - 发送请求      │
│  - 记录结果      │
└──────┬───────────┘
       │
       ▼
┌────────────┐
│   Report   │ 生成报告
└─────┬──────┘
      │
      ▼
┌────────────┐
│ BibParser  │ 写回
└─────┬──────┘
      │
      ▼
输出文件 (.bib)
```

## 配置系统

配置文件 (`config.yaml`) 采用层级结构：

```yaml
sources:          # 数据源配置
  priority: []    # 查询优先级
  semantic_scholar: {}
  dblp: {}

link_check:       # 链接检查配置
  timeout: 10
  retry: 2

venue_mappings:   # 会议名称映射
  - patterns: []
    standard: ""

output:           # 输出配置
  backup: true
  backup_suffix: ".bak"
```

## 错误处理

- **API 失败**：自动重试，记录到报告
- **解析错误**：返回 None，继续处理其他条目
- **网络超时**：配置超时时间和重试次数
- **文件写入失败**：保留备份，不覆盖原文件

## 扩展性设计

### 添加新功能

1. 在 `checkers/` 创建新的检查器类
2. 实现主要的处理方法
3. 在 `bib_sanitizer.py` 中集成
4. 添加命令行参数
5. 更新配置文件

### 添加新数据源

1. 在 `sources/` 创建新的 API 适配器
2. 实现标准接口
3. 在 `checkers/auto_update.py` 注册
4. 更新配置文件

### 自定义输出格式

修改 `utils/report.py` 的 `print_report()` 方法，或添加新的导出方法（如 JSON、CSV）。

## 性能考虑

- **批量处理**：使用 `tqdm` 显示进度
- **API 限流**：支持配置速率限制
- **并发请求**：未来可以添加异步支持
- **缓存**：未来可以添加 API 响应缓存

## 依赖管理

核心依赖：
- `bibtexparser`: BibTeX 解析
- `requests`: HTTP 请求
- `pyyaml`: 配置文件解析
- `colorama`: 彩色输出
- `tqdm`: 进度条

## 测试策略

- **单元测试**：测试各个模块的功能
- **集成测试**：测试完整的处理流程
- **示例测试**：使用 `examples/sample.bib` 测试
- **回归测试**：确保更新不破坏现有功能
