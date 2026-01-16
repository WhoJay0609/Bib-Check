# 测试样例

本目录包含用于测试 Bib-Check 工具的样例文件。

## sample.bib

这是一个包含各种类型条目的示例 BibTeX 文件：

1. **arXiv 条目**: 可通过 `--auto-update` 查找正式发表版本
2. **含链接条目**: 可通过 `--check-links` 检测失效链接
3. **作者过长条目**: 会触发作者截断（et. al）

## 测试命令

### 测试所有功能

```bash
cd /path/to/Bib-Check
python bib_check.py examples/sample.bib --all --output examples/sample_cleaned.bib
```

### 仅测试自动更新

```bash
python bib_check.py examples/sample.bib --auto-update --dry-run
```

### 仅测试链接检查

```bash
python bib_check.py examples/sample.bib --check-links
```

### 指定数据源优先级

```bash
python bib_check.py examples/sample.bib --auto-update --priority dblp,semantic-scholar
```

## 预期结果

运行完整测试后，你应该看到：

- **更新**: arXiv 条目可能被更新为正式发表版本（如果 API 能找到）
- **作者截断**: 作者过长条目会被截断为 `et. al`
- **失效链接**: 无法访问的链接会被标记为失效
