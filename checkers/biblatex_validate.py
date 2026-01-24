"""BibLaTeX 字段校验器"""

import re
import datetime
from colorama import Fore, Style
from tqdm import tqdm


class BibLaTeXValidator:
    """BibLaTeX 校验器"""
    
    def __init__(self, config, report):
        """初始化"""
        self.config = config
        self.report = report
        self.validation_config = config.get('validation', {})
        
        # 必需字段定义
        self.required_fields = self.validation_config.get('required_fields', self._default_required_fields())
        
        # 字段别名
        self.field_aliases = self.validation_config.get('field_aliases', {
            'school': 'institution',
            'address': 'location'
        })
        
        # 检查规则开关
        self.check_missing_fields = self.validation_config.get('check_missing_fields', True)
        self.check_author_format = self.validation_config.get('check_author_format', True)
        self.check_journal_abbrev = self.validation_config.get('check_journal_abbrev', True)
        self.check_unique_ids = self.validation_config.get('check_unique_ids', True)
        self.check_type_consistency = self.validation_config.get('check_type_consistency', True)
        self.check_doi_format = self.validation_config.get('check_doi_format', True)
        self.check_isbn_issn_format = self.validation_config.get('check_isbn_issn_format', True)
        self.check_year_range = self.validation_config.get('check_year_range', True)
        self.check_pages_format = self.validation_config.get('check_pages_format', True)
        self.check_url_format = self.validation_config.get('check_url_format', True)

        self.year_min = int(self.validation_config.get('year_min', 1900))
        self.year_max = int(self.validation_config.get('year_max', datetime.datetime.now().year + 1))
        self.doi_pattern = re.compile(r'^10\.\d{4,9}/\S+$', re.IGNORECASE)
        self.isbn_pattern = re.compile(r'^(97(8|9))?\d{9}(\d|X)$', re.IGNORECASE)
        self.issn_pattern = re.compile(r'^\d{4}-\d{3}[\dX]$', re.IGNORECASE)
        self.url_pattern = re.compile(r'^https?://', re.IGNORECASE)
        
        # 已见过的 ID 集合
        self.seen_ids = set()
    
    def _default_required_fields(self):
        """默认必需字段定义"""
        return {
            "article": ["author", "title", "journaltitle/journal", "year/date"],
            "book": ["author", "title", "year/date"],
            "mvbook": "book",
            "inbook": ["author", "title", "booktitle", "year/date"],
            "bookinbook": "inbook",
            "suppbook": "inbook",
            "booklet": ["author/editor", "title", "year/date"],
            "collection": ["editor", "title", "year/date"],
            "mvcollection": "collection",
            "incollection": ["author", "title", "booktitle", "year/date"],
            "suppcollection": "incollection",
            "manual": ["author/editor", "title", "year/date"],
            "misc": ["author/editor", "title", "year/date"],
            "online": ["author/editor", "title", "year/date", "url"],
            "patent": ["author", "title", "number", "year/date"],
            "periodical": ["editor", "title", "year/date"],
            "suppperiodical": "article",
            "proceedings": ["title", "year/date"],
            "mvproceedings": "proceedings",
            "inproceedings": ["author", "title", "booktitle", "year/date"],
            "reference": "collection",
            "mvreference": "collection",
            "inreference": "incollection",
            "report": ["author", "title", "type", "institution", "year/date"],
            "thesis": ["author", "title", "type", "institution", "year/date"],
            "unpublished": ["author", "title", "year/date"],
            "mastersthesis": ["author", "title", "institution", "year/date"],
            "techreport": ["author", "title", "institution", "year/date"],
            "conference": "inproceedings",
            "electronic": "online",
            "phdthesis": "mastersthesis",
            "www": "online",
            "school": "mastersthesis",
        }
    
    def validate_entries(self, bib_database, used_ids=None):
        """校验所有条目"""
        print(f"{Fore.GREEN}[信息] 开始 BibLaTeX 字段校验{Style.RESET_ALL}")
        
        entries_to_check = bib_database.entries
        
        # 如果提供了 used_ids，仅检查被引用的条目
        if used_ids:
            entries_to_check = [e for e in bib_database.entries if e.get('ID') in used_ids]
            print(f"{Fore.GREEN}[信息] 仅检查 {len(entries_to_check)} 个被引用的条目{Style.RESET_ALL}")
        else:
            print(f"{Fore.GREEN}[信息] 检查全部 {len(entries_to_check)} 个条目{Style.RESET_ALL}")
        
        # 重置 ID 集合
        self.seen_ids.clear()
        
        # 遍历检查
        for entry in tqdm(entries_to_check, desc="校验条目", unit="条目"):
            self._validate_entry(entry)
        
        # 打印统计
        total_issues = (
            len(self.report.validation_issues.get('missing_fields', [])) +
            len(self.report.validation_issues.get('author_format', [])) +
            len(self.report.validation_issues.get('journal_abbrev', [])) +
            len(self.report.validation_issues.get('duplicate_ids', [])) +
            len(self.report.validation_issues.get('type_issues', []))
        )
        
        if total_issues > 0:
            print(f"{Fore.YELLOW}[警告] 发现 {total_issues} 个校验问题{Style.RESET_ALL}")
        else:
            print(f"{Fore.GREEN}[成功] 所有条目均通过校验{Style.RESET_ALL}")
        
        return bib_database
    
    def _validate_entry(self, entry):
        """校验单个条目"""
        entry_id = entry.get('ID', 'unknown')
        entry_type = entry.get('ENTRYTYPE', '').lower()
        
        # 1. 检查 ID 唯一性
        if self.check_unique_ids:
            if entry_id in self.seen_ids:
                self.report.add_validation_issue(
                    'duplicate_ids',
                    entry_id,
                    f"重复的条目 ID: '{entry_id}'"
                )
            else:
                self.seen_ids.add(entry_id)
        
        # 2. 检查必需字段
        if self.check_missing_fields:
            self._check_required_fields(entry, entry_id, entry_type)
        
        # 3. 检查作者格式
        if self.check_author_format and 'author' in entry:
            self._check_author_format(entry, entry_id)
        
        # 4. 检查期刊缩写
        if self.check_journal_abbrev:
            self._check_journal_abbreviations(entry, entry_id, entry_type)
        
        # 5. 检查类型一致性
        if self.check_type_consistency:
            self._check_type_consistency(entry, entry_id, entry_type)

        # 6. DOI 格式检查
        if self.check_doi_format and 'doi' in entry:
            self._check_doi_format(entry, entry_id)

        # 7. ISBN/ISSN 格式检查
        if self.check_isbn_issn_format:
            self._check_isbn_issn(entry, entry_id)

        # 8. 年份范围检查
        if self.check_year_range:
            self._check_year_range(entry, entry_id)

        # 9. 页码格式检查
        if self.check_pages_format and 'pages' in entry:
            self._check_pages_format(entry, entry_id)

        # 10. URL 格式检查
        if self.check_url_format:
            self._check_url_format(entry, entry_id)
    
    def _check_required_fields(self, entry, entry_id, entry_type):
        """检查必需字段"""
        required = self.required_fields.get(entry_type)
        
        if not required:
            return
        
        # 解析别名引用
        required = self._resolve_field_aliases(required)
        
        if not required:
            return
        
        # 获取条目中的所有字段（考虑别名）
        entry_fields = set(entry.keys())
        for field, alias in self.field_aliases.items():
            if field in entry_fields:
                entry_fields.add(alias)
        
        # 检查每个必需字段
        for required_field in required:
            # 支持 author/editor 语法（任选其一）
            alternatives = required_field.split('/')
            
            # 检查是否至少有一个字段存在
            if set(alternatives).isdisjoint(entry_fields):
                self.report.add_validation_issue(
                    'missing_fields',
                    entry_id,
                    f"缺少必需字段 '{required_field}' (类型: {entry_type})"
                )
    
    def _resolve_field_aliases(self, required):
        """解析字段别名引用"""
        # 如果是字符串，表示引用另一个类型
        while isinstance(required, str):
            required = self.required_fields.get(required)
            if not required:
                return None
        return required
    
    def _check_author_format(self, entry, entry_id):
        """检查作者格式"""
        author_value = entry.get('author', '')
        
        # 检查每个作者的格式
        for author in author_value.split(' and '):
            author = author.strip()
            if not author:
                continue
            
            # 检查逗号分隔的姓名格式
            parts = author.split(',')
            
            if len(parts) == 0:
                self.report.add_validation_issue(
                    'author_format',
                    entry_id,
                    f"作者名称格式错误：缺少组成部分"
                )
            elif len(parts) > 2:
                self.report.add_validation_issue(
                    'author_format',
                    entry_id,
                    f"作者名称 '{author}' 包含过多逗号分隔部分"
                )
            elif len(parts) == 2:
                # 检查姓氏和名字是否为空
                if not parts[0].strip():
                    self.report.add_validation_issue(
                        'author_format',
                        entry_id,
                        f"作者 '{author}' 的姓氏为空"
                    )
                if not parts[1].strip():
                    self.report.add_validation_issue(
                        'author_format',
                        entry_id,
                        f"作者 '{author}' 的名字为空"
                    )
    
    def _check_journal_abbreviations(self, entry, entry_id, entry_type):
        """检查期刊名称缩写"""
        if entry_type != 'article':
            return
        
        for field in ['journal', 'journaltitle']:
            if field in entry:
                value = entry[field]
                # 检查是否包含点号（可能是缩写）
                if '.' in value:
                    self.report.add_validation_issue(
                        'journal_abbrev',
                        entry_id,
                        f"期刊名称 '{value}' 可能使用了缩写"
                    )
    
    def _check_type_consistency(self, entry, entry_id, entry_type):
        """检查类型一致性"""
        # 检查 proceedings 类型但有页码的情况
        if entry_type == 'proceedings' and 'pages' in entry:
            self.report.add_validation_issue(
                'type_issues',
                entry_id,
                f"类型可能错误：'{entry_type}' 有页码，应该使用 'inproceedings'"
            )

    def _check_doi_format(self, entry, entry_id):
        """检查 DOI 格式"""
        doi = entry.get('doi', '').strip()
        if not doi:
            return
        doi = doi.replace('https://doi.org/', '').replace('http://doi.org/', '').replace('doi:', '').strip()
        if not self.doi_pattern.match(doi):
            self.report.add_validation_issue(
                'doi_format',
                entry_id,
                f"DOI 格式可能不正确: '{entry.get('doi', '')}'"
            )

    def _check_isbn_issn(self, entry, entry_id):
        """检查 ISBN/ISSN 格式"""
        isbn = entry.get('isbn', '')
        if isbn:
            normalized = re.sub(r'[\s-]', '', isbn)
            if not self.isbn_pattern.match(normalized):
                self.report.add_validation_issue(
                    'isbn_format',
                    entry_id,
                    f"ISBN 格式可能不正确: '{isbn}'"
                )

        issn = entry.get('issn', '')
        if issn:
            normalized = issn.strip()
            if not self.issn_pattern.match(normalized):
                self.report.add_validation_issue(
                    'issn_format',
                    entry_id,
                    f"ISSN 格式可能不正确: '{issn}'"
                )

    def _check_year_range(self, entry, entry_id):
        """检查年份范围"""
        year_value = entry.get('year', '') or entry.get('date', '')
        if not year_value:
            return
        match = re.search(r'(\d{4})', str(year_value))
        if not match:
            return
        year = int(match.group(1))
        if year < self.year_min or year > self.year_max:
            self.report.add_validation_issue(
                'year_range',
                entry_id,
                f"年份 {year} 超出范围 ({self.year_min}-{self.year_max})"
            )

    def _check_pages_format(self, entry, entry_id):
        """检查页码格式"""
        pages = entry.get('pages', '').strip()
        if not pages:
            return
        if re.search(r'\d-\d', pages) and '--' not in pages:
            self.report.add_validation_issue(
                'pages_format',
                entry_id,
                f"页码格式可能应使用双短横线: '{pages}'"
            )

    def _check_url_format(self, entry, entry_id):
        """检查 URL 格式"""
        for field in ['url', 'pdf']:
            if field not in entry:
                continue
            value = entry.get(field, '')
            if value and not self.url_pattern.match(value):
                self.report.add_validation_issue(
                    'url_format',
                    entry_id,
                    f"URL 格式可能不正确: '{value}'"
                )
