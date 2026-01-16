#!/bin/bash
# Bib-Check 测试脚本

set -e

echo "================================"
echo "Bib-Check 测试脚本"
echo "================================"
echo

# 检查是否安装依赖
if ! python -c "import bibtexparser" 2>/dev/null; then
    echo "[错误] 请先安装依赖: pip install -r requirements.txt"
    exit 1
fi

# 创建测试输出目录
mkdir -p test_output

echo "[测试 1] 仅链接检查"
python bib_check.py examples/sample.bib --check-links
echo

echo "[测试 2] 所有功能（输出到新文件）"
python bib_check.py examples/sample.bib --all --output test_output/sample_cleaned.bib
echo

echo "[测试 3] 指定数据源优先级"
python bib_check.py examples/sample.bib --auto-update --priority semantic-scholar,dblp --dry-run
echo

echo "================================"
echo "所有测试完成！"
echo "================================"
echo
echo "输出文件保存在 test_output/ 目录"
