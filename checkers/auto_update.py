"""自动更新 arXiv 条目"""

import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from colorama import Fore, Style
from tqdm import tqdm

from utils.bib_parser import BibParser
from utils.cache import FileCache
from sources.semantic_scholar import SemanticScholarAPI
from sources.dblp import DBLPAPI
from sources.crossref import CrossrefAPI
from sources.arxiv import ArxivAPI
from sources.pubmed import PubMedAPI


class AutoUpdater:
    """自动更新器"""
    
    def __init__(self, config, report):
        """初始化"""
        self.config = config
        self.report = report
        self.priority = config.get('sources', {}).get('priority', [
            'semantic-scholar', 'dblp', 'crossref', 'arxiv', 'pubmed'
        ])
        self.max_workers = config.get('concurrency', {}).get('max_workers', 4)
        self.cache = FileCache(config.get('cache', {}))
        
        # 初始化 API 客户端
        self.apis = {
            'semantic-scholar': SemanticScholarAPI(config, cache=self.cache),
            'dblp': DBLPAPI(config, cache=self.cache),
            'crossref': CrossrefAPI(config, cache=self.cache),
            'arxiv': ArxivAPI(config, cache=self.cache),
            'pubmed': PubMedAPI(config, cache=self.cache)
        }
    
    def update_entries(self, bib_database):
        """更新条目"""
        arxiv_entries = self._find_arxiv_entries(bib_database)
        
        if not arxiv_entries:
            print(f"{Fore.YELLOW}[信息] 没有找到 arXiv-only 条目{Style.RESET_ALL}")
            return bib_database
        
        print(f"{Fore.GREEN}[信息] 找到 {len(arxiv_entries)} 个 arXiv-only 条目{Style.RESET_ALL}")
        
        # 遍历更新
        updated_count = 0
        if self.max_workers and self.max_workers > 1:
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                futures = [executor.submit(self._update_entry, entry) for entry in arxiv_entries]
                for future in tqdm(as_completed(futures), total=len(futures), desc="更新条目", unit="条目"):
                    if future.result():
                        updated_count += 1
        else:
            for entry in tqdm(arxiv_entries, desc="更新条目", unit="条目"):
                if self._update_entry(entry):
                    updated_count += 1
        
        print(f"{Fore.GREEN}[成功] 成功更新 {updated_count} 个条目{Style.RESET_ALL}")
        
        return bib_database
    
    def _find_arxiv_entries(self, bib_database):
        """查找 arXiv-only 条目"""
        arxiv_entries = []
        
        for entry in bib_database.entries:
            # 检查是否是 arXiv only
            if self._is_arxiv_only(entry):
                arxiv_entries.append(entry)
        
        return arxiv_entries
    
    def _is_arxiv_only(self, entry):
        """判断是否是 arXiv-only 条目"""
        # 检查 entry type
        entry_type = entry.get('ENTRYTYPE', '').lower()
        
        # 检查 journal/booktitle
        journal = entry.get('journal', '').lower()
        booktitle = entry.get('booktitle', '').lower()
        venue = entry.get('venue', '').lower()
        
        # 检查 eprint 或 archiveprefix
        eprint = entry.get('eprint', '')
        archiveprefix = entry.get('archiveprefix', '').lower()
        
        # 如果明确标记为 arXiv
        if 'arxiv' in journal or 'arxiv' in booktitle or 'arxiv' in venue:
            return True
        
        if archiveprefix == 'arxiv' and eprint:
            return True
        
        # 检查 note 字段
        note = entry.get('note', '').lower()
        if 'arxiv' in note and not any(x in note for x in ['accepted', 'published', 'appear']):
            return True
        
        return False
    
    def _update_entry(self, entry):
        """更新单个条目"""
        # 提取信息
        title = entry.get('title', '').replace('{', '').replace('}', '')
        arxiv_id = self._extract_arxiv_id(entry)
        doi_hint = entry.get('doi', '')
        
        # 查询所有来源，优先用 DBLP 的 BibTeX
        results = {}
        for source in self.priority:
            api = self.apis.get(source)
            if api:
                result = api.search_paper(title=title, arxiv_id=arxiv_id, doi=doi_hint)
                if result:
                    results[source] = result
        if not doi_hint:
            doi_hint = results.get('semantic-scholar', {}).get('doi', '') or results.get('crossref', {}).get('doi', '')

        # 若 DBLP 未命中，尝试用 DOI 再查一次
        if 'dblp' not in results and doi_hint:
            dblp_api = self.apis.get('dblp')
            if dblp_api:
                dblp_result = dblp_api.search_paper(doi=doi_hint)
                if dblp_result:
                    results['dblp'] = dblp_result
        
        if not results:
            self.report.add_update_miss(
                entry.get('ID', 'unknown'),
                title,
                arxiv_id or ''
            )
            return False

        preferred_result = results.get('dblp') or results.get('semantic-scholar') or next(iter(results.values()))
        if 'dblp' in results and results['dblp'].get('bibtex'):
            preferred_result = results['dblp']

        self.report.add_update_candidate(
            entry.get('ID', 'unknown'),
            preferred_result.get('title', title),
            preferred_result.get('venue', ''),
            preferred_result.get('year', ''),
            preferred_result.get('doi', ''),
            {
                'semantic-scholar': results.get('semantic-scholar', {}).get('url', ''),
                'dblp': results.get('dblp', {}).get('url', '')
            },
            list(results.keys()),
            arxiv_id or ''
        )

        # 若获取到 BibTeX，优先用其完全替换条目（保留原 ID）
        bibtex = preferred_result.get('bibtex', '')
        if bibtex:
            parser = BibParser()
            return self._replace_with_bibtex(entry, parser, bibtex)

        # 记录变更
        changes = {}
        old_type = entry.get('ENTRYTYPE', '')
        
        # 更新字段
        if preferred_result.get('venue'):
            old_venue = entry.get('booktitle', entry.get('journal', ''))
            if preferred_result['publication_type'] == 'conference':
                entry['booktitle'] = preferred_result['venue']
                entry['ENTRYTYPE'] = 'inproceedings'
                if 'journal' in entry:
                    del entry['journal']
            else:
                entry['journal'] = preferred_result['venue']
                entry['ENTRYTYPE'] = 'article'
                if 'booktitle' in entry:
                    del entry['booktitle']
            
            changes['venue'] = (old_venue, preferred_result['venue'])
        
        # 年份/DOI 优先覆盖
        if preferred_result.get('year'):
            old_year = entry.get('year', '')
            if old_year != preferred_result['year']:
                entry['year'] = preferred_result['year']
                changes['year'] = (old_year, preferred_result['year'])
        
        if preferred_result.get('doi'):
            old_doi = entry.get('doi', '')
            if old_doi != preferred_result['doi']:
                entry['doi'] = preferred_result['doi']
                changes['doi'] = (old_doi, preferred_result['doi'])

        # 仅在缺失时补齐更多字段
        self._fill_if_missing(entry, changes, 'title', preferred_result.get('title'))
        self._fill_if_missing(entry, changes, 'author', self._format_authors(preferred_result.get('authors')))
        self._fill_if_missing(entry, changes, 'url', preferred_result.get('url'))
        self._fill_if_missing(entry, changes, 'pages', preferred_result.get('pages'))
        self._fill_if_missing(entry, changes, 'volume', preferred_result.get('volume'))
        self._fill_if_missing(entry, changes, 'number', preferred_result.get('number'))
        
        # 移除 arXiv 相关字段
        for field in ['eprint', 'archiveprefix', 'primaryclass']:
            if field in entry:
                del entry[field]
        
        # 添加到报告
        self.report.add_update(
            entry.get('ID', 'unknown'),
            old_type,
            entry.get('ENTRYTYPE', ''),
            changes
        )
        
        return True

    def _replace_with_bibtex(self, entry, parser, bibtex):
        """使用 API 返回的 BibTeX 完整替换条目内容"""
        parsed_db = parser.parse_string(bibtex)
        if not parsed_db or not parsed_db.entries:
            return False

        new_entry = parsed_db.entries[0]
        old_entry = dict(entry)
        old_type = old_entry.get('ENTRYTYPE', '')

        # 保留原 ID，避免破坏引用
        new_entry['ID'] = old_entry.get('ID', new_entry.get('ID', ''))

        # 原地替换
        entry.clear()
        entry.update(new_entry)

        # 生成变更详情
        changes = self._diff_entries(old_entry, new_entry)
        self.report.add_update(
            entry.get('ID', 'unknown'),
            old_type,
            entry.get('ENTRYTYPE', ''),
            changes
        )
        return True

    def _diff_entries(self, old_entry, new_entry):
        """对比两个条目并生成变更"""
        changes = {}
        fields = set(old_entry.keys()) | set(new_entry.keys())
        for field in fields:
            old_value = old_entry.get(field, '')
            new_value = new_entry.get(field, '')
            if old_value != new_value:
                changes[field] = (str(old_value), str(new_value))
        return changes

    def _fill_if_missing(self, entry, changes, field, value):
        """仅在缺失时补齐字段"""
        if value is None:
            return
        value = str(value).strip()
        if not value:
            return
        old_value = entry.get(field, '')
        if not old_value or str(old_value).strip() == '':
            entry[field] = value
            changes[field] = (old_value, value)

    def _format_authors(self, authors):
        """将作者列表格式化为 BibTeX author 字段"""
        if not authors:
            return ''
        return ' and '.join([a for a in authors if a])
    
    def _extract_arxiv_id(self, entry):
        """提取 arXiv ID"""
        # 从 eprint 字段
        eprint = entry.get('eprint', '')
        if eprint:
            return eprint
        
        # 从 note, journal, booktitle 等字段提取
        for field in ['note', 'journal', 'booktitle', 'url']:
            text = entry.get(field, '')
            match = re.search(r'arXiv[:\s]*(\d+\.\d+)', text, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return None
