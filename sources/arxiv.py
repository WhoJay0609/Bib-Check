"""arXiv API 适配器"""

import time
import requests
import xml.etree.ElementTree as ET


class ArxivAPI:
    """arXiv API 客户端"""

    def __init__(self, config, cache=None):
        self.config = config.get('sources', {}).get('arxiv', {})
        self.base_url = self.config.get('base_url', 'http://export.arxiv.org/api/query')
        self.timeout = self.config.get('timeout', 10)
        self.retry = self.config.get('retry', 3)
        self.rate_limit = self.config.get('rate_limit', 30)
        self.cache = cache
        self.session = requests.Session()
        self._last_request_ts = 0.0

    def search_paper(self, title=None, arxiv_id=None, doi=None):
        if arxiv_id:
            return self._search_by_arxiv_id(arxiv_id)
        if title:
            return self._search_by_title(title)
        return None

    def _search_by_arxiv_id(self, arxiv_id):
        arxiv_id = arxiv_id.replace('arXiv:', '').strip()
        cache_key = f"arxiv:id:{arxiv_id}"
        cached = self._get_cache(cache_key)
        if cached is not None:
            return cached

        params = {
            'id_list': arxiv_id,
            'max_results': 1
        }
        result = self._query(params)
        self._set_cache(cache_key, result)
        return result

    def _search_by_title(self, title):
        query = title.strip().replace('"', '')
        cache_key = f"arxiv:title:{query.lower()}"
        cached = self._get_cache(cache_key)
        if cached is not None:
            return cached

        params = {
            'search_query': f'ti:"{query}"',
            'max_results': 1
        }
        result = self._query(params)
        self._set_cache(cache_key, result)
        return result

    def _query(self, params):
        for attempt in range(self.retry):
            try:
                self._rate_limit()
                response = self.session.get(self.base_url, params=params, timeout=self.timeout)
                if response.status_code == 200:
                    return self._parse_response(response.text)
                if response.status_code == 429:
                    time.sleep(2 ** attempt)
                    continue
                return None
            except Exception as e:
                if attempt == self.retry - 1:
                    print(f"arXiv API 错误: {e}")
                    return None
                time.sleep(1)
        return None

    def _parse_response(self, xml_text):
        try:
            root = ET.fromstring(xml_text)
            ns = {
                'atom': 'http://www.w3.org/2005/Atom',
                'arxiv': 'http://arxiv.org/schemas/atom'
            }
            entry = root.find('atom:entry', ns)
            if entry is None:
                return None

            title = (entry.findtext('atom:title', default='', namespaces=ns) or '').strip().replace('\n', ' ')
            published = entry.findtext('atom:published', default='', namespaces=ns)
            year = published[:4] if published else ''
            url = ''
            for link in entry.findall('atom:link', ns):
                if link.get('rel') == 'alternate':
                    url = link.get('href', '')
                    break

            authors = []
            for author in entry.findall('atom:author', ns):
                name = author.findtext('atom:name', default='', namespaces=ns)
                if name:
                    authors.append(name)

            doi = entry.findtext('arxiv:doi', default='', namespaces=ns)
            journal_ref = entry.findtext('arxiv:journal_ref', default='', namespaces=ns)
            venue = journal_ref or ''

            if not doi and not journal_ref:
                return None

            result = {
                'title': title,
                'authors': authors,
                'year': year,
                'venue': venue,
                'doi': doi,
                'url': url,
                'pages': '',
                'volume': '',
                'number': '',
                'publication_type': 'journal' if journal_ref or doi else 'conference',
                'is_published': True,
                'bibtex': ''
            }
            return result
        except Exception as e:
            print(f"arXiv 解析错误: {e}")
            return None

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
