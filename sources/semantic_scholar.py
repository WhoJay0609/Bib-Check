"""Semantic Scholar API 适配器"""

import requests
import time
from urllib.parse import quote


class SemanticScholarAPI:
    """Semantic Scholar API 客户端"""
    
    def __init__(self, config):
        """初始化"""
        self.config = config.get('sources', {}).get('semantic_scholar', {})
        self.base_url = self.config.get('base_url', 'https://api.semanticscholar.org/graph/v1')
        self.timeout = self.config.get('timeout', 10)
        self.retry = self.config.get('retry', 3)
        self.session = requests.Session()
    
    def search_paper(self, title=None, arxiv_id=None):
        """搜索论文"""
        if arxiv_id:
            return self._search_by_arxiv_id(arxiv_id)
        elif title:
            return self._search_by_title(title)
        return None
    
    def _search_by_arxiv_id(self, arxiv_id):
        """通过 arXiv ID 搜索"""
        # 清理 arXiv ID
        arxiv_id = arxiv_id.replace('arXiv:', '').strip()
        
        url = f"{self.base_url}/paper/arXiv:{arxiv_id}"
        params = {
            'fields': 'title,authors,year,venue,publicationVenue,externalIds,publicationTypes'
        }
        
        for attempt in range(self.retry):
            try:
                response = self.session.get(url, params=params, timeout=self.timeout)
                
                if response.status_code == 200:
                    data = response.json()
                    return self._format_result(data)
                elif response.status_code == 404:
                    return None
                elif response.status_code == 429:
                    # 速率限制，等待后重试
                    time.sleep(2 ** attempt)
                    continue
                else:
                    return None
            except Exception as e:
                if attempt == self.retry - 1:
                    print(f"Semantic Scholar API 错误: {e}")
                    return None
                time.sleep(1)
        
        return None
    
    def _search_by_title(self, title):
        """通过标题搜索"""
        url = f"{self.base_url}/paper/search"
        params = {
            'query': title,
            'limit': 1,
            'fields': 'title,authors,year,venue,publicationVenue,externalIds,publicationTypes'
        }
        
        for attempt in range(self.retry):
            try:
                response = self.session.get(url, params=params, timeout=self.timeout)
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get('data') and len(data['data']) > 0:
                        return self._format_result(data['data'][0])
                    return None
                elif response.status_code == 429:
                    time.sleep(2 ** attempt)
                    continue
                else:
                    return None
            except Exception as e:
                if attempt == self.retry - 1:
                    print(f"Semantic Scholar API 错误: {e}")
                    return None
                time.sleep(1)
        
        return None
    
    def _format_result(self, data):
        """格式化结果"""
        if not data:
            return None
        
        # 判断是否有正式出版版本
        publication_types = data.get('publicationTypes', [])
        external_ids = data.get('externalIds', {})
        
        # 如果是会议论文或期刊论文，不是 arXiv only
        is_published = False
        venue = data.get('venue', '')
        
        if publication_types:
            if 'Conference' in publication_types or 'Journal' in publication_types:
                is_published = True
        
        # 检查是否有 DOI（通常意味着正式发表）
        if external_ids.get('DOI'):
            is_published = True
        
        # 如果只有 arXiv ID，说明没有正式出版
        if external_ids.get('ArXiv') and not is_published:
            return None
        
        # 构建返回结果
        result = {
            'title': data.get('title', ''),
            'authors': [author.get('name', '') for author in data.get('authors', [])],
            'year': str(data.get('year', '')),
            'venue': venue,
            'doi': external_ids.get('DOI', ''),
            'publication_type': 'conference' if 'Conference' in publication_types else 'journal',
            'is_published': is_published
        }
        
        return result if is_published else None
