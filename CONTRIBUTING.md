# 贡献指南

感谢你对 Bib-Check 的兴趣！

## 如何贡献

### 报告问题

如果你发现了 bug 或有功能建议：

1. 检查是否已有相关的 issue
2. 创建新 issue 时请提供：
   - 详细的问题描述
   - 复现步骤
   - 预期行为和实际行为
   - 你的环境信息（Python 版本、操作系统等）

### 提交代码

1. Fork 这个仓库
2. 创建你的特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交你的改动 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启一个 Pull Request

### 代码规范

- 使用 Python 3.7+ 的特性
- 遵循 PEP 8 编码规范
- 添加必要的注释和文档字符串
- 为新功能添加测试用例

### 调整作者截断规则

如果你想修改作者截断规则：

1. 编辑 `config.yaml` 文件
2. 调整 `author_truncation` 配置
3. 运行测试验证效果

示例：

```yaml
author_truncation:
  max_authors: 4
  suffix: "et. al"
```

### 添加新的数据源

如果你想添加新的论文数据源（如 Google Scholar、CrossRef 等）：

1. 在 `sources/` 目录创建新的 API 适配器
2. 实现 `search_paper()` 方法
3. 返回标准化的结果格式
4. 更新 `config.yaml` 添加新数据源配置
5. 在 `checkers/auto_update.py` 中注册新数据源

### 测试

在提交前请运行测试：

```bash
bash test.sh
```

## 开发环境设置

1. 克隆仓库
2. 安装依赖：`pip install -r requirements.txt`
3. 进行你的修改
4. 运行测试确保一切正常

## 行为准则

- 尊重他人
- 建设性的反馈
- 专注于项目目标
- 保持友好和专业

## 许可证

通过贡献代码，你同意你的贡献将在 MIT 许可证下发布。
