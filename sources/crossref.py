"""Crossref API 适配器"""

import time
import requests


class CrossrefAPI:
    """Crossref API 客户端"""

    def __init__(self, config, cache=None):
        self.config = config.get('sources', {}).get('crossref', {})
        self.base_url = self.config.get('base_url', 'https://api.crossref.org')
        self.timeout = self.config.get('timeout', 10)
        self.retry = self.config.get('retry', 3)
        self.rate_limit = self.config.get('rate_limit', 60)
        self.mailto = self.config.get('mailto', '')
        self.cache = cache
        self.session = requests.Session()
        self._last_request_ts = 0.0

    def search_paper(self, title=None, doi=None, arxiv_id=None):
        if doi:
            return self._search_by_doi(doi)
        if title:
            return self._search_by_title(title)
        return None

    def _search_by_doi(self, doi):
        doi = doi.strip().lower()
        cache_key = f"crossref:doi:{doi}"
        cached = self._get_cache(cache_key)
        if cached is not None:
            return cached

        url = f"{self.base_url}/works/{doi}"
        params = self._build_params()

        for attempt in range(self.retry):
            try:
                self._rate_limit()
                response = self.session.get(url, params=params, timeout=self.timeout)
                if response.status_code == 200:
                    data = response.json().get('message', {})
                    result = self._format_item(data)
                    if result:
                        result['bibtex'] = self._fetch_bibtex(doi)
                    self._set_cache(cache_key, result)
                    return result
                if response.status_code == 404:
                    self._set_cache(cache_key, None)
                    return None
                if response.status_code == 429:
                    time.sleep(2 ** attempt)
                    continue
                return None
            except Exception as e:
                if attempt == self.retry - 1:
                    print(f"Crossref API 错误: {e}")
                    return None
                time.sleep(1)
        return None

    def _search_by_title(self, title):
        query = title.strip()
        cache_key = f"crossref:title:{query.lower()}"
        cached = self._get_cache(cache_key)
        if cached is not None:
            return cached

        url = f"{self.base_url}/works"
        params = self._build_params()
        params.update({
            'query.title': query,
            'rows': 1
        })

        for attempt in range(self.retry):
            try:
                self._rate_limit()
                response = self.session.get(url, params=params, timeout=self.timeout)
                if response.status_code == 200:
                    items = response.json().get('message', {}).get('items', [])
                    if not items:
                        self._set_cache(cache_key, None)
                        return None
                    result = self._format_item(items[0])
                    doi = result.get('doi', '') if result else ''
                    if doi:
                        result['bibtex'] = self._fetch_bibtex(doi)
                    self._set_cache(cache_key, result)
                    return result
                if response.status_code == 429:
                    time.sleep(2 ** attempt)
                    continue
                return None
            except Exception as e:
                if attempt == self.retry - 1:
                    print(f"Crossref API 错误: {e}")
                    return None
                time.sleep(1)
        return None

    def _build_params(self):
        params = {}
        if self.mailto:
            params['mailto'] = self.mailto
        return params

    def _format_item(self, item):
        if not item:
            return None

        title_list = item.get('title') or []
        container = item.get('container-title') or []
        authors = item.get('author') or []

        doi = (item.get('DOI') or '').lower()
        venue = container[0] if container else ''
        year = self._extract_year(item)
        url = item.get('URL', '')

        publication_type = 'journal'
        item_type = item.get('type', '')
        if 'proceedings' in item_type:
            publication_type = 'conference'

        result = {
            'title': title_list[0] if title_list else '',
            'authors': [self._format_author(a) for a in authors],
            'year': year,
            'venue': venue,
            'doi': doi,
            'url': url,
            'pages': item.get('page', ''),
            'volume': item.get('volume', ''),
            'number': item.get('issue', ''),
            'publication_type': publication_type,
            'is_published': True,
            'bibtex': ''
        }

        return result

    def _extract_year(self, item):
        for field in ['issued', 'published-print', 'published-online', 'created']:
            date_parts = item.get(field, {}).get('date-parts', [])
            if date_parts and date_parts[0]:
                return str(date_parts[0][0])
        return ''

    def _format_author(self, author):
        family = author.get('family', '')
        given = author.get('given', '')
        if family and given:
            return f"{family}, {given}"
        return family or given or ''

    def _fetch_bibtex(self, doi):
        if not doi:
            return ''
        url = f"{self.base_url}/works/{doi}/transform/application/x-bibtex"
        params = self._build_params()
        for attempt in range(self.retry):
            try:
                self._rate_limit()
                response = self.session.get(url, params=params, timeout=self.timeout)
                if response.status_code == 200:
                    return response.text
                if response.status_code == 429:
                    time.sleep(2 ** attempt)
                    continue
                return ''
            except Exception:
                if attempt == self.retry - 1:
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
