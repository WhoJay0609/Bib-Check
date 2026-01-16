# Bib-Check

一个强大的 BibTeX 文件深度检查和自动修复工具。

## ✨ 功能特性

1. **📚 Auto-Update**: 自动检测 arXiv 预印本论文，在 Semantic Scholar 或 DBLP 查询正式发表版本并更新条目
2. **🔗 Dead Link Check**: 检查 PDF 和 URL 链接的可用性
3. **✂️ 作者截断**: 作者过长时自动截断为 `et. al`

## 🚀 快速开始

### 安装

```bash
cd /path/to/Bib-Check
pip install -r requirements.txt
```

### 基本用法

```bash
# 启用所有功能（推荐）
python bib_check.py your_file.bib --all

# 先运行 dry-run 查看会有哪些变化
python bib_check.py your_file.bib --all --dry-run
```

## 📖 详细文档

- **[快速开始指南](QUICKSTART.md)**: 详细的使用教程和常见场景
- **[架构文档](ARCHITECTURE.md)**: 项目架构和扩展指南
- **[贡献指南](CONTRIBUTING.md)**: 如何参与项目开发

## 💡 使用示例

### 单独功能

```bash
# 自动更新 arXiv 条目
python bib_check.py input.bib --auto-update

# 检查链接
python bib_check.py input.bib --check-links
```

### 高级选项

```bash
# 指定输出文件
python bib_check.py input.bib --output cleaned.bib

# 配置数据源优先级
python bib_check.py input.bib --auto-update --priority dblp,semantic-scholar

# 使用自定义配置
python bib_check.py input.bib --all --config my_config.yaml
```

## ⚙️ 配置

编辑 `config.yaml` 文件来自定义：

- 作者截断规则
- API 超时和重试参数
- 数据源优先级
- 链接检查配置

示例配置：

```yaml
sources:
  priority:
    - semantic-scholar
    - dblp

author_truncation:
  max_authors: 3
  suffix: "et. al"
```

## 📊 输出报告

工具会生成彩色控制台报告，并在同目录输出一份 JSON 报告文件（默认后缀 `.report.json`），内容包括：

- ✅ **更新的条目列表**: arXiv → 正式发表版本
- ⚠️ **失效的链接列表**: 无法访问的 URL
- ✂️ **作者截断**: 过长作者列表 → `et. al`
- 📈 **统计信息**: 总体处理结果汇总

## 🧪 测试

运行测试脚本：

```bash
bash test.sh
```

或查看示例：

```bash
cd examples
python ../bib_check.py sample.bib --all
```

## 📁 项目结构

```
Bib-Check/
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
│   └── link_check.py     # 链接检查
└── examples/             # 示例文件
    └── sample.bib
```

## 🤝 贡献

欢迎贡献！请查看 [贡献指南](CONTRIBUTING.md)。

常见贡献方式：
- 🐛 报告 bug
- 💡 提出新功能建议
- 📝 改进文档
- ➕ 添加新的作者截断规则
- 🔌 添加新的数据源支持

## 📄 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件

## 🙏 致谢

- [bibtexparser](https://github.com/sciunto-org/python-bibtexparser) - BibTeX 解析
- [Semantic Scholar API](https://www.semanticscholar.org/product/api) - 论文元数据
- [DBLP](https://dblp.org/) - 计算机科学文献数据库
