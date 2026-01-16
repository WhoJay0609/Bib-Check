# 测试样例

本目录包含用于测试 Bib-Sanitizer 工具的样例文件。

## sample.bib

这是一个包含各种类型条目的示例 BibTeX 文件：

1. **example_arxiv_only**: 仅有 arXiv 预印本的条目，可通过 `--auto-update` 查找正式发表版本
2. **example_long_venue_name**: 包含冗长会议名称的条目，可通过 `--format-clean` 统一为简称
3. **example_with_dead_link**: 包含失效链接的条目，可通过 `--check-links` 检测
4. **example_neurips**: NeurIPS 会议论文，会议名称需要统一
5. **example_good_entry**: 格式良好的条目，不需要修改

## 测试命令

### 测试所有功能

```bash
cd /home/hujie/paper/tools/Bib-Sanitizer
python bib_sanitizer.py examples/sample.bib --all --output examples/sample_cleaned.bib
```

### 仅测试自动更新

```bash
python bib_sanitizer.py examples/sample.bib --auto-update --dry-run
```

### 仅测试格式清理

```bash
python bib_sanitizer.py examples/sample.bib --format-clean --dry-run
```

### 仅测试链接检查

```bash
python bib_sanitizer.py examples/sample.bib --check-links
```

### 指定数据源优先级

```bash
python bib_sanitizer.py examples/sample.bib --auto-update --priority dblp,semantic-scholar
```

## 预期结果

运行完整测试后，你应该看到：

- **更新**: `example_arxiv_only` 可能被更新为正式发表版本（如果 API 能找到）
- **格式变更**: `example_long_venue_name` 的 booktitle 被统一为 "CVPR"，`example_neurips` 的 booktitle 被统一为 "NeurIPS"
- **失效链接**: `example_with_dead_link` 的两个链接被标记为失效
- **无变化**: `example_good_entry` 保持不变
