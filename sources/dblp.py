"""DBLP API 适配器"""

import requests
import time
import xml.etree.ElementTree as ET


class DBLPAPI:
    """DBLP API 客户端"""
    
    def __init__(self, config, cache=None):
        """初始化"""
        self.config = config.get('sources', {}).get('dblp', {})
        self.base_url = self.config.get('base_url', 'https://dblp.org/search/publ/api')
        self.timeout = self.config.get('timeout', 10)
        self.retry = self.config.get('retry', 3)
        self.rate_limit = self.config.get('rate_limit', 60)
        self.cache = cache
        self.session = requests.Session()
        self._last_request_ts = 0.0
    
    def search_paper(self, title=None, arxiv_id=None, doi=None):
        """搜索论文"""
        if doi:
            return self._search(f"doi:{doi}")
        if arxiv_id:
            # DBLP 也索引了 arXiv 论文
            arxiv_id = arxiv_id.replace('arXiv:', '').strip()
            return self._search(f"arxiv:{arxiv_id}")
        elif title:
            return self._search(title)
        return None
    
    def _search(self, query):
        """执行搜索"""
        cache_key = f"dblp:query:{query}"
        cached = self._get_cache(cache_key)
        if cached is not None:
            return cached

        params = {
            'q': query,
            'h': 1,  # 只返回第一个结果
            'format': 'xml'
        }
        
        for attempt in range(self.retry):
            try:
                self._rate_limit()
                response = self.session.get(self.base_url, params=params, timeout=self.timeout)
                
                if response.status_code == 200:
                    result = self._parse_result(response.text)
                    self._set_cache(cache_key, result)
                    return result
                elif response.status_code == 429:
                    time.sleep(2 ** attempt)
                    continue
                else:
                    return None
            except Exception as e:
                if attempt == self.retry - 1:
                    print(f"DBLP API 错误: {e}")
                    return None
                time.sleep(1)
        
        return None
    
    def _parse_result(self, xml_text):
        """解析 XML 结果"""
        try:
            root = ET.fromstring(xml_text)
            
            # 查找第一个 hit
            hit = root.find('.//hit')
            if hit is None:
                return None
            
            info = hit.find('info')
            if info is None:
                return None
            
            # 提取信息
            title = info.find('title')
            authors = info.findall('author')
            year = info.find('year')
            venue = info.find('venue')
            doi = info.find('doi')
            url = info.find('url')
            pages = info.find('pages')
            volume = info.find('volume')
            number = info.find('number')
            pub_type = info.find('type')
            key = info.find('key')
            
            # 判断是否是正式出版（不是 arXiv only）
            venue_text = venue.text if venue is not None else ''
            type_text = pub_type.text if pub_type is not None else ''
            
            # 如果是 arXiv only，不返回
            if 'arxiv' in venue_text.lower() and not doi:
                return None
            
            # 判断出版类型
            is_conference = type_text in ['Conference and Workshop Papers', 'Conference Paper']
            is_journal = type_text in ['Journal Articles', 'Journal Article']
            
            if not (is_conference or is_journal):
                return None
            
            dblp_key = key.text if key is not None else ''
            bibtex = self._fetch_bibtex(dblp_key) if dblp_key else ''

            dblp_url = url.text if url is not None else ''
            if not dblp_url and dblp_key:
                dblp_url = f"https://dblp.org/rec/{dblp_key}"

            result = {
                'title': title.text if title is not None else '',
                'authors': [author.text for author in authors],
                'year': year.text if year is not None else '',
                'venue': venue_text,
                'doi': doi.text if doi is not None else '',
                'url': dblp_url,
                'pages': pages.text if pages is not None else '',
                'volume': volume.text if volume is not None else '',
                'number': number.text if number is not None else '',
                'publication_type': 'conference' if is_conference else 'journal',
                'is_published': True,
                'bibtex': bibtex,
                'dblp_key': dblp_key
            }
            
            return result
        except Exception as e:
            print(f"DBLP XML 解析错误: {e}")
            return None

    def _fetch_bibtex(self, dblp_key):
        """通过 DBLP key 获取 BibTeX"""
        if not dblp_key:
            return ''

        url = f"https://dblp.org/rec/{dblp_key}.bib"
        for attempt in range(self.retry):
            try:
                self._rate_limit()
                response = self.session.get(url, timeout=self.timeout)
                if response.status_code == 200:
                    return response.text
                if response.status_code == 429:
                    time.sleep(2 ** attempt)
                    continue
                return ''
            except Exception as e:
                if attempt == self.retry - 1:
                    print(f"DBLP BibTeX 获取失败: {e}")
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
