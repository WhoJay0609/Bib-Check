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
from utils.report import Report
from checkers.auto_update import AutoUpdater
from checkers.link_check import LinkChecker

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
                'priority': ['semantic-scholar', 'dblp'],
                'semantic_scholar': {
                    'base_url': 'https://api.semanticscholar.org/graph/v1',
                    'timeout': 10,
                    'retry': 3
                },
                'dblp': {
                    'base_url': 'https://dblp.org/search/publ/api',
                    'timeout': 10,
                    'retry': 3
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
            'output': {
                'backup': True,
                'backup_suffix': '.bak',
                'report_suffix': '.report.json'
            }
        }
    
    def process_file(self, input_file, output_file=None,
                    auto_update=False,
                    check_links=False, dry_run=False, priority=None):
        """处理 BibTeX 文件"""
        
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
        
        # 功能 1: Auto-Update
        if auto_update:
            print(f"\n{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
            print(f"{Fore.CYAN}[功能 1] 自动更新 arXiv 条目{Style.RESET_ALL}")
            print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
            
            updater = AutoUpdater(self.config, self.report)
            bib_database = updater.update_entries(bib_database)
        
        # 功能 2: Dead Link Check
        if check_links:
            print(f"\n{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
            print(f"{Fore.CYAN}[功能 2] 检查链接可用性{Style.RESET_ALL}")
            print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
            
            checker = LinkChecker(self.config, self.report)
            checker.check_entries(bib_database)

        # 作者截断（默认启用）
        print(f"\n{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}[功能 3] 作者截断{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
        authors_changed = self._truncate_authors(bib_database)
        
        # 写回文件
        if not dry_run and (auto_update or authors_changed):
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


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='bib-check: BibTeX 文件深度检查和自动修复工具',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument('input', help='输入 .bib 或 .tex 文件路径')
    parser.add_argument('-o', '--output', help='输出文件路径（默认覆盖输入文件）')
    parser.add_argument('-c', '--config', default='config.yaml', help='配置文件路径')
    
    # 功能开关
    parser.add_argument('--auto-update', action='store_true',
                       help='启用自动更新 arXiv 条目')
    parser.add_argument('--check-links', action='store_true',
                       help='启用链接检查')
    parser.add_argument('--all', action='store_true',
                       help='启用所有功能')
    
    # 其他选项
    parser.add_argument('--priority', help='数据源优先级，用逗号分隔（如 semantic-scholar,dblp）')
    parser.add_argument('--dry-run', action='store_true', 
                       help='不写回文件，仅生成报告')
    
    args = parser.parse_args()
    
    # 检查输入文件
    if not os.path.exists(args.input):
        print(f"{Fore.RED}[错误] 文件不存在: {args.input}{Style.RESET_ALL}")
        sys.exit(1)
    
    # 检查文件格式
    if not args.input.endswith(('.bib', '.tex')):
        print(f"{Fore.RED}[错误] 不支持的文件格式，仅支持 .bib 和 .tex 文件{Style.RESET_ALL}")
        sys.exit(1)
    
    # 如果使用 --all，启用所有功能
    if args.all:
        args.auto_update = True
        args.check_links = True
    
    # 检查是否至少启用一个功能
    if not (args.auto_update or args.check_links):
        print(f"{Fore.YELLOW}[警告] 未启用任何功能，请使用 --auto-update, --check-links 或 --all{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}[提示] 使用 --help 查看帮助信息{Style.RESET_ALL}")
        sys.exit(1)
    
    # 创建 sanitizer 并处理文件
    sanitizer = BibSanitizer(args.config)
    success = sanitizer.process_file(
        args.input,
        args.output,
        auto_update=args.auto_update,
        check_links=args.check_links,
        dry_run=args.dry_run,
        priority=args.priority
    )
    
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
