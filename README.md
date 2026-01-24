# Bib-Check

一个强大的 BibTeX 文件深度检查和自动修复工具。

## ✨ 功能特性

1. **📚 Auto-Update**: 自动检测 arXiv 预印本论文，在 Semantic Scholar、DBLP、Crossref、arXiv、PubMed 查询正式发表版本并更新条目
2. **🔗 Dead Link Check**: 检查 PDF 和 URL 链接的可用性
3. **✅ BibLaTeX 校验**: 检查缺失字段、作者格式、期刊缩写、ID 唯一性、DOI/ISBN/ISSN/年份/页码/URL 格式
4. **🛠️ 自动修复**: 规范化 DOI/URL、页码范围、年份与空白
5. **✂️ 作者截断**: 作者过长时自动截断为 `et. al`
6. **🧾 多格式报告**: 支持 Markdown、JSON、CSV、LaTeX、PDF 和交互式 HTML 报告
7. **🎯 引用过滤**: 可从 `.aux` 文件提取引用，仅检查被引用条目

## 🚀 快速开始

### 安装

```bash
cd /path/to/Bib-Check
pip install -r requirements.txt
```

### 基本用法

```bash
# 启用所有功能（默认不写回 Bib 文件）
python bib_check.py your_file.bib --all

# 先运行 dry-run 查看会有哪些变化
python bib_check.py your_file.bib --all --dry-run
```

## 📖 详细文档

- **[快速开始指南](docs/QUICKSTART.md)**: 详细的使用教程和常见场景
- **[架构文档](docs/ARCHITECTURE.md)**: 项目架构和扩展指南
- **[贡献指南](CONTRIBUTING.md)**: 如何参与项目开发

## 💡 使用示例

### 单独功能

```bash
# 自动更新 arXiv 条目
python bib_check.py input.bib --auto-update

# 检查链接
python bib_check.py input.bib --check-links

# BibLaTeX 字段校验
python bib_check.py input.bib --validate

# 生成 HTML 交互报告
python bib_check.py input.bib --validate --html-report

# 自动修复并预览
python bib_check.py input.bib --auto-fix --fix-preview

# 生成 CSV/LaTeX/PDF 报告
python bib_check.py input.bib --all --csv-report --latex-report --pdf-report
```

### 高级选项

```bash
# 指定输出文件并写回
python bib_check.py input.bib --output cleaned.bib --write-bib

# 配置数据源优先级
python bib_check.py input.bib --auto-update --priority dblp,semantic-scholar

# 使用 .aux 文件过滤引用
python bib_check.py input.bib --validate --aux references.aux

# 使用自定义配置
python bib_check.py input.bib --all --config my_config.yaml
```

## ⚙️ 配置

编辑 `config.yaml` 文件来自定义：

- 作者截断规则
- API 超时和重试参数
- 数据源优先级
- 链接检查配置
- BibLaTeX 校验规则
- 自动修复、缓存与并发

示例配置：

```yaml
sources:
  priority:
    - semantic-scholar
    - dblp

author_truncation:
  max_authors: 3
  suffix: "et. al"

validation:
  check_missing_fields: true
  check_author_format: true
  check_journal_abbrev: true
  check_unique_ids: true
```

## 📊 输出报告

工具会生成彩色控制台报告，并在同目录输出多种格式的报告文件，内容包括：

### 报告格式
- **Markdown** (`.report.md`): 文本格式，便于查看和分享
- **JSON** (`.report.json`): 机器可读格式，便于自动化处理
- **HTML** (`.report.html`): 交互式报告，支持搜索和过滤（使用 `--html-report`）

### 报告内容
- ✅ **更新的条目列表**: arXiv → 正式发表版本
- 🔗 **已出版链接**: 能检索到的正式发表链接
- ⚠️ **失效的链接列表**: 无法访问的 URL
- ✂️ **作者截断**: 过长作者列表 → `et. al`
- ✅ **校验问题**: 缺失字段、作者格式、期刊缩写等
- 📈 **统计信息**: 总体处理结果汇总

## 🧪 测试

运行测试脚本：

```bash
bash scripts/test.sh
```

或查看示例：

```bash
cd examples
python ../bib_check.py sample.bib --all
```

## 📁 项目结构

```
Bib-Check/
├── docs/                 # 文档
│   ├── QUICKSTART.md
│   ├── ARCHITECTURE.md
│   ├── VALIDATION_GUIDE.md
│   └── IMPLEMENTATION_SUMMARY.md
├── scripts/              # 脚本
│   ├── demo.py
│   └── test.sh
├── bib_check.py           # 主入口
├── config.yaml            # 配置文件
├── requirements.txt       # 依赖列表
├── utils/                 # 工具模块
│   ├── bib_parser.py     # BibTeX 解析
│   └── report.py         # 报告生成
├── sources/              # 数据源适配器
│   ├── semantic_scholar.py
│   └── dblp.py
├── checkers/             # 检查器
│   ├── auto_update.py    # 自动更新
│   ├── link_check.py     # 链接检查
│   └── biblatex_validate.py  # BibLaTeX 校验
└── examples/             # 示例文件
    └── sample.bib
```

## 🤝 贡献

欢迎贡献！请查看 [贡献指南](CONTRIBUTING.md)。

常见贡献方式：
- 🐛 报告 bug
- 💡 提出新功能建议
- 📝 改进文档
- ➕ 添加新的校验规则
- ➕ 添加新的作者截断规则
- 🔌 添加新的数据源支持

## 📄 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件

## 🙏 致谢

- [bibtexparser](https://github.com/sciunto-org/python-bibtexparser) - BibTeX 解析
- [Semantic Scholar API](https://www.semanticscholar.org/product/api) - 论文元数据
- [DBLP](https://dblp.org/) - 计算机科学文献数据库
