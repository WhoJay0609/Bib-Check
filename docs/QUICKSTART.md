# 快速开始指南

这是一个快速上手 Bib-Check 的指南。

## 1. 安装依赖

```bash
cd /path/to/Bib-Check
pip install -r requirements.txt
```

## 2. 基本使用

### 最简单的用法

对一个 BibTeX 文件运行所有检查和修复（默认不写回 Bib 文件）：

```bash
python bib_check.py your_file.bib --all
```

这会：
- 自动更新 arXiv 条目为正式发表版本
- 自动修复常见字段问题（DOI/URL/页码/年份）
- 作者过长自动截断
- 检查所有链接的可用性
- 校验 BibLaTeX 字段和格式
- 在原文件旁边创建备份（.bak）
- 直接修改原文件（需要 --write-bib）
- 生成多格式报告（Markdown/JSON/HTML/CSV/LaTeX/PDF）

### 安全模式（推荐第一次使用）

使用 `--dry-run` 模式，只查看报告，不修改文件：

```bash
python bib_check.py your_file.bib --all --dry-run
```

### 输出到新文件

如果你想保留原文件不变：

```bash
python bib_check.py input.bib --all --output output.bib --write-bib
```

## 3. 单独功能

### 只校验 BibLaTeX 字段

```bash
python bib_check.py your_file.bib --validate
```

这会检查：
- 缺失的必需字段（根据条目类型）
- 作者格式问题
- 期刊名称缩写
- 重复的条目 ID
- 条目类型一致性
- DOI/ISBN/ISSN/年份/页码/URL 格式

### 只更新 arXiv 条目

```bash
python bib_check.py your_file.bib --auto-update
```

这会查找所有仅有 arXiv 版本的论文，并尝试在 Semantic Scholar、DBLP、Crossref、arXiv 和 PubMed 上找到正式发表版本。

### 只检查链接

```bash
python bib_check.py your_file.bib --check-links
```

这会检查所有 `url` 和 `pdf` 字段的链接是否可访问。

### 只做自动修复

```bash
python bib_check.py your_file.bib --auto-fix --fix-preview
```

`--fix-preview` 会输出修复报告但不写回文件。

## 4. 高级选项

### 指定数据源优先级

默认先查 Semantic Scholar，再查 DBLP。你可以改变顺序：

```bash
python bib_check.py your_file.bib --auto-update --priority dblp,semantic-scholar
```

### 批量/目录处理

```bash
# 处理多个文件并生成汇总报告
python bib_check.py a.bib b.bib --all

# 递归处理目录下所有 .bib 文件
python bib_check.py ./bib_dir --all --recursive

# 使用 glob 模式筛选文件
python bib_check.py ./bib_dir --all --glob "**/*survey*.bib"
```

### 更多报告格式

```bash
python bib_check.py your_file.bib --all --csv-report --latex-report --pdf-report
```

### 使用自定义配置文件

```bash
python bib_check.py your_file.bib --all --config my_config.yaml
```

## 5. 配置文件自定义

编辑 `config.yaml` 文件来：

### 作者截断规则

在 `author_truncation` 部分调整作者截断阈值：

```yaml
author_truncation:
  max_authors: 3
  suffix: "et. al"
```

### 调整超时和重试参数

```yaml
link_check:
  timeout: 15  # 增加超时时间
  retry: 3     # 增加重试次数
```

### 调整 API 配置

```yaml
sources:
  semantic_scholar:
    timeout: 15
    retry: 5
```

### 缓存与并发

```yaml
cache:
  enabled: true
  dir: ".cache/bib-check"
  ttl: 86400
  max_size_mb: 200

concurrency:
  max_workers: 4
```

## 6. 常见使用场景

### 场景 1：论文投稿前清理参考文献

```bash
# 先查看会有哪些变化
python bib_check.py references.bib --all --dry-run

# 确认后执行
python bib_check.py references.bib --all
```

### 场景 2：定期维护文献库

```bash
# 每个月运行一次，更新 arXiv 论文
python bib_check.py my_library.bib --auto-update
```

### 场景 3：检查老旧文献的链接

```bash
# 只检查链接，不修改文件
python bib_check.py old_papers.bib --check-links
```

### 场景 4：投稿前的 BibTeX 质量检查

```bash
# 检查被引用条目的格式规范性
python bib_check.py references.bib --validate --aux main.aux --html-report

# 查看生成的 HTML 报告
firefox references.bib.report.html
```

### 场景 5：团队协作的文献库规范化

```bash
# 全面检查和修复
python bib_check.py team_library.bib --all --html-report

# 团队成员可以通过浏览器查看报告
# 决定哪些问题需要修复
```

## 7. 理解输出

工具会生成控制台报告，并同时输出一份 JSON 报告文件（默认后缀 `.report.json`），包括：

- **[更新]**: 从 arXiv 升级到正式发表的条目列表
- **[作者]**: 作者截断记录
- **[修复]**: 自动修复记录
- **[链接]**: 失效的链接列表
- **[错误]**: 处理过程中的错误（如 API 请求失败）
- **统计信息**: 总体的统计数据

## 8. 故障排除

### 问题：API 请求超时

- 增加配置文件中的 `timeout` 值
- 检查网络连接
- 尝试使用不同的数据源优先级

### 问题：无法解析 BibTeX 文件

- 确保文件是有效的 BibTeX 格式
- 检查文件编码是否为 UTF-8
- 尝试使用其他 BibTeX 工具先验证文件

### 问题：更新后某些字段丢失

- 工具会备份原文件（.bak）
- 查看报告中的具体变更
- 如有问题，从备份恢复

## 9. 示例文件

查看 `examples/` 目录中的示例文件：

```bash
cd examples
python ../bib_check.py sample.bib --all --output sample_cleaned.bib
```

## 10. 获取帮助

查看完整的命令行选项：

```bash
python bib_check.py --help
```
