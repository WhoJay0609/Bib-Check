"""PubMed API 适配器"""

import time
import requests


class PubMedAPI:
    """PubMed API 客户端"""

    def __init__(self, config, cache=None):
        self.config = config.get('sources', {}).get('pubmed', {})
        self.base_url = self.config.get('base_url', 'https://eutils.ncbi.nlm.nih.gov/entrez/eutils')
        self.timeout = self.config.get('timeout', 10)
        self.retry = self.config.get('retry', 3)
        self.rate_limit = self.config.get('rate_limit', 60)
        self.email = self.config.get('email', '')
        self.tool = self.config.get('tool', 'bib-check')
        self.cache = cache
        self.session = requests.Session()
        self._last_request_ts = 0.0

    def search_paper(self, title=None, doi=None, arxiv_id=None, pmid=None):
        if pmid:
            return self._fetch_summary(pmid)
        if title:
            return self._search_by_title(title)
        return None

    def _search_by_title(self, title):
        query = title.strip()
        cache_key = f"pubmed:title:{query.lower()}"
        cached = self._get_cache(cache_key)
        if cached is not None:
            return cached

        params = {
            'db': 'pubmed',
            'term': query,
            'retmax': 1,
            'retmode': 'json',
            'tool': self.tool
        }
        if self.email:
            params['email'] = self.email

        for attempt in range(self.retry):
            try:
                self._rate_limit()
                url = f"{self.base_url}/esearch.fcgi"
                response = self.session.get(url, params=params, timeout=self.timeout)
                if response.status_code == 200:
                    data = response.json()
                    id_list = data.get('esearchresult', {}).get('idlist', [])
                    if not id_list:
                        self._set_cache(cache_key, None)
                        return None
                    result = self._fetch_summary(id_list[0])
                    self._set_cache(cache_key, result)
                    return result
                if response.status_code == 429:
                    time.sleep(2 ** attempt)
                    continue
                return None
            except Exception as e:
                if attempt == self.retry - 1:
                    print(f"PubMed API 错误: {e}")
                    return None
                time.sleep(1)
        return None

    def _fetch_summary(self, pmid):
        pmid = str(pmid).strip()
        cache_key = f"pubmed:pmid:{pmid}"
        cached = self._get_cache(cache_key)
        if cached is not None:
            return cached

        params = {
            'db': 'pubmed',
            'id': pmid,
            'retmode': 'json',
            'tool': self.tool
        }
        if self.email:
            params['email'] = self.email

        for attempt in range(self.retry):
            try:
                self._rate_limit()
                url = f"{self.base_url}/esummary.fcgi"
                response = self.session.get(url, params=params, timeout=self.timeout)
                if response.status_code == 200:
                    data = response.json().get('result', {})
                    item = data.get(pmid, {})
                    result = self._format_item(item, pmid)
                    self._set_cache(cache_key, result)
                    return result
                if response.status_code == 429:
                    time.sleep(2 ** attempt)
                    continue
                return None
            except Exception as e:
                if attempt == self.retry - 1:
                    print(f"PubMed API 错误: {e}")
                    return None
                time.sleep(1)
        return None

    def _format_item(self, item, pmid):
        if not item:
            return None

        title = item.get('title', '')
        authors = [a.get('name', '') for a in item.get('authors', [])]
        pubdate = item.get('pubdate', '')
        year = pubdate[:4] if pubdate else ''
        venue = item.get('fulljournalname') or item.get('source', '')

        doi = ''
        for article_id in item.get('articleids', []):
            if article_id.get('idtype') == 'doi':
                doi = article_id.get('value', '')
                break
        if not doi and item.get('elocationid', '').lower().startswith('doi:'):
            doi = item.get('elocationid', '').split(':', 1)[-1]

        url = f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"

        result = {
            'title': title,
            'authors': [a for a in authors if a],
            'year': year,
            'venue': venue,
            'doi': doi,
            'url': url,
            'pages': '',
            'volume': item.get('volume', ''),
            'number': item.get('issue', ''),
            'publication_type': 'journal',
            'is_published': True,
            'bibtex': ''
        }
        return result

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
