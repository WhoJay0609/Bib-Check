"""自动更新 arXiv 条目"""

import re
from colorama import Fore, Style
from tqdm import tqdm

from sources.semantic_scholar import SemanticScholarAPI
from sources.dblp import DBLPAPI


class AutoUpdater:
    """自动更新器"""
    
    def __init__(self, config, report):
        """初始化"""
        self.config = config
        self.report = report
        self.priority = config.get('sources', {}).get('priority', ['semantic-scholar', 'dblp'])
        
        # 初始化 API 客户端
        self.apis = {
            'semantic-scholar': SemanticScholarAPI(config),
            'dblp': DBLPAPI(config)
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
        
        # 按优先级查询
        result = None
        for source in self.priority:
            api = self.apis.get(source)
            if api:
                result = api.search_paper(title=title, arxiv_id=arxiv_id)
                if result:
                    break
        
        if not result:
            return False
        
        # 记录变更
        changes = {}
        old_type = entry.get('ENTRYTYPE', '')
        
        # 更新字段
        if result['venue']:
            old_venue = entry.get('booktitle', entry.get('journal', ''))
            if result['publication_type'] == 'conference':
                entry['booktitle'] = result['venue']
                entry['ENTRYTYPE'] = 'inproceedings'
                if 'journal' in entry:
                    del entry['journal']
            else:
                entry['journal'] = result['venue']
                entry['ENTRYTYPE'] = 'article'
                if 'booktitle' in entry:
                    del entry['booktitle']
            
            changes['venue'] = (old_venue, result['venue'])
        
        if result['year']:
            old_year = entry.get('year', '')
            entry['year'] = result['year']
            changes['year'] = (old_year, result['year'])
        
        if result['doi']:
            old_doi = entry.get('doi', '')
            entry['doi'] = result['doi']
            changes['doi'] = (old_doi, result['doi'])
        
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
