"""Semantic Scholar API 适配器"""

import requests
import time


class SemanticScholarAPI:
    """Semantic Scholar API 客户端"""
    
    def __init__(self, config, cache=None):
        """初始化"""
        self.config = config.get('sources', {}).get('semantic_scholar', {})
        self.base_url = self.config.get('base_url', 'https://api.semanticscholar.org/graph/v1')
        self.timeout = self.config.get('timeout', 10)
        self.retry = self.config.get('retry', 3)
        self.rate_limit = self.config.get('rate_limit', 100)
        self.cache = cache
        self.session = requests.Session()
        self._last_request_ts = 0.0
    
    def search_paper(self, title=None, arxiv_id=None, doi=None):
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

        cache_key = f"semantic:arxiv:{arxiv_id}"
        cached = self._get_cache(cache_key)
        if cached is not None:
            return cached
        
        url = f"{self.base_url}/paper/arXiv:{arxiv_id}"
        params = {
            'fields': (
                'paperId,title,authors,year,venue,publicationVenue,externalIds,publicationTypes,'
                'journal,openAccessPdf,url'
            )
        }
        
        for attempt in range(self.retry):
            try:
                self._rate_limit()
                response = self.session.get(url, params=params, timeout=self.timeout)
                
                if response.status_code == 200:
                    data = response.json()
                    result = self._format_result(data)
                    self._set_cache(cache_key, result)
                    return result
                elif response.status_code == 404:
                    self._set_cache(cache_key, None)
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
        cache_key = f"semantic:title:{title.strip().lower()}"
        cached = self._get_cache(cache_key)
        if cached is not None:
            return cached

        url = f"{self.base_url}/paper/search"
        params = {
            'query': title,
            'limit': 1,
            'fields': (
                'paperId,title,authors,year,venue,publicationVenue,externalIds,publicationTypes,'
                'journal,openAccessPdf,url'
            )
        }
        
        for attempt in range(self.retry):
            try:
                self._rate_limit()
                response = self.session.get(url, params=params, timeout=self.timeout)
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get('data') and len(data['data']) > 0:
                        result = self._format_result(data['data'][0])
                        self._set_cache(cache_key, result)
                        return result
                    self._set_cache(cache_key, None)
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
        publication_venue = data.get('publicationVenue') or {}
        venue = publication_venue.get('name') or data.get('venue', '')
        
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
        journal = data.get('journal') or {}
        open_access_pdf = data.get('openAccessPdf') or {}
        url = open_access_pdf.get('url') or data.get('url', '')

        publication_type = 'conference'
        if 'Journal' in publication_types:
            publication_type = 'journal'
        elif 'Conference' in publication_types:
            publication_type = 'conference'
        elif journal.get('name'):
            publication_type = 'journal'

        paper_id = data.get('paperId', '')
        bibtex = self._fetch_bibtex(paper_id) if paper_id else ''

        ss_url = data.get('url', '')
        if not ss_url and paper_id:
            ss_url = f"https://www.semanticscholar.org/paper/{paper_id}"

        result = {
            'paper_id': paper_id,
            'title': data.get('title', ''),
            'authors': [author.get('name', '') for author in data.get('authors', [])],
            'year': str(data.get('year', '')),
            'venue': venue,
            'doi': external_ids.get('DOI', ''),
            'url': ss_url or url,
            'pages': journal.get('pages', ''),
            'volume': journal.get('volume', ''),
            'number': journal.get('issue', '') or journal.get('number', ''),
            'publication_type': publication_type,
            'is_published': is_published,
            'bibtex': bibtex
        }
        
        return result if is_published else None

    def _fetch_bibtex(self, paper_id):
        """获取 BibTeX"""
        if not paper_id:
            return ''

        url = f"{self.base_url}/paper/{paper_id}"
        params = {'fields': 'citationStyles'}

        for attempt in range(self.retry):
            try:
                self._rate_limit()
                response = self.session.get(url, params=params, timeout=self.timeout)
                if response.status_code == 200:
                    data = response.json()
                    citation_styles = data.get('citationStyles') or {}
                    return citation_styles.get('bibtex', '')
                if response.status_code == 429:
                    time.sleep(2 ** attempt)
                    continue
                return ''
            except Exception as e:
                if attempt == self.retry - 1:
                    print(f"Semantic Scholar BibTeX 获取失败: {e}")
                    return ''
                time.sleep(1)

        return ''

    def _rate_limit(self):
        if not self.rate_limit:
            return
        min_interval = 60.0 / max(self.rate_limit, 1)
        elapsed = time.time() - self._last_request_ts
        if elapsed < min_interval:
            time.sleep(min_interval - elapsed)
        self._last_request_ts = time.time()

    def _get_cache(self, key):
        if not self.cache:
            return None
        return self.cache.get(key)

    def _set_cache(self, key, value):
        if not self.cache:
            return
        self.cache.set(key, value)
