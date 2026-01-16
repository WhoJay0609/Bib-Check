# 快速开始指南

这是一个快速上手 Bib-Sanitizer 的指南。

## 1. 安装依赖

```bash
cd /home/hujie/paper/tools/Bib-Sanitizer
pip install -r requirements.txt
```

## 2. 基本使用

### 最简单的用法

对一个 BibTeX 文件运行所有检查和修复：

```bash
python bib_sanitizer.py your_file.bib --all
```

这会：
- 自动更新 arXiv 条目为正式发表版本
- 统一会议名称格式
- 检查所有链接的可用性
- 在原文件旁边创建备份（.bak）
- 直接修改原文件

### 安全模式（推荐第一次使用）

使用 `--dry-run` 模式，只查看报告，不修改文件：

```bash
python bib_sanitizer.py your_file.bib --all --dry-run
```

### 输出到新文件

如果你想保留原文件不变：

```bash
python bib_sanitizer.py input.bib --all --output output.bib
```

## 3. 单独功能

### 只更新 arXiv 条目

```bash
python bib_sanitizer.py your_file.bib --auto-update
```

这会查找所有仅有 arXiv 版本的论文，并尝试在 Semantic Scholar 和 DBLP 上找到正式发表版本。

### 只统一会议名称

```bash
python bib_sanitizer.py your_file.bib --format-clean
```

这会将长的会议名称（如 "Proceedings of the IEEE/CVF Conference on..."）统一为简称（如 "CVPR"）。

### 只检查链接

```bash
python bib_sanitizer.py your_file.bib --check-links
```

这会检查所有 `url` 和 `pdf` 字段的链接是否可访问。

## 4. 高级选项

### 指定数据源优先级

默认先查 Semantic Scholar，再查 DBLP。你可以改变顺序：

```bash
python bib_sanitizer.py your_file.bib --auto-update --priority dblp,semantic-scholar
```

### 使用自定义配置文件

```bash
python bib_sanitizer.py your_file.bib --all --config my_config.yaml
```

## 5. 配置文件自定义

编辑 `config.yaml` 文件来：

### 添加更多会议名称映射

在 `venue_mappings` 部分添加新规则：

```yaml
venue_mappings:
  - patterns:
      - "Your Conference Full Name"
      - "Another Variant"
    standard: "YourConf"
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

## 6. 常见使用场景

### 场景 1：论文投稿前清理参考文献

```bash
# 先查看会有哪些变化
python bib_sanitizer.py references.bib --all --dry-run

# 确认后执行
python bib_sanitizer.py references.bib --all
```

### 场景 2：定期维护文献库

```bash
# 每个月运行一次，更新 arXiv 论文
python bib_sanitizer.py my_library.bib --auto-update
```

### 场景 3：清理从不同来源合并的文献

```bash
# 统一格式
python bib_sanitizer.py merged.bib --format-clean
```

### 场景 4：检查老旧文献的链接

```bash
# 只检查链接，不修改文件
python bib_sanitizer.py old_papers.bib --check-links
```

## 7. 理解输出

工具会生成一个详细的报告，包括：

- **[更新]**: 从 arXiv 升级到正式发表的条目列表
- **[格式]**: 统一格式的变更列表
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
python ../bib_sanitizer.py sample.bib --all --output sample_cleaned.bib
```

## 10. 获取帮助

查看完整的命令行选项：

```bash
python bib_sanitizer.py --help
```
