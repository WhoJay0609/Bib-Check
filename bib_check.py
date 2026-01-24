#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
bib-check: BibTeX 文件深度检查和自动修复工具
"""

import argparse
import sys
import os
import shutil
from pathlib import Path
import yaml
from colorama import init, Fore, Style

from utils.bib_parser import BibParser
from utils.report import Report, SummaryReport
from checkers.auto_update import AutoUpdater
from checkers.link_check import LinkChecker
from checkers.biblatex_validate import BibLaTeXValidator
from checkers.auto_fix import AutoFixer

# 初始化 colorama
init(autoreset=True)


class BibSanitizer:
    """主控制类"""
    
    def __init__(self, config_path='config.yaml'):
        """初始化"""
        self.config = self._load_config(config_path)
        self.report = Report()
    
    def _load_config(self, config_path):
        """加载配置文件"""
        if not os.path.exists(config_path):
            # 使用默认配置
            return self._default_config()
        
        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    
    def _default_config(self):
        """默认配置"""
        return {
            'sources': {
                'priority': ['semantic-scholar', 'dblp', 'crossref', 'arxiv', 'pubmed'],
                'semantic_scholar': {
                    'base_url': 'https://api.semanticscholar.org/graph/v1',
                    'timeout': 10,
                    'retry': 3,
                    'rate_limit': 100
                },
                'dblp': {
                    'base_url': 'https://dblp.org/search/publ/api',
                    'timeout': 10,
                    'retry': 3,
                    'rate_limit': 60
                },
                'crossref': {
                    'base_url': 'https://api.crossref.org',
                    'timeout': 10,
                    'retry': 3,
                    'rate_limit': 60,
                    'mailto': ''
                },
                'arxiv': {
                    'base_url': 'http://export.arxiv.org/api/query',
                    'timeout': 10,
                    'retry': 3,
                    'rate_limit': 30
                },
                'pubmed': {
                    'base_url': 'https://eutils.ncbi.nlm.nih.gov/entrez/eutils',
                    'timeout': 10,
                    'retry': 3,
                    'rate_limit': 60,
                    'email': '',
                    'tool': 'bib-check'
                }
            },
            'link_check': {
                'timeout': 10,
                'retry': 2
            },
            'author_truncation': {
                'max_authors': 3,
                'suffix': 'et. al'
            },
            'auto_fix': {
                'fix_doi': True,
                'fix_url': True,
                'fix_pages': True,
                'fix_year': True,
                'fix_whitespace': True
            },
            'cache': {
                'enabled': False,
                'dir': '.cache/bib-check',
                'ttl': 86400,
                'max_size_mb': 200
            },
            'concurrency': {
                'max_workers': 4
            },
            'output': {
                'backup': True,
                'backup_suffix': '.bak',
                'report_suffix': '.report.json',
                'report_md_suffix': '.report.md',
                'report_csv_suffix': '.report.csv',
                'report_tex_suffix': '.report.tex',
                'report_pdf_suffix': '.report.pdf',
                'summary_suffix': '.summary.json',
                'summary_md_suffix': '.summary.md'
            },
            'validation': {
                'check_missing_fields': True,
                'check_author_format': True,
                'check_journal_abbrev': True,
                'check_unique_ids': True,
                'check_type_consistency': True,
                'check_doi_format': True,
                'check_isbn_issn_format': True,
                'check_year_range': True,
                'check_pages_format': True,
                'check_url_format': True,
                'year_min': 1900,
                'year_max': 2100
            }
        }
    
    def process_file(self, input_file, output_file=None,
                    auto_update=False,
                    check_links=False, validate=False, dry_run=False, priority=None,
                    write_bib=False, aux_file=None, html_report=False,
                    auto_fix=False, fix_preview=False,
                    csv_report=False, latex_report=False, pdf_report=False):
        """处理 BibTeX 文件"""
        self.report = Report()
        if fix_preview:
            dry_run = True
        print(f"{Fore.CYAN}[信息] 正在处理文件: {input_file}{Style.RESET_ALL}")
        
        # 解析 BibTeX 文件
        parser = BibParser()
        bib_database = parser.parse_file(input_file)
        
        if bib_database is None:
            print(f"{Fore.RED}[错误] 无法解析文件: {input_file}{Style.RESET_ALL}")
            return False
        
        print(f"{Fore.GREEN}[成功] 找到 {len(bib_database.entries)} 个条目{Style.RESET_ALL}")
        
        # 如果指定了优先级，更新配置
        if priority:
            self.config['sources']['priority'] = priority.split(',')
        
        # 解析 .aux 文件（如果提供）
        used_ids = None
        if aux_file:
            print(f"\n{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
            print(f"{Fore.CYAN}[引用过滤] 从 .aux 文件提取引用{Style.RESET_ALL}")
            print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
            used_ids = self._extract_citations_from_aux(aux_file)
            if used_ids:
                print(f"{Fore.GREEN}[信息] 从 {aux_file} 提取到 {len(used_ids)} 个引用{Style.RESET_ALL}")
            else:
                print(f"{Fore.YELLOW}[警告] 未能从 {aux_file} 提取引用{Style.RESET_ALL}")
        
        # 功能 1: Auto-Update
        if auto_update:
            print(f"\n{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
            print(f"{Fore.CYAN}[功能 1] 自动更新 arXiv 条目{Style.RESET_ALL}")
            print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
            
            updater = AutoUpdater(self.config, self.report)
            bib_database = updater.update_entries(bib_database)
        
        # 功能 2: 自动修复
        auto_fixed = False
        if auto_fix:
            print(f"\n{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
            print(f"{Fore.CYAN}[功能 2] 自动修复常见问题{Style.RESET_ALL}")
            print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
            fixer = AutoFixer(self.config, self.report)
            auto_fixed = fixer.fix_entries(bib_database, apply=not fix_preview)

        # 功能 3: Dead Link Check
        if check_links:
            print(f"\n{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
            print(f"{Fore.CYAN}[功能 3] 检查链接可用性{Style.RESET_ALL}")
            print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
            
            checker = LinkChecker(self.config, self.report)
            checker.check_entries(bib_database)
        
        # 功能 4: BibLaTeX 校验
        if validate:
            print(f"\n{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
            print(f"{Fore.CYAN}[功能 4] BibLaTeX 字段校验{Style.RESET_ALL}")
            print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
            
            validator = BibLaTeXValidator(self.config, self.report)
            validator.validate_entries(bib_database, used_ids)

        # 作者截断（默认启用）
        print(f"\n{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}[功能 5] 作者截断{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
        authors_changed = self._truncate_authors(bib_database)
        
        # 写回文件（默认不输出新 Bib 文件）
        if write_bib and not dry_run and (auto_update or authors_changed or auto_fixed):
            if output_file is None:
                output_file = input_file
                # 备份原文件
                if self.config['output'].get('backup', True):
                    backup_file = input_file + self.config['output'].get('backup_suffix', '.bak')
                    shutil.copy2(input_file, backup_file)
                    print(f"\n{Fore.YELLOW}[备份] 原文件已备份至: {backup_file}{Style.RESET_ALL}")
            
            parser.write_file(bib_database, output_file)
            print(f"\n{Fore.GREEN}[成功] 已写入文件: {output_file}{Style.RESET_ALL}")
        
        # 生成报告
        print(f"\n{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}执行报告{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
        self.report.print_report()

        # 写入 JSON 报告
        report_target = output_file or input_file
        report_suffix = self.config.get('output', {}).get('report_suffix', '.report.json')
        report_path = f"{report_target}{report_suffix}"
        self.report.write_json(report_path)
        print(f"\n{Fore.GREEN}[报告] 已写入: {report_path}{Style.RESET_ALL}")

        # 写入 Markdown 报告
        report_md_suffix = self.config.get('output', {}).get('report_md_suffix', '.report.md')
        report_md_path = f"{report_target}{report_md_suffix}"
        self.report.write_markdown(report_md_path)
        print(f"{Fore.GREEN}[报告] 已写入: {report_md_path}{Style.RESET_ALL}")
        
        # 写入 HTML 报告（如果启用）
        if html_report:
            html_suffix = self.config.get('output', {}).get('html_report_suffix', '.report.html')
            html_path = f"{report_target}{html_suffix}"
            self.report.write_html(html_path, input_file)
            print(f"{Fore.GREEN}[报告] 已写入: {html_path}{Style.RESET_ALL}")

        # 写入 CSV 报告
        if csv_report:
            csv_suffix = self.config.get('output', {}).get('report_csv_suffix', '.report.csv')
            csv_path = f"{report_target}{csv_suffix}"
            self.report.write_csv(csv_path)
            print(f"{Fore.GREEN}[报告] 已写入: {csv_path}{Style.RESET_ALL}")

        # 写入 LaTeX 报告
        if latex_report:
            tex_suffix = self.config.get('output', {}).get('report_tex_suffix', '.report.tex')
            tex_path = f"{report_target}{tex_suffix}"
            self.report.write_latex(tex_path)
            print(f"{Fore.GREEN}[报告] 已写入: {tex_path}{Style.RESET_ALL}")

        # 写入 PDF 报告
        if pdf_report:
            pdf_suffix = self.config.get('output', {}).get('report_pdf_suffix', '.report.pdf')
            pdf_path = f"{report_target}{pdf_suffix}"
            self.report.write_pdf(pdf_path)
            print(f"{Fore.GREEN}[报告] 已写入: {pdf_path}{Style.RESET_ALL}")
        
        return True

    def _truncate_authors(self, bib_database):
        """作者过长时截断为 et. al"""
        config = self.config.get('author_truncation', {})
        max_authors = int(config.get('max_authors', 3))
        suffix = config.get('suffix', 'et. al')

        if max_authors < 1:
            return False

        changed = False
        for entry in bib_database.entries:
            if 'author' not in entry:
                continue

            raw_authors = entry['author']
            authors = [a.strip() for a in raw_authors.split(' and ') if a.strip()]

            if len(authors) > max_authors:
                new_value = f"{authors[0]} {suffix}"
                entry['author'] = new_value
                changed = True
                self.report.add_author_truncation(
                    entry.get('ID', 'unknown'),
                    raw_authors,
                    new_value,
                    len(authors),
                    max_authors
                )
        return changed
    
    def _extract_citations_from_aux(self, aux_file):
        """从 .aux 文件提取引用的条目 ID"""
        if not os.path.exists(aux_file):
            print(f"{Fore.YELLOW}[警告] .aux 文件不存在: {aux_file}{Style.RESET_ALL}")
            return None
        
        used_ids = set()
        try:
            with open(aux_file, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.startswith('\\citation'):
                        # 提取 \citation{entry1,entry2,...}
                        content = line.split('{')[1].rstrip('} \n')
                        entry_ids = [e.strip() for e in content.split(',') if e.strip()]
                        used_ids.update(entry_ids)
        except Exception as e:
            print(f"{Fore.RED}[错误] 读取 .aux 文件失败: {e}{Style.RESET_ALL}")
            return None
        
        return used_ids


def _collect_input_files(inputs, recursive=False, glob_pattern=None):
    """收集输入文件列表"""
    files = []
    for item in inputs:
        path = Path(item)
        if path.is_dir():
            patterns = []
            if glob_pattern:
                patterns = [glob_pattern]
            else:
                patterns = ['**/*.bib', '**/*.tex'] if recursive else ['*.bib', '*.tex']
            for pattern in patterns:
                for file_path in path.glob(pattern):
                    if file_path.is_file():
                        files.append(str(file_path))
        else:
            files.append(str(path))
    # 去重并保留顺序
    seen = set()
    unique_files = []
    for file_path in files:
        if file_path not in seen:
            seen.add(file_path)
            unique_files.append(file_path)
    return unique_files


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='bib-check: BibTeX 文件深度检查和自动修复工具',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument('input', nargs='+', help='输入 .bib/.tex 文件或目录路径')
    parser.add_argument('-o', '--output', help='输出文件路径（默认覆盖输入文件）')
    parser.add_argument('-c', '--config', default='config.yaml', help='配置文件路径')
    parser.add_argument('--recursive', action='store_true', help='递归处理目录下的文件')
    parser.add_argument('--glob', dest='glob_pattern', help='指定 glob 模式过滤文件')
    
    # 功能开关
    parser.add_argument('--auto-update', action='store_true',
                       help='启用自动更新 arXiv 条目')
    parser.add_argument('--auto-fix', action='store_true',
                       help='启用自动修复常见字段问题')
    parser.add_argument('--fix-preview', action='store_true',
                       help='仅预览修复，不写回')
    parser.add_argument('--check-links', action='store_true',
                       help='启用链接检查')
    parser.add_argument('--validate', action='store_true',
                       help='启用 BibLaTeX 字段校验')
    parser.add_argument('--all', action='store_true',
                       help='启用所有功能')
    parser.add_argument('--write-bib', action='store_true',
                       help='写回 Bib 文件（默认不写回）')
    
    # 其他选项
    parser.add_argument('--priority', help='数据源优先级，用逗号分隔（如 semantic-scholar,dblp）')
    parser.add_argument('--aux', help='.aux 文件路径（用于过滤引用）')
    parser.add_argument('--html-report', action='store_true',
                       help='生成 HTML 交互报告')
    parser.add_argument('--csv-report', action='store_true',
                       help='生成 CSV 报告')
    parser.add_argument('--latex-report', action='store_true',
                       help='生成 LaTeX 报告')
    parser.add_argument('--pdf-report', action='store_true',
                       help='生成 PDF 报告')
    parser.add_argument('--summary-report', action='store_true',
                       help='生成批量处理汇总报告')
    parser.add_argument('--dry-run', action='store_true', 
                       help='不写回文件，仅生成报告')
    
    args = parser.parse_args()
    
    # 收集输入文件
    input_files = _collect_input_files(args.input, args.recursive, args.glob_pattern)
    if not input_files:
        print(f"{Fore.RED}[错误] 未找到输入文件{Style.RESET_ALL}")
        sys.exit(1)

    # 检查文件存在与格式
    filtered_files = []
    for file_path in input_files:
        if not os.path.exists(file_path):
            print(f"{Fore.RED}[错误] 文件不存在: {file_path}{Style.RESET_ALL}")
            sys.exit(1)
        if not file_path.endswith(('.bib', '.tex')):
            print(f"{Fore.YELLOW}[警告] 跳过不支持的文件: {file_path}{Style.RESET_ALL}")
            continue
        filtered_files.append(file_path)
    if not filtered_files:
        print(f"{Fore.RED}[错误] 没有可处理的 .bib/.tex 文件{Style.RESET_ALL}")
        sys.exit(1)
    
    # 如果使用 --all，启用所有功能
    if args.all:
        args.auto_update = True
        args.check_links = True
        args.validate = True
        args.auto_fix = True
    
    # 检查是否至少启用一个功能
    if args.fix_preview:
        args.auto_fix = True

    if not (args.auto_update or args.check_links or args.validate or args.auto_fix):
        print(f"{Fore.YELLOW}[警告] 未启用任何功能，请使用 --auto-update, --auto-fix, --check-links, --validate 或 --all{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}[提示] 使用 --help 查看帮助信息{Style.RESET_ALL}")
        sys.exit(1)
    
    # 创建 sanitizer 并处理文件
    sanitizer = BibSanitizer(args.config)

    output_dir = None
    if args.output:
        output_path = Path(args.output)
        if output_path.exists() and output_path.is_dir():
            output_dir = output_path
        elif len(filtered_files) > 1:
            output_dir = output_path
            if output_dir.exists() and not output_dir.is_dir():
                print(f"{Fore.RED}[错误] 多文件模式下输出必须为目录: {args.output}{Style.RESET_ALL}")
                sys.exit(1)
            output_dir.mkdir(parents=True, exist_ok=True)

    reports = []
    all_success = True
    for file_path in filtered_files:
        output_file = None
        if args.output:
            if output_dir:
                output_file = str(output_dir / Path(file_path).name)
            else:
                output_file = args.output

        success = sanitizer.process_file(
            file_path,
            output_file,
            auto_update=args.auto_update,
            check_links=args.check_links,
            validate=args.validate,
            dry_run=args.dry_run,
            priority=args.priority,
            write_bib=args.write_bib,
            aux_file=args.aux,
            html_report=args.html_report,
            auto_fix=args.auto_fix,
            fix_preview=args.fix_preview,
            csv_report=args.csv_report,
            latex_report=args.latex_report,
            pdf_report=args.pdf_report
        )
        all_success = all_success and success
        report = sanitizer.report
        stats = {
            'updates': len(report.updates),
            'update_candidates': len(report.update_candidates),
            'update_misses': len(report.update_misses),
            'author_truncations': len(report.author_truncations),
            'fixes': len(report.fixes),
            'dead_links': len(report.dead_links),
            'validation_issues': sum(len(v) for v in report.validation_issues.values()),
            'errors': len(report.errors)
        }
        reports.append({'file': file_path, 'stats': stats})

    if len(filtered_files) > 1 or args.summary_report:
        summary = SummaryReport(reports)
        summary_target_dir = output_dir or Path(filtered_files[0]).parent
        summary_json_suffix = sanitizer.config.get('output', {}).get('summary_suffix', '.summary.json')
        summary_md_suffix = sanitizer.config.get('output', {}).get('summary_md_suffix', '.summary.md')
        summary_json_path = str(summary_target_dir / f"bib-check{summary_json_suffix}")
        summary_md_path = str(summary_target_dir / f"bib-check{summary_md_suffix}")
        summary.write_json(summary_json_path)
        summary.write_markdown(summary_md_path)
        print(f"\n{Fore.GREEN}[汇总] 已写入: {summary_json_path}{Style.RESET_ALL}")
        print(f"{Fore.GREEN}[汇总] 已写入: {summary_md_path}{Style.RESET_ALL}")

    sys.exit(0 if all_success else 1)


if __name__ == '__main__':
    main()
